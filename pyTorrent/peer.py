import asyncio
import socket


class AsyncPeer:
    def __init__(self, address):
        self.ip = address[0]
        self.port = address[1]
        self.reader = None
        self.writer = None

    async def __aenter__(self):
        return self

    async def __aexit__(self,exc_type, exc, tb):
        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()

    async def connect(self):
        fut = asyncio.open_connection(self.ip, self.port)
        try:
            self.reader, self.writer = await asyncio.wait_for(fut, timeout=5)
            print("Connected To Peer!")
        except asyncio.TimeoutError:
            print("Connection Timed Out!")
            raise ConnectionRefusedError("Connection Timed Out")

    async def initHandshake(self, info_hash, peer_id):
        if self.writer is None or self.reader is None:
            raise ConnectionRefusedError("Cannot connect to peer!")

        print("Shaking Hands...")
        message_length = 68

        self.writer.write(self._encodeHandshake(info_hash, peer_id))
        await self.writer.drain()

        handshake_reply = b''
        tries = 0
        while tries < 10 and len(handshake_reply) < message_length:
            handshake_reply = await self.reader.read(message_length)
            tries+=1

        if handshake_reply == b'' or handshake_reply is None:
            print("Handshake Refused!")
            raise ConnectionRefusedError("Could Not Complete Handshake")
        else:
            decoded_reply = self._decodeHandshake(handshake_reply)
            if decoded_reply['info_hash'] != info_hash:
                raise ValueError('Invalid replied info hash!')
            return handshake_reply

    def _encodeHandshake(self, info_hash, peer_id):
        prefix = b'\x13BitTorrent protocol'
        reserved = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        peer_id_bytes = bytes(peer_id, 'utf-8')
        handshake_message = prefix + reserved + info_hash + peer_id_bytes
        return handshake_message

    def _decodeHandshake(self, handshake_reply):
        if len(handshake_reply) < 68:
            raise ValueError("Invalid Reply!")
        else:
            decoded_reply = {}
            decoded_reply['info_hash'] = handshake_reply[28:48]
            decoded_reply['peer_id'] = handshake_reply[48:]
            return decoded_reply



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
        prefix = b'\x13BitTorrent protocol'
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
