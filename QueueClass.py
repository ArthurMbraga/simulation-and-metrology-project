import queue


class QueueClass(object):
    def __init__(self, env, serviceRate):
        self.env = env
        self.inService = False
        self.buffer = queue.Queue()
        self.queueLength = 0
        self.serviceRate = serviceRate

    def service(self):
        global sources

        p = self.buffer.get()
        self.inService = True

        service_time = p.pktSize / self.serviceRate
        yield self.env.timeout(service_time)

        response_time = self.env.now - p.t

        sources[p.ident].responseTimes += response_time
        sources[p.ident].nbEmissions += 1

        self.queueLength -= p.pktSize
        del p

        if self.queueLength > 0:
            self.env.process(self.service())
        else:
            self.inService = False

    def reception(self, pkt):
        self.queueLength += pkt.pktSize
        self.buffer.put(pkt)

        if not self.inService:
            self.env.process(self.service())
