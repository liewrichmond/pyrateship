import bencodepy
import os
import requests

class Client:
    def __init__(self):
        self.peer_id = self.getNewPeerId()

    def getNewPeerId(self):
        return os.urandom(20)

    def download(self, torrentFilePath):
        torrentFile = TorrentFile(torrentFilePath)
        announceUrl = torrentFile.getAnnounceUrl()
        self.peer_id = self.getNewPeerId()
        tracker = Tracker(announceUrl, self.peer_id, 6881)
        res = tracker.get(torrentFile.getPiece(0))
        peerIp = self.getPeerIp(res)
        peerPort = self.getPeerPort(res)
        print(peerIp)
        print(peerPort)
        return res

    def getPeerIp(self, trackerResponse):
        ipInBytes = trackerResponse[b'peers'][0:4]
        ip = ''
        for byte in ipInBytes:
            ip += str(byte)
            ip += '.'
        ip = ip[:-1]
        return ip

    def getPeerPort(self, trackerResponse):
        portInBytes = trackerResponse[b'peers'][4:]
        port = (portInBytes[0] << 8 | portInBytes[1])
        return port


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
        res = requests.get(self.announce_url, reqData )
        return bencodepy.decode(res.content)




class TorrentFile:
    def __init__(self, filePath):
        decodedTorrentFile = bencodepy.bread(filePath)

        self.announceURL = decodedTorrentFile[b'announce'].decode()
        self.pieces = decodedTorrentFile[b'info'][b'pieces']
        if(len(self.pieces) % 20) != 0:
            raise ValueError('Pieces not divisible by 20')

    def getAnnounceUrl(self):
        return self.announceURL

    def getPiece(self, pieceIndex):

        startIndex = pieceIndex * 20
        endIndex = startIndex + 20

        return self.pieces[startIndex:endIndex]

    def getNPieces(self):
        return len(self.pieces)

if __name__ == "__main__":
    client = Client()
    res = client.download('./fanimatrix.torrent')
    print(res)
