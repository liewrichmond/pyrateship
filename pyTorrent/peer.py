import asyncio
import socket


class AsyncPeer:
    def __init__(self, address):
        self.ip = address[0]
        self.port = address[1]
        self.reader = None
        self.writer = None

    async def connect(self):
        fut = asyncio.open_connection(self.ip, self.port)
        try:
            self.reader, self.writer = await asyncio.wait_for(fut, timeout=5)
        except asyncio.TimeoutError:
            print("Connecting....")
            raise ConnectionRefusedError("Connection Timed Out")

    async def initHandshake(self, info_hash, peer_id):
        if self.writer is None:
            raise ConnectionRefusedError("Cannot connect to peer!")

        prefix = b'\x13BitTorrennt protocol'
        reserved = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        info_hash_bytes = info_hash
        peer_id_bytes = bytes(peer_id, 'utf-8')
        handshake_message = prefix + reserved+ info_hash_bytes + peer_id_bytes

        self.writer.write(handshake_message)


# Rewrite using asyncio?
class Peer:
    def __init__(self, address):
        self.address = address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)

    def connect(self):
        try:
            self.sock.connect(self.address)
        except socket.timeout:
            raise ConnectionRefusedError("Timeout")

    def initHandshake(self, info_hash, peer_id):
        prefix = b'\x13BitTorrennt protocol'
        reserved = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        info_hash_bytes = info_hash
        peer_id_bytes = bytes(peer_id, 'utf-8')
        handshake_message = prefix + reserved+ info_hash_bytes + peer_id_bytes

        totalSent = 0
        while totalSent < len(handshake_message):
            sent = self.sock.send(handshake_message[totalSent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            totalSent += totalSent + sent
