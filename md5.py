import hashlib
import sys
from DCCNET_Emu import DCCNET, dccnet_connect

def main():
    ip_port = sys.argv[1].split(':')
    gas = sys.argv[2] + '\n'
    dcc = dccnet_connect(ip_port[0], int(ip_port[1]))
    dcc.enqueue_frame(gas.encode())
    output = bytearray()
    while not dcc.end_received:
        data = dcc.read()
        if not data:
            continue
        output.extend(data)
        while b'\n' in output:
            line, _, output = output.partition(b'\n')
            md5 = hashlib.md5(line).hexdigest() + '\n'
            dcc.enqueue_frame(md5.encode())
    dcc.close()

if __name__ == '__main__':
    main()