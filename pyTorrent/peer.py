import asyncio
import socket

class ProtocolError(BaseException):
    pass

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

    async def initiateHandshake(self, info_hash, peer_id):
        if self.writer is None or self.reader is None:
            raise ProtocolError("Can't shake hands before connecting to a peer!")

        handshake = Handshake(info_hash, peer_id)

        await self.sendInitialHandshake(handshake)
        raw_reply = await self.waitForHandshakeReply()

        decoded_reply = handshake.decode(raw_reply)
        if(self.hashesMatch(decoded_reply, info_hash)):
            return decoded_reply

    async def sendInitialHandshake(self, handshake):
        if self.writer is not None:
            self.writer.write(handshake.encode())
            await self.writer.drain()

    async def waitForHandshakeReply(self):
        reply = b''
        tries = 0
        while tries < 10 and len(reply) < Handshake.MESSAGE_LENGTH:
            reply = await self.reader.read(Handshake.MESSAGE_LENGTH)
            tries+=1

        if reply != b'' and reply is not None:
            return reply
        else:
            raise ConnectionRefusedError("Could Not Complete Handshake")

    def hashesMatch(self, decoded_reply, expectedHash):
        try:
            if(decoded_reply['info_hash'] == expectedHash):
                return True
            else:
                return False
        except KeyError:
            raise ValueError("Reply is missing the info_hash key")



class Handshake:
    MESSAGE_LENGTH = 68
    def __init__(self, info_hash, peer_id):
        self.info_hash = info_hash
        self.peer_id = peer_id

    def encode_prefix(self):
        return b'\x13BitTorrent protocol'

    def encode_reserved_bytes(self):
        return b'\x00\x00\x00\x00\x00\x00\x00\x00'

    def encode_peer_id(self):
        return bytes(self.peer_id, 'utf-8')

    def encode(self):
        encoded_message = (
                            self.encode_prefix() +
                            self.encode_reserved_bytes() +
                            self.info_hash +
                            self.encode_peer_id()
                           )
        return encoded_message

    def decode(self, reply):
        if len(reply) < self.MESSAGE_LENGTH:
            raise ValueError("Invalid Reply!")
        else:
            decoded_reply = {}
            decoded_reply['info_hash'] = reply[28:48]
            decoded_reply['peer_id'] = reply[48:]
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
