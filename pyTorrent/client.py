import os
import socket
import asyncio
from torrentFile import TorrentFile
from tracker import Tracker
from peer import Peer, AsyncPeer

class Client:
    def __init__(self):
        self.peer_id = self.getNewPeerId()
        self.torrentFile = None

    def getNewPeerId(self):
        prefix = "-TR3000-"
        peerId = prefix + os.urandom(6).hex()
        return peerId

    async def download(self, torrentFilePath):
        self.torrentFile = TorrentFile(torrentFilePath)
        announceUrl = self.torrentFile.getAnnounceUrl()

        tracker = Tracker(announceUrl, self.peer_id, 6881)
        availablePeers = self.getAvailablePeers(tracker)

        for peer in availablePeers:
            async with AsyncPeer(peer) as p:
                try:
                    await self.shakeHands(p)
                    break
                except ConnectionRefusedError:
                    pass

        return res

    def getAvailablePeers(self, tracker):
        res = tracker.getResponse(self.torrentFile.getInfoHash())
        try:
            availablePeers = []
            peers = res[b'peers']
            for i in range(0,len(peers),6):
                peerIp = self.parsePeerIp(peers[i:i+4])
                peerPort = self.parsePeerPort(peers[i+4:])
                peerEndpoint = (peerIp, peerPort)
                availablePeers.append(peerEndpoint)
            return availablePeers
        except KeyError:
            raise KeyError('Invalid Tracker Response')

    def parsePeerIp(self, ipInBytes):
        ip = ''
        for byte in ipInBytes:
            ip += str(byte)
            ip += '.'
        ip = ip[:-1]
        return ip

    def parsePeerPort(self, portInBytes):
        port = (portInBytes[0] << 8 | portInBytes[1])
        return port

    async def shakeHands(self, peer):
        try:
            await peer.connect()
            await peer.initHandshake(self.torrentFile.getInfoHash(), self.peer_id)
        except ConnectionRefusedError:
            raise ConnectionRefusedError("Connection Refused")

if __name__ == "__main__":
    client = Client()
    asyncio.run(client.download('../resources/fanimatrix.torrent'))
