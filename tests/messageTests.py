import unittest
from pyTorrent.peer import Message, Have

class MessageTest(unittest.TestCase):
    def testTest(self):
        self.assertEqual(True, True)

    def testHaveMessage(self):
        payload = b'\x00\x00\x00\x00'
        haveMessage = Have(payload)
        self.assertEqual(haveMessage.piece_index, 0)

    def testHaveMessage2(self):
        payload = b'\x00\x00\x00\x80'
        haveMessage = Have(payload)
        self.assertEqual(haveMessage.piece_index, 128)
