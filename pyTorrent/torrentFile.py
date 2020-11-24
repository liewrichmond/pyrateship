import bencodepy
import hashlib

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
