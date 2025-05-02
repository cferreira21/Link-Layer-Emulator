import struct
import socket
import threading
import queue
import time

SYNC = bytes.fromhex('DCC023C2')
SYNC_PATTERN = SYNC * 2

def compute_checksum(data):
    if len(data) % 2 != 0:
        data += b'\x00'
    total = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1]
        total += word
        total = (total & 0xffff) + (total >> 16)
    return ~total & 0xffff

class DCCNET:
    def __init__(self, sock):
        self.sock = sock
        self.send_lock = threading.Lock()
        self.current_id = 0
        self.expected_receive_id = 0
        self.last_sent_frame = None
        self.last_sent_id = None
        self.retransmit_count = 0
        self.timer = None
        self.ack_received = threading.Event()
        self.receive_buffer = bytearray()
        self.received_data = bytearray()
        self.closed = False
        self.send_queue = queue.Queue()
        self.receiver_thread = threading.Thread(target=self.receive_loop)
        self.receiver_thread.start()
        self.sender_thread = threading.Thread(target=self.send_loop)
        self.sender_thread.start()
        self.last_received_id = None
        self.last_received_checksum = None
        self.expected_id = 0
        self.end_received = False
        self.state_lock = threading.Lock()

    def build_frame(self, data, frame_id, flags):
        sync = SYNC_PATTERN
        header_without_checksum = struct.pack('!HHHB', 0, len(data), frame_id, flags)
        frame_without_checksum = sync + header_without_checksum + data
        checksum = compute_checksum(frame_without_checksum)
        header = struct.pack('!HHHB', checksum, len(data), frame_id, flags)
        return sync + header + data

    def enqueue_frame(self, data, flags=0):
        with self.state_lock:
            self.send_queue.put((data, flags))

    def send_loop(self):
        while not self.closed:
            try:
                data, flags = self.send_queue.get()
                if data is None:
                    break
                with self.state_lock:
                    frame_id = self.current_id
                    frame = self.build_frame(data, frame_id, flags)
                    self.last_sent_frame = frame
                    self.last_sent_id = frame_id
                    self.retransmit_count = 0
                    self.ack_received.clear()
                    self.sock.sendall(frame)
                    self.start_timer()
                    self.ack_received.wait()
            except Exception as e:
                break

    def start_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(1.0, self.retransmit)
        self.timer.start()

    def retransmit(self):
        with self.state_lock:
            if self.retransmit_count >= 16:
                self.send_rst()
                self.close()
                return
            if self.last_sent_frame and not self.ack_received.is_set():
                self.sock.sendall(self.last_sent_frame)
                self.retransmit_count += 1
                self.start_timer()

    def send_ack(self, ack_id):
        ack_frame = self.build_frame(b'', ack_id, 0x80)
        self.sock.sendall(ack_frame)

    def send_rst(self):
        rst_frame = self.build_frame(b'', 0xFFFF, 0x20)
        self.sock.sendall(rst_frame)

    def receive_loop(self):
        while not self.closed:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                self.receive_buffer.extend(data)
                self.process_frames()
            except Exception as e:
                break
        self.close()

    def process_frames(self):
        while True:
            pos = self.receive_buffer.find(SYNC_PATTERN)
            if pos == -1:
                break
            if len(self.receive_buffer) < pos + 15:
                break
            chksum = struct.unpack('!H', self.receive_buffer[pos+8:pos+10])[0]
            length = struct.unpack('!H', self.receive_buffer[pos+10:pos+12])[0]
            if length > 4096:
                del self.receive_buffer[:pos+8]
                continue
            total_length = pos + 15 + length
            if len(self.receive_buffer) < total_length:
                break
            frame_data = self.receive_buffer[pos:total_length]
            temp_frame = frame_data[:8] + b'\x00\x00' + frame_data[10:]
            computed_chksum = compute_checksum(temp_frame)
            if computed_chksum != chksum:
                del self.receive_buffer[:pos+8]
                continue
            frame_id = struct.unpack('!H', frame_data[12:14])[0]
            flags = frame_data[14]
            data = frame_data[15:15+length]
            with self.state_lock:
                if flags & 0x20:
                    self.close()
                    return
                if flags & 0x80:
                    if frame_id == self.last_sent_id:
                        self.ack_received.set()
                        self.current_id ^= 1
                else:
                    end_flag = flags & 0x40
                    if frame_id == self.expected_id:
                        self.received_data.extend(data)
                        self.expected_id ^= 1
                        self.last_received_id = frame_id
                        self.last_received_checksum = computed_chksum
                        self.send_ack(frame_id)
                        if end_flag:
                            self.end_received = True
                    elif frame_id == self.last_received_id and computed_chksum == self.last_received_checksum:
                        self.send_ack(frame_id)
            del self.receive_buffer[:total_length]

    def read(self, size=-1):
        with self.state_lock:
            if size == -1:
                data = bytes(self.received_data)
                self.received_data.clear()
                return data
            else:
                data = self.received_data[:size]
                self.received_data = self.received_data[size:]
                return data

    def close(self):
        with self.state_lock:
            if self.closed:
                return
            self.closed = True
            self.sock.close()
            if self.timer:
                self.timer.cancel()
            self.send_queue.put((None, None))

def dccnet_connect(ip, port):
    sock = socket.create_connection((ip, port))
    return DCCNET(sock)