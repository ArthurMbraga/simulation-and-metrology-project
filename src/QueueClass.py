import queue

import src.Globals as Globals
from src.LimitCounter import LimitCounter


class QueueClass(object):
    def __init__(self, env, serviceRate):
        self.env = env
        self.inService = False
        self.buffer = queue.Queue()
        self.queueSize = 0
        self.queueLength = 0

        self.serviceRate = serviceRate

        self.printQueueCounter = LimitCounter(10000)
        self.debug = False

    def service(self):
        p = self.buffer.get()
        self.inService = True

        service_time = p.pktSize / self.serviceRate
        yield self.env.timeout(service_time)

        response_time = self.env.now - p.t

        Globals.sources[p.ident].responseTimes += response_time
        Globals.sources[p.ident].nbEmissions += 1
        Globals.sources[p.ident].updateMetrics()

        self.queueSize -= p.pktSize
        self.queueLength -= 1

        del p

        if self.queueSize > 0:
            self.env.process(self.service())
        else:
            self.inService = False

    def reception(self, pkt):
        self.queueSize += pkt.pktSize
        self.queueLength += 1

        if self.debug and self.printQueueCounter.incrementAndCheck():
            print(f"Queue size: {self.queueSize} bytes")
            print(f"Queue length: {self.queueLength} packets")

        self.buffer.put(pkt)

        if not self.inService:
            self.env.process(self.service())
