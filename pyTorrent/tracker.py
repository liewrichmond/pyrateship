import bencodepy
import requests

class Tracker:
    DefaultListenPort = 6881
    def __init__(self,torrentFile, peer_id):
        self.announce_url = torrentFile.announce_url
        self.info_hash = torrentFile.info_hash
        self.peer_id = peer_id

    def request(self):
        reqData = {
            'info_hash': self.info_hash,
            'peer_id': self.peer_id,
            'port': self.DefaultListenPort,
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

    def getAvailablePeers(self):
        res = self.request()
        try:
            availablePeers = set()
            peers = res[b'peers']
            for i in range(0,len(peers),6):
                peerIp = self.parsePeerIp(peers[i:i+4])
                peerPort = self.parsePeerPort(peers[i+4:])
                peerEndpoint = (peerIp, peerPort)
                availablePeers.add(peerEndpoint)
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
