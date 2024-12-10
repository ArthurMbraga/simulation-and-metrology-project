import numpy as np

from Packet import Packet
from sources.Source import Source


class BurstySource(Source):
    def __init__(self, env, q, ident, transmissionRate, packetSize, avgPeriodOn, burstiness):
        super().__init__(env, q, ident, transmissionRate)
        self.packetSize = packetSize

        self.avgPeriodOn = avgPeriodOn
        self.avgPeriodOff = self.avgPeriodOn * (burstiness - 1)

        self.peakRate = burstiness * self.transmissionRate

        self.cycleStart = 0
        self.debug = False

    def run(self):
        periodOn = 0
        periodOff = 0

        while True:
            self.cycleStart = self.env.now
            periodOn = np.random.exponential(self.avgPeriodOn)
            periodOff = np.random.exponential(self.avgPeriodOff)

            self.debug and print(f"periodOn: {periodOn}")
            self.debug and print(f"periodOff: {periodOff}")

            yield self.env.timeout(periodOff)

            lam = self.packetSize / self.peakRate
            self.debug and print(f"lam: {lam}")

            while self.env.now - self.cycleStart - periodOff < periodOn:

                yield self.env.timeout(lam)
                p = Packet(self.env.now, self.ident, self.packetSize)

                self.q.reception(p)
