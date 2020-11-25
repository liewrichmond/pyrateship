import os
import socket
import asyncio
from torrentFile import TorrentFile
from tracker import Tracker
from peer import Peer, AsyncPeer

class Client:
    def __init__(self):
        self.peer_id = self.getNewPeerId()

    def getNewPeerId(self):
        prefix = "-TR3000-"
        peerId = prefix + os.urandom(6).hex()
        return peerId

    async def download(self, torrentFilePath):
        torrentFile = TorrentFile(torrentFilePath)
        announceUrl = torrentFile.getAnnounceUrl()
        self.peer_id = self.getNewPeerId()

        tracker = Tracker(announceUrl, self.peer_id, 6881)
        res = tracker.getResponse(torrentFile.getInfoHash())

        availablePeers = self.getAvailablePeers(res)
        for peer in availablePeers:
            async with AsyncPeer(peer) as p:
                try:
                    await self.shakeHands(p,torrentFile.getInfoHash(), self.peer_id)
                    print("connected")
                    break
                except ConnectionRefusedError:
                    pass

        return res

    def getAvailablePeers(self, trackerResponse):
        try:
            availablePeers = []
            peers = trackerResponse[b'peers']
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

    async def shakeHands(self, peer, info_hash, peer_id):
        try:
            await peer.connect()
            await peer.initHandshake(info_hash, peer_id)
        except ConnectionRefusedError:
            raise ConnectionRefusedError("Connection Refused")

if __name__ == "__main__":
    client = Client()
    asyncio.run(client.download('../resources/fanimatrix.torrent'))
