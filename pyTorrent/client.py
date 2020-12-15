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

class Downloader:
    @classmethod
    def getNewPeerId(self):
        prefix = "-TR3000-"
        peerId = prefix + os.urandom(6).hex()
        return peerId

    def __init__(self, torrentFile):
        self.torrentFile = torrentFile
        self.downloadQueue = self.generateDownloadQueue()
        self.working = set()
        self.available_peer_addresses = self.getAvailablePeers()
        self.connected_peers = set()
        self.peer_id = self.getNewPeerId()

    def downloadComplete(self):
        if(self.downloadQueue.empty() and len(self.working) == 0):
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
                    await peer.sendInterested()
                    self.connected_peers.add(peer)
            except ConnectionRefusedError:
                await peer.close_tcp_connection()
                pass

    async def requestPiece(self, peer, piece_index):
        self.working.add(piece_index)
        for block_index in range(0, self.torrentFile.getNBlocks(piece_index)):
            block_size = self.torrentFile.getBlockSize(piece_index, block_index)
            block_offset= block_index * self.torrentFile.DefaultBlockSize
            request_message = Request(piece_index, block_offset, block_size)
            response = await peer.requestPiece(request_message)
            #give response to some file writer
            print(response.piece_index, response.offset)
        self.working.remove(piece_index)
        self.connected_peers.add(peer)

    async def download(self):
        asyncio.create_task(self.connectToPeers())
        await asyncio.sleep(15)
        while not self.downloadComplete():
            peer = self.connected_peers.pop()
            pieceIndex = self.downloadQueue.get()
            asyncio.create_task(self.requestPiece(peer, pieceIndex))
            await asyncio.sleep(5)

if __name__ == "__main__":
    client = Client()
    asyncio.run(client.download('../resources/fanimatrix.torrent'))
