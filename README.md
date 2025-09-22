# Link-Layer Emulator

This project implements a simple link-layer protocol emulator using Python sockets and threading. It provides reliable data transfer between two endpoints over TCP, simulating features like frame synchronization, checksums, retransmissions, and acknowledgments.

## Files Overview

- `DCCNET_Emu.py`: Core implementation of the DCCNET protocol, including frame construction, sending, receiving, retransmission logic, and connection management.
- `fta.py`: File transfer application using the DCCNET protocol. Supports both server and client modes for sending and receiving files.
- `md5.py`: Application that exchanges data and MD5 hashes over the DCCNET protocol.

---

## DCCNET Protocol (`DCCNET_Emu.py`)

### Key Features

- **Frame Structure**: Each frame includes a synchronization pattern, checksum, length, frame ID, flags, and payload data.
- **Checksum**: Ensures data integrity using a custom checksum algorithm.
- **Reliable Transfer**: Implements retransmission with a timer and acknowledgment mechanism.
- **Threading**: Uses separate threads for sending and receiving frames.
- **Connection Management**: Handles connection closure, reset, and error conditions.

### Main Components

- `DCCNET` class: Manages the protocol state, frame building, sending, receiving, and retransmission.
- `compute_checksum(data)`: Calculates a 16-bit checksum for frame validation.
- `dccnet_connect(ip, port)`: Helper to create a DCCNET connection to a remote host.

---

## File Transfer Application (`fta.py`)

### Usage

- **Server Mode**: Listens for incoming connections, sends file data, and writes received data to an output file.
- **Client Mode**: Connects to a server, sends file data, and writes received data to an output file.

### Command-Line Arguments

- Server: `python fta.py -s <port> <input_file> <output_file>`
- Client: `python fta.py <client> <ip:port> <input_file> <output_file>`

---

## MD5 Exchange Application (`md5.py`)

### Functionality

- Connects to a remote DCCNET server.
- Sends a string (with newline) as a frame.
- Receives data, computes MD5 hashes for each line, and sends the hash back as a frame.

### Command-Line Usage

```sh
python md5.py <ip:port> <string>
```

---

## Protocol Details

- **Synchronization**: Frames start with a fixed sync pattern (`DCC023C2` repeated twice).
- **Header**: Contains checksum, data length, frame ID, and flags.
- **Flags**:
  - `0x80`: ACK frame
  - `0x40`: End of data
  - `0x20`: Reset frame
- **Retransmission**: If ACK is not received within 1 second, the frame is resent (up to 16 times).
- **Thread Safety**: Uses locks to protect shared state.

---

## How to Run

1. Start the server:
   ```sh
   python fta.py -s 9000 input.bin output.bin
   ```
2. Start the client:
   ```sh
   python fta.py client 127.0.0.1:9000 input.bin output.bin
   ```
3. For MD5 exchange:
   ```sh
   python md5.py 127.0.0.1:9000 "your string"
   ```

---

## Requirements

- Python 3.x
- No external dependencies (uses only standard library modules)

---

## Notes

- The protocol is designed for educational purposes and may not handle all edge cases or provide high performance.
- The code uses TCP sockets for transport but implements its own reliability and framing on top.

---

## License

This project is provided as-is for educational use.
