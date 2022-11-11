from argparse import *
from socket import *
from select import select
import time

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('hostname')
    parser.add_argument('port', type=int)
    parser.add_argument('filename')
    parser.add_argument('retry', type=int)
    parser.add_argument('window', type=int)
    args = parser.parse_args()

    retry_time = args.retry / 1000
    dstAddress = (args.hostname, args.port)
    window_size = args.window

    send_socket = socket(AF_INET, SOCK_DGRAM)
    send_socket.setblocking(False)
    send_socket.settimeout(retry_time)
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
            # msg = seq_no_b + is_eof + data
            packets.append(msg)
            total_seq += 1

    seq_ack = 0

    for i in range(window_size):
        if seq_ack + i == total_seq:
            break
        print('start or retransmit', seq_ack + i)
        send_socket.sendto(packets[seq_ack + i], dstAddress)

    while running:
        try:
            readable, _, _ = select([send_socket], [], [], retry_time)
            for sock in readable:
                data, dstAddress = sock.recvfrom(2)
                ack = int.from_bytes(data, 'big')
                if ack == seq_ack:
                    seq_ack += 1
                    # send next packet
                    if seq_ack + window_size <= total_seq:
                        print('normal', ack)
                        sock.sendto(packets[seq_ack + window_size - 1], dstAddress)
                    if seq_ack == total_seq:
                        running = False
                        break
                elif ack > seq_ack:
                    seq_ack += (ack - seq_ack + 1)
                    if seq_ack + window_size <= total_seq:
                        print('receive > send', ack)
                        sock.sendto(packets[seq_ack + window_size - 1], dstAddress)
                else:
                    print('receive < send', ack)
        except:
            print('timeout')
            for i in range(window_size):
                if seq_ack + i == total_seq:
                    break
                send_socket.sendto(packets[seq_ack + i], dstAddress)
