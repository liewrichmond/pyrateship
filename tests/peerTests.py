import unittest
from pyTorrent.peer import Request
from pyTorrent.torrentFile import TorrentFile

class peerTests(unittest.TestCase):
    def testTest(self):
        self.assertEqual(True, True)

    def testRequestMessage(self):
        torrentFile = TorrentFile('../resources/fanimatrix.torrent')
        piece_index = 0
        block_index = 0
        block_length = torrentFile.getBlockSize(0, 0)
        requestMessage = Request(piece_index, block_index, block_length)
        encoded_message = requestMessage.encode()
        expected_message = b'\x00\x00\x00\x0D\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x00'
        self.assertEqual(encoded_message, expected_message)

    def testRequestMesage2(self):
        torrentFile = TorrentFile('../resources/fanimatrix.torrent')
        piece_index = 0
        block_index = 4
        block_length = torrentFile.getBlockSize(0, 0)
        requestMessage = Request(piece_index, block_index*TorrentFile.DefaultBlockSize, block_length)
        encoded_message = requestMessage.encode()
        expected_message = b'\x00\x00\x00\x0D\x06\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x40\x00'
        self.assertEqual(encoded_message, expected_message)

    def testRequestMesage3(self):
        torrentFile = TorrentFile('../resources/fanimatrix.torrent')
        piece_index = 1
        block_index = 0
        block_length = torrentFile.getBlockSize(0, 0)
        requestMessage = Request(piece_index, block_index*TorrentFile.DefaultBlockSize, block_length)
        encoded_message = requestMessage.encode()
        expected_message = b'\x00\x00\x00\x0D\x06\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x40\x00'
        self.assertEqual(encoded_message, expected_message)
