import asyncio
import socket
import struct

class ProtocolError(BaseException):
    pass

class Peer:
    def __init__(self, address):
        self.ip = address[0]
        self.port = address[1]
        self.reader = None
        self.writer = None
        self.choking = True
        self.interested = False

    async def __aenter__(self):
        return self

    async def __aexit__(self,exc_type, exc, tb):
        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()

    def is_connected(self):
        if self.writer is None or self.reader is None:
            return False
        else:
            return True

    async def read_from_buffer(self, expected_length):
        if(self.is_connected()):
            reply = b''
            while len(reply) < expected_length:
                readsize = expected_length- len(reply)
                reply += await self.reader.read(readsize)
            return reply

    async def create_tcp_connection(self):
        fut = asyncio.open_connection(self.ip, self.port)
        try:
            self.reader, self.writer = await asyncio.wait_for(fut, timeout=5)
            print("TCP Connected Created... ")
        except asyncio.TimeoutError:
            print("Connection Timed Out!")
            raise ConnectionRefusedError("Connection Timed Out")

    async def close_tcp_connection(self):
        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()

    async def initiateHandshake(self, info_hash, peer_id):
        if(self.is_connected()):
            handshake = Handshake(info_hash, peer_id)

            await self.sendInitialHandshake(handshake)
            raw_reply = await self.waitForHandshakeReply()
            decoded_reply = handshake.decode(raw_reply)

            if(self.hashesMatch(decoded_reply, info_hash)):
                return decoded_reply

    async def getBitField(self):
        if(self.is_connected()):
            message_length= await self.getMessageLength()
            bitField = await self.read_from_buffer(message_length)
            return bitField[1:]
            #await self.expressInterest()

    async def expressInterest(self):
        if(self.is_connected()):
            interested_message = struct.pack(
                '>IB',
                1,
                2
            )
            self.writer.write(interested_message)
            await self.writer.drain()
            self.interested = True

        else:
            raise ProtocolError("nah")

    async def waitForUnchocked(self):
        message = await self.getMessage()

    async def getMessage(self):
        message_length = await self.getMessageLength()
        message = await self.read_from_buffer(message_length)
        return message

    async def getMessageLength(self):
        length_prefix_size = 4
        length_prefix = await self.read_from_buffer(length_prefix_size)
        return int.from_bytes(length_prefix, byteorder='big')

    async def sendInitialHandshake(self, handshake):
        if self.writer is not None:
            self.writer.write(handshake.encode())
            await self.writer.drain()

    async def waitForHandshakeReply(self):
        reply = b''
        tries = 1
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


#class Message:
#    def __init__(self, kind, payload):
#        self.type =




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
