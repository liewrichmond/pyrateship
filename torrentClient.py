import bencodepy

class Client:
    def __init__(self, torrentFile):
        self.torrentFile = torrentFile

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
    print(torrentFile.getPiece(514))
    print(torrentFile.getPiece(515))
