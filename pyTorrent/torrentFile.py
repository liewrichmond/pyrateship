import bencodepy
import hashlib

class TorrentFile:
    def __init__(self, filePath):
        decodedTorrentFile = bencodepy.bread(filePath)
        encodedInfoDict = bencodepy.encode(decodedTorrentFile[b'info'])

        self.info_hash = hashlib.sha1(encodedInfoDict)
        self.announce_url = decodedTorrentFile[b'announce'].decode()
        self.pieces = decodedTorrentFile[b'info'][b'pieces']
        self.nPieces = len(self.pieces)//20

        if(len(self.pieces) % 20) != 0:
            raise ValueError('Pieces not divisible by 20')

    def getPiece(self, pieceIndex):

        startIndex = pieceIndex * 20
        endIndex = startIndex + 20

        return self.pieces[startIndex:endIndex]

    def getInfoHash(self):
        return(self.info_hash.digest())
