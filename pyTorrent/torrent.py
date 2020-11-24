import bencodepy
import hashlib
import requests

class Tracker:
    def __init__(self,announce_url, peer_id, port_number):
        self.announce_url = announce_url
        self.peer_id = peer_id
        self.listen_port_number = port_number

    def getResponse(self, info_hash):
        reqData = {
            'info_hash': info_hash,
            'peer_id': self.peer_id,
            'port': self.listen_port_number,
            'uploaded': 0,
            'downloaded':0
        }
        res = requests.get(self.announce_url, reqData)
        #idk why but the debian torrent makes the parser complain :(
        #maybe I can special case it later...? whatevs I'm working with the fanimatrix one for now
        decodedRes = bencodepy.decode(res.content)
        try:
            decodedRes[b'failure reason']
            raise AttributeError("Tracker GET request failed. Response:{}".format(decodedRes))
        except KeyError:
            return decodedRes


class TorrentFile:
    def __init__(self, filePath):
        decodedTorrentFile = bencodepy.bread(filePath)
        encodedInfoDict = bencodepy.encode(decodedTorrentFile[b'info'])

        self.info_hash = hashlib.sha1(encodedInfoDict)
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

    def getInfoHash(self):
        return(self.info_hash.digest())
