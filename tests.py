import unittest
from torrentClient import TorrentFile

class TestTest(unittest.TestCase):
    def test_True(self):
        self.assertEqual(True, True)

    def test_torrent_file_import(self):
        torrentFile = TorrentFile("./fanimatrix.torrent")

        nPieces = torrentFile.getNPieces()
        prevPiece = torrentFile.getPiece(0)

        for i in range(1,nPieces):
            currPiece = torrentFile.getPiece(i)
            self.assertNotEqual(prevPiece[-1], currPiece[0])
            prevPiece = currPiece

if __name__ == "__main__":
    unittest.main()
