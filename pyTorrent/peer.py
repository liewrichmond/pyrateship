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
        self.available_pieces = None

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

    def hasPiece(self, piece_index):
        return self.available_pieces[piece_index]

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
            message = await self.getMessage()
            if(type(message) is BitField):
                self.setAvailablePieces(message.bit_field)
                return message.bit_field

    def setAvailablePieces(self, bit_field):
        if(self.available_pieces is None):
            self.available_pieces = [0] * (len(bit_field)*8)
            for i in range(0, len(bit_field)):
                for j in range(0, 8):
                    piece_index = (i*8) + j
                    shift_amnt = 7 - j
                    mask = 1 << shift_amnt
                    bit_field_val = True if bit_field[i] & mask > 0 else False
                    self.available_pieces[piece_index] = bit_field_val

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

    async def isChoked(self):
        if(self.choking):
            message = await self.getMessage()
            if(type(message) == Unchoke):
                self.choking = False
        return self.choking

    async def getMessage(self):
        message_length = await self.getMessageLength()
        raw_bytes = await self.read_from_buffer(message_length)
        return Message.factory(raw_bytes)

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


class Message:
    Choke = 0
    Unchoke = 1
    Interested = 2
    NotInterested = 3
    Have = 4
    BitField = 5
    Request = 6
    Piece = 7
    Cancel = 8

    def __init__(self, payload):
        self.payload = payload

    @classmethod
    def factory(self, raw_bytes):
        if(len(raw_bytes) == 0):
            raise ValueError("Empty message!")
        message_type = raw_bytes[0]
        if(self.hasPayload(message_type)):
            message_payload = raw_bytes[1:]
            if message_type == self.Have:
                return Have(message_payload)
            elif message_type == self.BitField:
                return BitField(message_payload)
            elif message_type == self.Request:
                return Request(message_payload)
            elif message_type == self.Piece:
                return Piece(message_payload)
            elif message_type == self.Cancel:
                return Cancel(message_payload)
            else:
                raise ValueError("Invalid Message Type")
        else:
            if message_type == self.Choke:
                return Choke(None)
            elif message_type == self.Unchoke:
                return Unchoke(None)
            elif message_type == self.Interested:
                return Interested(None)
            elif message_type == self.NotInterested:
                return NotInterested(None)
            else: raise ValueError("Invalid Message Type")

    @classmethod
    def hasPayload(cls, message_type):
        if message_type == 4 or message_type == 5 or message_type == 6 or message_type == 7 or message_type == 8:
            return True
        else:
            return False

class BitField(Message):
    def __init__(self, message_payload):
        self.bit_field = message_payload
    def __str__(self):
        return "BitField"

class Request(Message):
    def __init__(self, piece_index, block_offset, block_length):
        self.piece_index = piece_index
        self.block_offset = block_offset
        self.block_length = block_length

    def encode(self):
        return struct.pack(
            '>IBIII',
            13,
            6,
            self.piece_index,
            self.block_offset,
            self.block_length
        )

class Unchoke(Message):
    def __str__(self):
        return "Unchoke"

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
        #might want to use structs here
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
