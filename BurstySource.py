import numpy as np

from Packet import Packet
from Source import Source


class BurstySource(Source):
    def __init__(self, env, q, ident, transmissionRate, packetSize, avgPeriodOn, peakRate):
        super().__init__(env, q, ident, transmissionRate)
        self.packetSize = packetSize
        self.avgPeriodOn = avgPeriodOn

        lamb = self.packetSize / self.transmissionRate
        print(f"avgPeriodOn: {avgPeriodOn}")
        self.avgPeriodOff = ((peakRate * avgPeriodOn) / lamb) - avgPeriodOn

        print(f"avgPeriodOff: {self.avgPeriodOff}")
        print(
            f"peakRate * avgPeriodOn / transmissionRate: {peakRate * avgPeriodOn / transmissionRate}")
        self.peakRate = peakRate
        self.cycleStart = 0

    def run(self):
        periodOn = 0
        periodOff = 0

        while True:
            now = self.env.now
            if self.cycleStart + periodOn + periodOff <= now:
                self.cycleStart = now
                periodOn = np.random.exponential(1/self.avgPeriodOn)
                periodOff = np.random.exponential(1/self.avgPeriodOff)
            elif self.cycleStart + periodOn <= now:
                # During On periods traffic is emitted at a constant peakRate
                lam = 1/self.peakRate
                yield self.env.timeout(lam)
                p = Packet(self.env.now, self.ident, self.packetSize)

                self.q.reception(p)
                self.updateMetrics()
