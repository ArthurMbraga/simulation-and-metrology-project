from Packet import Packet
from sources.Source import Source


class ConstantSource(Source):

    def __init__(self, env, q, ident, transmissionRate, packetSize):
        super().__init__(env, q, ident, transmissionRate)
        self.packetSize = packetSize

    def run(self):
        while True:
            lamb = self.packetSize / self.transmissionRate
            yield self.env.timeout(lamb)

            p = Packet(self.env.now, self.ident, self.packetSize)

            self.q.reception(p)
