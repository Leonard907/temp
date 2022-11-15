from argparse import *
from socket import *
import time
from select import select

WAIT = 0
SENT = 1
ACK = 2

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('hostname')
    parser.add_argument('port', type=int)
    parser.add_argument('filename')
    parser.add_argument('retry', type=int)
    parser.add_argument('window', type=int)
    args = parser.parse_args()

    dstAddress = (args.hostname, args.port)
    window_size = args.window
    retry_time = args.retry / 1000
    total_transferred = 0
    retransmit_times = 0
    start_time = time.time()
    total_seq = 0
    packets = []
    running = True

    # Process all msg
    with open(args.filename, "rb") as f:
        while True:
            data = f.read(1024)
            if not data:
                break 
            is_eof = len(data) < 1024
            seq_no_b = total_seq.to_bytes(2, 'big')
            header = bytearray(seq_no_b)
            header.append(is_eof)
            msg = header + data
            packets.append(msg)
            total_seq += 1
            total_transferred += len(data)

    status = {n: WAIT for n in range(total_seq)}

    # all sockets
    send_socket = socket(AF_INET, SOCK_DGRAM)
    send_socket.setblocking(False)
    send_socket.settimeout(retry_time)

    timeout_socks = [retry_time for _ in range(window_size)]
    last_unack = 0

    for i in range(window_size):
        send_socket.sendto(packets[i], dstAddress)
        status[i] = SENT

    while running:
        try:
            sock_start_time = time.time()
            readable, _, _ = select([send_socket], [], [], min(timeout_socks))
            # update ack packets
            for sock in readable:
                data, _ = sock.recvfrom(2)
                ack_no = int.from_bytes(data, 'big')
                status[ack_no] = ACK
            process_pointer = last_unack
            out_of_order = False
            update_sock_timeout = [True for _ in range(window_size)]
            # start from send_base, ack packets in correct order
            while process_pointer < last_unack + window_size:
                # end of file, no timeout
                if process_pointer >= total_seq:
                    update_sock_timeout[process_pointer % window_size] = False
                else:
                    if status[process_pointer] == ACK:
                        # if out of order, don't send next packet
                        if not out_of_order:
                            next_send = last_unack + window_size
                            # check end of file
                            if next_send < total_seq:
                                send_socket.sendto(packets[next_send], dstAddress)
                                status[next_send] = SENT
                            last_unack += 1
                            # terminate if all acked
                            if last_unack == total_seq:
                                running = False
                                break
                        update_sock_timeout[process_pointer % window_size] = False
                    # out of order, buffered
                    elif status[process_pointer] == SENT:
                        out_of_order = True 
                process_pointer += 1
            delay = time.time() - sock_start_time
            # update timeout
            for i in range(window_size):
                if update_sock_timeout[i]:
                    timeout_socks[i] -= delay
                else:
                    timeout_socks[i] = retry_time
        except:
            timeout_value = min(timeout_socks)
            for i in range(last_unack, min(last_unack + window_size, total_seq)):
                if status[i] == SENT:
                    # timeout, retransmit
                    if timeout_socks[i % window_size] <= timeout_value:
                        send_socket.sendto(packets[i], dstAddress)
                        retransmit_times += 1
                        timeout_socks[i % window_size] = retry_time
                    else:
                        timeout_socks[i % window_size] -= timeout_value
                # if ack, no timeout needed
                elif status[i] == ACK:
                    timeout_socks[i % window_size] = retry_time

    print(int(total_transferred / (1000 * (time.time() - start_time))))