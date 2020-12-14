import os
import socket
import asyncio
import queue
from torrentFile import TorrentFile
from tracker import Tracker
from peer import Peer, Request

class Client:
    def __init__(self):
        self.torrentFile = None
        self.queue = None

    async def download(self, torrentFilePath):
        self.torrentFile = TorrentFile(torrentFilePath)
        downloader = Downloader(self.torrentFile)
        await downloader.download()

    async def startRequests(self, connected_peers):
        for peer in connected_peers:
            peer_is_choked = await peer.isChoked()
            if not peer_is_choked:
                piece_index = 0
                if peer.hasPiece(piece_index):
                    await self.requestPiece(piece_index, peer)
                    await peer.getMessage()
                else:
                    pass
            else:
                #If peer is choked, don't bother asking for a piece; just move on
                pass

    async def requestPiece(self, piece_index, peer):
        for block_index in range(0, self.torrentFile.getNBlocks(piece_index)):
            block_size = self.torrentFile.getBlockSize(piece_index, block_index)
            block_offset= block_index * self.torrentFile.DefaultBlockSize
            request = Request(piece_index, block_offset, block_size)
            await self.send_message(peer, request)

    async def send_message(self, peer, request):
        if(peer.is_connected()):
            peer.writer.write(request.encode())
            await peer.writer.drain()
        else:
            raise ValueError("Peer isn't connected")

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

    async def create_torrent_connection(self, peer):
        try:
            await peer.create_tcp_connection()
            await peer.initiateHandshake(self.torrentFile.info_hash, self.peer_id)
            self.checkBitField(await peer.getBitField())
        except ConnectionRefusedError:
            raise ConnectionRefusedError("Connection Refused")

class Downloader:

    @classmethod
    def getNewPeerId(self):
        prefix = "-TR3000-"
        peerId = prefix + os.urandom(6).hex()
        return peerId

    def __init__(self, torrentFile):
        self.torrentFile = torrentFile
        self.downloadQueue = self.generateDownloadQueue()
        self.workingQueue = queue.Queue()
        self.available_peer_addresses = self.getAvailablePeers()
        self.connected_peers = set()
        self.peer_id = self.getNewPeerId()

    def downloadComplete(self):
        if(self.downloadQueue.empty() and self.workingQueue.empty()):
            return True
        else:
            return False

    def generateDownloadQueue(self):
        download_queue = queue.Queue()
        for i in range(0, self.torrentFile.nPieces):
            download_queue.put(i)
        return download_queue

    def getAvailablePeers(self):
        tracker = Tracker(self.torrentFile, self.getNewPeerId())
        return tracker.getAvailablePeers()

    def isValidBitField(self, bit_field):
        if(len(bit_field)*8 == self.torrentFile.nPieces or
           (len(bit_field)*(8)) - 4 == self.torrentFile.nPieces):
            return True
        else:
            return False

    async def connectToPeers(self):
        while len(self.available_peer_addresses) != 0:
            peer_address = self.available_peer_addresses.pop()
            peer = Peer(peer_address)
            try:
                await peer.create_tcp_connection()
                await peer.startHandshake(self.torrentFile.info_hash, self.peer_id)
                if self.isValidBitField(await peer.getBitField()):
                    await peer.expressInterest()
                    self.connected_peers.add(peer)
            except ConnectionRefusedError:
                await peer.close_tcp_connection()
                pass

    async def makeRequest(self, peer, piece_index):
        self.workingQueue.put(pieceIndex)
        for block_index in range(0, self.torrentFile.getNBlocks(piece_index)):
            block_size = self.torrentFile.getBlockSize(piece_index, block_index)
            block_offset= block_index * self.torrentFile.DefaultBlockSize
            request = Request(piece_index, block_offset, block_size)
            await peer.write(request.encode())

    async def download(self):
        asyncio.create_task(self.connectToPeers())
        await asyncio.sleep(15)
        while not self.downloadComplete():
            peer = self.connected_peers.pop()
            pieceIndex = self.downloadQueue.get()
            asyncio.create_task(self.makeRequest(peer, pieceIndex))
            await asyncio.sleep(5)

if __name__ == "__main__":
    client = Client()
    asyncio.run(client.download('../resources/fanimatrix.torrent'))
