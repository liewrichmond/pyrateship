import unittest

from pyTorrent.peer import Peer

class PeerTest(unittest.TestCase):
    def testSetAvailablePieces(self):
        peer = Peer(('192.168.1.1', 80))
        peer.setAvailablePieces(b'\xff')
        expected = [True] * 8
        self.assertEqual(peer.available_pieces, expected)

    def testSetAvailablePieces2(self):
        peer = Peer(('192.168.1.1', 80))
        peer.setAvailablePieces(b'\xaf')
        expected = [True] * 8
        expected[1] = False
        expected[3] = False
        self.assertEqual(peer.available_pieces, expected)

    def testSetAvailablePieces3(self):
        peer = Peer(('192.168.1.1', 80))
        peer.setAvailablePieces(b'\x00')
        expected = [False] * 8
        self.assertEqual(peer.available_pieces, expected)

