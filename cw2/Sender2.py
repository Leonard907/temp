from argparse import *
from code import interact
from pickletools import int4
from socket import *
import sys
import time
from tracemalloc import start

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('hostname')
    parser.add_argument('port', type=int)
    parser.add_argument('filename')
    parser.add_argument('retry', type=int)
    args = parser.parse_args()

    send_socket = socket(AF_INET, SOCK_DGRAM)
    send_socket.settimeout(args.retry / 1000)
    retransmit_time = 0
    total_transferred = 0
    start_time = time.time()
    total_seq = 0
    packets = []

    with open(args.filename, 'rb') as f:
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

    last_unack = 0

    while last_unack < total_seq:
        send_socket.sendto(packets[last_unack], (args.hostname, args.port))
        while True:
            try:
                ack, serverAddress = send_socket.recvfrom(2)
                recv_seq_no = int.from_bytes(ack, 'big')
                # send next if ack, else retransmit
                if recv_seq_no == last_unack:
                    total_transferred += len(packets[last_unack])
                    last_unack += 1
                    break
            except:
                retransmit_time += 1
                send_socket.sendto(packets[last_unack], (args.hostname, args.port))
    print(retransmit_time, int(total_transferred / (1000 * (time.time() - start_time))))