import bencodepy
import os
import requests
import socket
import hashlib

class Client:
    def __init__(self):
        self.peer_id = self.getNewPeerId()

    def getNewPeerId(self):
        prefix = "-TR3000-"
        peerId = prefix + os.urandom(6).hex()
        return peerId

    def download(self, torrentFilePath):
        torrentFile = TorrentFile(torrentFilePath)
        announceUrl = torrentFile.getAnnounceUrl()
        self.peer_id = self.getNewPeerId()

        tracker = Tracker(announceUrl, self.peer_id, 6881)
        res = tracker.getResponse(torrentFile.getInfoHash())

        availablePeers = self.getAvailablePeers(res)
        for peer in availablePeers:
            try:
                connectedPeer =  self.connect(peer)
                print("connected")
                break
            except ConnectionRefusedError:
                pass

        connectedPeer.initHandshake(torrentFile.getInfoHash(), self.peer_id)

        return res

    def getAvailablePeers(self, trackerResponse):
        try:
            availablePeers = []
            peers = trackerResponse[b'peers']
            for i in range(0,len(peers),6):
                peerIp = self.parsePeerIp(peers[i:i+4])
                peerPort = self.parsePeerPort(peers[i+4:])
                peerEndpoint = (peerIp, peerPort)
                availablePeers.append(peerEndpoint)
            return availablePeers
        except KeyError:
            raise KeyError('Invalid Tracker Response')

    def parsePeerIp(self, ipInBytes):
        ip = ''
        for byte in ipInBytes:
            ip += str(byte)
            ip += '.'
        ip = ip[:-1]
        return ip

    def parsePeerPort(self, portInBytes):
        port = (portInBytes[0] << 8 | portInBytes[1])
        return port

    def connect(self, address):
        try:
            p = Peer(address)
            p.connect()
            return p
        except ConnectionRefusedError:
            raise ConnectionRefusedError("Connection Refused")

class Peer:
    def __init__(self, address):
        self.address = address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)

    def connect(self):
        try:
            self.sock.connect(self.address)
        except socket.timeout:
            raise ConnectionRefusedError("Timeout")

    def initHandshake(self, info_hash, peer_id):
        prefix = b'\x13BitTorrennt protocol'
        reserved = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        info_hash_bytes = info_hash
        peer_id_bytes = bytes(peer_id, 'utf-8')
        handshake_message = prefix + reserved+ info_hash_bytes + peer_id_bytes

        totalSent = 0
        while totalSent < len(handshake_message):
            sent = self.sock.send(handshake_message[totalSent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            totalSent += totalSent + sent

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

if __name__ == "__main__":
    client = Client()
    res = client.download('./fanimatrix.torrent')
