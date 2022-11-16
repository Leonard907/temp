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
        data, clientAddress = receive_socket.recvfrom(1027)
        is_eof = data[2]
        while True:
            seq_no = int.from_bytes(data[:2], 'big')
            content = data[3:]
            if not seq_no == receive_seq_count:
                print('Sequence number cannot match, terminate process')
                sys.exit(0)
            receive_seq_count += 1
            total_received += len(data[3:])
            receive_file.write(content)
            data, clientAddress = receive_socket.recvfrom(1027)
            is_eof = data[2]
            if is_eof:
                sys.exit(0)
