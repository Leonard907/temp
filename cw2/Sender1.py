from argparse import *
from socket import *
import time

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('hostname')
    parser.add_argument('port', type=int)
    parser.add_argument('filename')
    args = parser.parse_args()

    send_socket = socket(AF_INET, SOCK_DGRAM)
    seq_no = 0
    with open(args.filename, "rb") as f:
        file_segment = f.read(1024)
        while True:
            is_eof = not bool(file_segment)
            seq_no_b = seq_no.to_bytes(2, 'big')
            header = bytearray(seq_no_b)
            header.append(is_eof)
            msg = header + file_segment
            send_socket.sendto(msg, (args.hostname, args.port))
            file_segment = f.read(1024)
            seq_no += 1
            time.sleep(0.01)
            if is_eof:
                break
        send_socket.close()