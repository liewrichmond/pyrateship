import os
import socket
import asyncio
import queue
import hashlib
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
        self.fd = os.open(self.torrentFile.file_name,  os.O_RDWR | os.O_CREAT)

    def downloadComplete(self):
        if(self.downloadQueue.empty()):
            return True
        else:
            return False

    def isValidBitField(self, bit_field):
        if(len(bit_field)*8 == self.torrentFile.nPieces or
           (len(bit_field)*(8)) - 4 == self.torrentFile.nPieces):
            return True
        else:
            return False

    def isValidData(self, piece_index, data):
        expected_hash = self.torrentFile.getPieceHash(piece_index)
        data_hash = hashlib.sha1(data).digest()
        if(expected_hash != data_hash):
            return False
        else:
            return True

    async def close(self, peer):
        self.available_peer_addresses.add(peer.getAddress())
        await peer.close_tcp_connection()

    def write(self, piece_index, data):
        pos = piece_index * self.torrentFile.piece_length
        os.lseek(self.fd, pos, os.SEEK_SET)
        os.write(self.fd, data)

    def generateDownloadQueue(self):
        """
        Generates a Queue object that contains the indexes for pieces to be downloaded
        """
        download_queue = queue.Queue()
        for i in range(0, self.torrentFile.nPieces):
            download_queue.put(i)
        return download_queue

    def getAvailablePeers(self):
        tracker = Tracker(self.torrentFile, self.getNewPeerId())
        return tracker.getAvailablePeers()

    async def getPeer(self):
        """
        Helper function to get a peer from the stack. This is done to prevent popping from an empty stack without catching the exception.
        """
        while len(self.connected_peers) <= 0:
            await asyncio.sleep(0.5)
        return self.connected_peers.pop()

    async def connectToPeers(self):
        """
        Mutates connected_peers directly.
        Creating a Peer Connection consists of a TCP connection, a handshake, and a Bitfield.
        This functions also sends and interested message to get the peer ready to receive messages.
        """
        while len(self.available_peer_addresses) != 0:
            peer_address = self.available_peer_addresses.pop()
            peer = Peer(peer_address)
            try:
                await peer.create_tcp_connection()
                await peer.startHandshake(self.torrentFile.info_hash, self.peer_id)
                if self.isValidBitField(await peer.getBitField()):
                    await peer.sendInterested()
                    self.connected_peers.add(peer)
            except ConnectionError:
                await self.close(peer)
                pass

    async def requestPiece(self, peer, piece_index):
        """
        Requests a Piece from a given peer.
        """
        self.working.add(piece_index)
        block_data = b''
        for block_index in range(0, self.torrentFile.getNBlocks(piece_index)):
            try:
                await asyncio.wait_for(peer.unchoke(), timeout=5)
                block_size = self.torrentFile.getBlockSize(piece_index, block_index)
                block_offset= block_index * self.torrentFile.DefaultBlockSize
                request_message = Request(piece_index, block_offset, block_size)
                response = await peer.requestPiece(request_message)
                block_data += response.data
            except (asyncio.TimeoutError, ConnectionError):
                await self.close(peer)
                self.downloadQueue.put(piece_index)
                print("Dropped peer")
                return
        if(self.isValidData(piece_index, block_data)):
            print(piece_index, "done")
            self.working.remove(piece_index)
            self.connected_peers.add(peer)
            self.write(piece_index, block_data)
        #give response to some file writer after checking hash
        else:
            print("Incorrect Data!")

    async def download(self):
        asyncio.create_task(self.connectToPeers())
        await asyncio.sleep(15)
        while not self.downloadComplete():
            peer = await self.getPeer()
            pieceIndex = self.downloadQueue.get(timeout = 5)
            if(peer.hasPiece(pieceIndex)):
                task = asyncio.create_task(self.requestPiece(peer, pieceIndex))
            else:
                self.connected_peers.add(peer)

if __name__ == "__main__":
    client = Client()
    asyncio.run(client.download('../resources/big-buck-bunny.torrent'))
