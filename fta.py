import sys
import socket
from DCCNET_Emu import DCCNET, dccnet_connect

def server_mode(port, input_file, output_file):
    with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', port))
        sock.listen(1)
        conn, _ = sock.accept()
        dcc = DCCNET(conn)
        data = f_in.read()
        dcc.enqueue_frame(data, flags=0x40)
        while not dcc.end_received:
            received = dcc.read()
            f_out.write(received)
        dcc.close()

def client_mode(ip_port, input_file, output_file):
    with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
        dcc = dccnet_connect(ip_port[0], int(ip_port[1]))
        data = f_in.read()
        dcc.enqueue_frame(data, flags=0x40)
        while not dcc.end_received:
            received = dcc.read()
            f_out.write(received)
        dcc.close()

def main():
    if sys.argv[1] == '-s':
        server_mode(int(sys.argv[2]), sys.argv[3], sys.argv[4])
    else:
        ip_port = sys.argv[2].split(':')
        client_mode(ip_port, sys.argv[3], sys.argv[4])

if __name__ == '__main__':
    main()