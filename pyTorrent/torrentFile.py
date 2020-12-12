import bencodepy
import hashlib

class TorrentFile:
    DefaultBlockSize = pow(2,14)
    def __init__(self, filePath):
        decodedTorrentFile = bencodepy.bread(filePath)
        encodedInfoDict = bencodepy.encode(decodedTorrentFile[b'info'])

        self.info_hash = hashlib.sha1(encodedInfoDict).digest()
        self.announce_url = decodedTorrentFile[b'announce'].decode()
        self.file_length = decodedTorrentFile[b'info'][b'length']
        self.pieces = decodedTorrentFile[b'info'][b'pieces']
        self.piece_length = decodedTorrentFile[b'info'][b'piece length']
        self.nPieces = len(self.pieces)//20

        if(len(self.pieces) % 20) != 0:
            raise ValueError('Pieces not divisible by 20')

    def isFinalPiece(self, piece_index):
        if(piece_index+1 == self.nPieces):
            return True
        else:
            return False

    def isFinalBlock(self, piece_index, block_index):
        if self.isFinalPiece(piece_index) and block_index+1 == self.getNBlocksFinalPiece():
            return True
        else:
            return False

    def getFinalPieceLength(self):
        return ((self.file_length/self.piece_length - self.file_length//self.piece_length) * self.piece_length)

    #create defaultblocksize const macro
    def getNBlocksFinalPiece(self):
        final_piece_length = self.getFinalPieceLength()
        n_blocks = (final_piece_length // pow(2,14)) + 1
        return n_blocks

    def getPieceHash(self, piece_index):
        start_index = piece_index * 20
        end_index = start_index + 20

        return self.pieces[start_index:end_index]

    def getNBlocks(self,piece_index):
        if(self.isFinalPiece(piece_index)):
            return self.getNBlocksFinalPiece()
        else:
            return self.piece_length//pow(2,14)

    def getBlockSize(self, piece_index, block_index):
        if(self.isFinalPiece(piece_index)):
            if self.isFinalBlock(piece_index, block_index):
                final_piece_length = self.getFinalPieceLength()
                n_blocks = self.getNBlocksFinalPiece()
                return ((final_piece_length / pow(2,14) - final_piece_length // pow(2,14)) * pow(2,14))
        else:
            return pow(2,14)
