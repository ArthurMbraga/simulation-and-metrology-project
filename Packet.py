class Packet(object):
    def __init__(self, t, ident, pktSize):
        self.t = t
        self.ident = ident
        self.pktSize = pktSize
