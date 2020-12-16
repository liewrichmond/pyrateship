import unittest
import os
from pyTorrent.tracker import Tracker
from pyTorrent.torrentFile import TorrentFile

class TrackerTest(unittest.TestCase):
    def test_test(self):
        self.assertEqual(True, True)

    def testTracker(self):
        torrentFile = TorrentFile('../resources/fanimatrix.torrent')
        prefix = "-TR3000-"
        peerId = prefix + os.urandom(6).hex()
        tracker = Tracker(torrentFile, peerId)
        available_peer_addresses = tracker.getAvailablePeers()
        self.assertNotEqual(len(available_peer_addresses), 0)
