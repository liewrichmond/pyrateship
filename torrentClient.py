import bencodepy
import os
import requests

class Client:
    def __init__(self, torrentFile):
        self.torrentFile = torrentFile
        self.peer_id = self.getNewPeerId()

    def getNewPeerId(self):
        return os.urandom(20)

    def startDownload(self):
        self.peer_id = self.getNewPeerId()
        announceUrl = self.torrentFile.getAnnounceUrl()
        tracker = Tracker(announceUrl, self.peer_id, 6881)
        res = tracker.get(self.torrentFile.getPiece(0))
        return res.text

class Tracker:
    def __init__(self,announce_url, peer_id, port_number):
        self.announce_url = announce_url
        self.peer_id = peer_id
        self.listen_port_number = port_number

    def get(self, info_hash):
        reqData = {
            'info_hash': info_hash,
            'peer_id': self.peer_id,
            'port': self.listen_port_number,
            'uploaded': 0,
            'downloaded':0
        }
        res = requests.get(self.announce_url, reqData)
        return res


class TorrentFile:
    def __init__(self, filePath):
        decodedTorrentFile = bencodepy.bread(filePath)

        if(len(decodedTorrentFile[b'info'][b'pieces'])%20)!=0:
            raise ValueError('Pieces not divisible by 20')

        self.announceURL = decodedTorrentFile[b'announce'].decode()
        self.pieces = decodedTorrentFile[b'info'][b'pieces']

    def getAnnounceUrl(self):
        return self.announceURL

    def getPiece(self, pieceIndex):

        startIndex = pieceIndex * 20
        endIndex = startIndex + 20

        return self.pieces[startIndex:endIndex]

    def getNPieces(self):
        return len(self.pieces)

if __name__ == "__main__":
    torrentFile = TorrentFile('./fanimatrix.torrent')
    client = Client(torrentFile)
    res = client.startDownload()
    print(res)
