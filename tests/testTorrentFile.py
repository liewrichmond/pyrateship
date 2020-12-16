import unittest
from pyTorrent.torrentFile import TorrentFile

class TorrentFileTest(unittest.TestCase):
    def testDecodeTorrentFile(self):
        torrentFile = TorrentFile('../resources/fanimatrix.torrent')
        self.assertEqual(torrentFile.piece_length, 262144)

    def testIsLastPiece(self):
        torrentFile = TorrentFile('../resources/fanimatrix.torrent')
        self.assertEqual(torrentFile.isFinalPiece(515), True)
        self.assertEqual(torrentFile.getFinalPieceLength(), 42414)
        self.assertEqual(torrentFile.getNBlocksFinalPiece(), 3)
        self.assertEqual(torrentFile.getNBlocks(50), 16)
        self.assertEqual(torrentFile.getNBlocks(515), 3)
        self.assertEqual(torrentFile.getBlockSize(50, 10), pow(2,14))
        self.assertEqual(torrentFile.getBlockSize(515, 2), 9646)
        self.assertEqual(torrentFile.getPieceHash(0), True)

