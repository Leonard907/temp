from argparse import *
from socket import *
from select import select
import time

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('hostname')
    parser.add_argument('port', type=int)
    parser.add_argument('filename')
    parser.add_argument('retry', type=float)
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
            packets.append(msg)
            total_seq += 1
            total_transferred += len(data)

    seq_ack = 0

    for i in range(window_size):
        if seq_ack + i == total_seq:
            break
        send_socket.sendto(packets[seq_ack + i], dstAddress)

    while running:
        readable, writable, exceptional = select([send_socket], [], [], retry_time)
        # timeout
        if not (readable or writable or exceptional):
            for i in range(window_size):
                if seq_ack + i == total_seq:
                    break
                send_socket.sendto(packets[seq_ack + i], dstAddress)
            continue
        for sock in readable:
            data, dstAddress = sock.recvfrom(2)
            ack = int.from_bytes(data, 'big')
            if ack == seq_ack:
                if seq_ack + window_size < total_seq:
                    sock.sendto(packets[seq_ack + window_size], dstAddress)
                seq_ack += 1
                # send next packet
            elif ack > seq_ack:
                # send packet of window
                if seq_ack + window_size < total_seq:
                    sock.sendto(packets[seq_ack + window_size], dstAddress)
                seq_ack += (ack - seq_ack + 1)
            if seq_ack == total_seq:
                running = False
                break
    print(int(total_transferred / (1024 * (time.time() - start_time))))