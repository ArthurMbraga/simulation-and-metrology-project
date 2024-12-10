import numpy as np

from src.Packet import Packet
from src.sources.Source import Source


class PoissonSource(Source):

    def __init__(self, env, q, ident, transmissionRate):
        super().__init__(env, q, ident, transmissionRate)
        self.packetSizes = [400, 4000, 12000]
        self.packetProbabilities = [0.4, 0.3, 0.3]

        self.avgPacketSize = sum(
            [size * prob for size, prob in zip(self.packetSizes, self.packetProbabilities)])

    def getPacketSize(self):
        # 40% are 400 bytes, 30% are 4000 bytes and 30% are 12000 bytes
        return np.random.choice(self.packetSizes, p=self.packetProbabilities)

    def run(self):
        while True:
            packetSize = self.getPacketSize()

            lam = self.avgPacketSize / self.transmissionRate
            sourceRate = np.random.exponential(lam)

            yield self.env.timeout(sourceRate)

            p = Packet(self.env.now, self.ident, packetSize)

            self.q.reception(p)