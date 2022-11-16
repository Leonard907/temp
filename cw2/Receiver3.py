from argparse import *
from socket import *
import sys

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('port', type=int)
    parser.add_argument('filename')
    args = parser.parse_args()
    
    receive_socket = socket(AF_INET, SOCK_DGRAM)
    receive_socket.bind(('', args.port))
    receive_seq_count = 0
    total_received = 0
    with open(args.filename, 'wb') as receive_file:
        while True:
            data, clientAddress = receive_socket.recvfrom(1027)
            is_eof = data[2]
            seq_no = int.from_bytes(data[:2], 'big')
            content = data[3:]
            if seq_no == receive_seq_count:
                ack_packet = receive_seq_count.to_bytes(2, 'big')
                receive_socket.sendto(ack_packet, clientAddress)
                receive_seq_count += 1
                total_received += len(data[3:])
                receive_file.write(content)
                if is_eof:
                    for i in range(50):
                        receive_socket.sendto(ack_packet, clientAddress)
                    sys.exit(0)
            else:
                ack_packet = (receive_seq_count - 1).to_bytes(2, 'big')
                if receive_seq_count > 0:
                    receive_socket.sendto(ack_packet, clientAddress)
