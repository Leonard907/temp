from argparse import *
from socket import *
import sys

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('port', type=int)
    parser.add_argument('filename')
    parser.add_argument('window', type=int)
    args = parser.parse_args()
    
    window_size = args.window
    receive_socket = socket(AF_INET, SOCK_DGRAM)
    receive_socket.bind(('', args.port))
    receive_seq_count = 0
    total_received = 0
    buffer = [False for _ in range(window_size)]
    eof_seq_no = -1
    running = True

    with open(args.filename, 'wb') as receive_file:
        while True:
            data, clientAddress = receive_socket.recvfrom(1027)
            is_eof = data[2]
            seq_no = int.from_bytes(data[:2], 'big')
            content = data[3:]
            ack_packet = seq_no.to_bytes(2, 'big')
            if seq_no < receive_seq_count:
                pass 
            else:
                buffer[seq_no - receive_seq_count] = (seq_no, content)
                if seq_no == receive_seq_count:
                    while buffer[0] != False:
                        content_seq_no, content = buffer.pop(0)
                        receive_file.write(content)
                        buffer.append(False)
                        receive_seq_count += 1

            if is_eof:
                eof_seq_no = seq_no

            receive_socket.sendto(ack_packet, clientAddress)
            if eof_seq_no != -1 and receive_seq_count >= eof_seq_no:
                # send more to avoid loss
                for i in range(100):
                    receive_socket.sendto(ack_packet, clientAddress)
                with open('log', 'w') as logf:
                    logf.write(str(seq_no))
                break