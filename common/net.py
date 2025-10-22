import struct, json, socket

def send_json(sock: socket.socket, obj: dict):
    data = json.dumps(obj).encode("utf-8")
    header = struct.pack(">I", len(data))  # 4 bytes big-endian
    sock.sendall(header + data)

def recv_json(sock: socket.socket):
    # Read 4-byte length
    header = _recvall(sock, 4)
    if not header:
        return None
    (length,) = struct.unpack(">I", header)
    body = _recvall(sock, length)
    if body is None:
        return None
    return json.loads(body.decode("utf-8"))

def _recvall(sock: socket.socket, n: int) -> bytes | None:
    data = bytearray()
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data.extend(chunk)
    return bytes(data)
