import os
import socket
import asyncio
from torrentFile import TorrentFile
from tracker import Tracker
from peer import Peer

class Client:
    def __init__(self):
        self.peer_id = self.getNewPeerId()
        self.torrentFile = None
        self.queue = None

    def getNewPeerId(self):
        prefix = "-TR3000-"
        peerId = prefix + os.urandom(6).hex()
        return peerId

    async def download(self, torrentFilePath):
        self.torrentFile = TorrentFile(torrentFilePath)
        self.generateDownloadQueue()
        available_peers = self.getAvailablePeers(Tracker(self.torrentFile.announce_url, self.peer_id, 6881))
        connected_peers = await self.connectToPeers(available_peers)
        await self.expressInterest(connected_peers)

    def generateDownloadQueue(self):
        self.queue = [False] * self.torrentFile.nPieces

    def startRequests(self, connected_peers):
        for peer in connected_peers:
            if peer.isChoked():
                #If peer is choked, don't bother asking for a piece; just move on
                pass


    async def connectToPeers(self, availablePeers):
        if len(availablePeers) > 0:
            connectedPeers = []
            for p in availablePeers:
                peer = Peer(p)
                try:
                    await self.create_torrent_connection(peer)
                    connectedPeers.append(peer)
                    if(len(connectedPeers) == 4) :
                        break
                except ConnectionRefusedError:
                    print("closing connection...")
                    await peer.close_tcp_connection()
                    pass
            return connectedPeers

    async def expressInterest(self, connectedPeers):
        for peer in connectedPeers:
            await peer.expressInterest()

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

    def checkBitField(self, bit_field):
        if(len(bit_field)*8 == self.torrentFile.nPieces or
           (len(bit_field)*(8)) - 4 == self.torrentFile.nPieces):
            pass
        else:
            raise ConnectionRefusedError("Invalid BitField Length")

    async def create_torrent_connection(self, peer):
        try:
            await peer.create_tcp_connection()
            await peer.initiateHandshake(self.torrentFile.getInfoHash(), self.peer_id)
            self.checkBitField(await peer.getBitField())
        except ConnectionRefusedError:
            raise ConnectionRefusedError("Connection Refused")

if __name__ == "__main__":
    client = Client()
    asyncio.run(client.download('../resources/fanimatrix.torrent'))
