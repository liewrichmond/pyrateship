import bencodepy
import os
import requests
import socket
import hashlib
import asyncio
from torrent import TorrentFile, Tracker

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


# Rewrite using asyncio?
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


if __name__ == "__main__":
    client = Client()
    res = client.download('../resources/fanimatrix.torrent')
