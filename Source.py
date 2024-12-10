import math
import numpy as np
import Settings
from LimitCounter import LimitCounter

class Source(object):

    def __init__(self, env, q, ident, transmissionRate):
        self.env = env
        self.transmissionRate = transmissionRate
        self.q = q  # The queue
        self.ident = ident

        self.nbEmissions = 0
        self.responseTimes = 0
        self.action = env.process(self.run())

        self.respTimeCounter = LimitCounter(Settings.periodPrintLR)
        self.blockCounter = LimitCounter(Settings.blockSize)

    def run(self):
        raise NotImplementedError("Subclasses should implement this!")

    def updateMetrics(self):
        if self.respTimeCounter.incrementAndCheck():
            self.printRespTime()  # called every periodPrintLR
            if self.blockCounter.incrementAndCheck():
                self.printBlockAverage()  # called every periodPrintLR + blockSize

    def printRespTime(self):
        global df_responseTimes

        if self.nbEmissions == 0:
            return

        responseTimes = self.responseTimes / self.nbEmissions
        df_responseTimes.loc[len(df_responseTimes)] = {
            'sourceId': self.ident, 'time': self.env.now, 'responseTime': responseTimes
        }

    def printBlockAverage(self):
        global df_blockRespTimes
        global df_responseTimes

        source_data = df_responseTimes[df_responseTimes['sourceId'] == self.ident]
        last_responseTimes = source_data.tail(Settings.blockSize)
        block_average = last_responseTimes['responseTime'].mean()

        index = len(df_blockRespTimes)
        df_blockRespTimes.loc[index] = {
            'sourceId': self.ident, 'time': self.env.now, 'avgResponseTime': block_average, 'epsilon_T': np.nan
        }

        # Computing the Epsilon
        blocks_data = df_blockRespTimes[df_blockRespTimes['sourceId'] == self.ident]
        num_of_blocks = len(blocks_data)

        if num_of_blocks < 2:
            return

        blocks_responseTime = blocks_data['avgResponseTime']
        sum_of_squares = sum(rt ** 2 for rt in blocks_responseTime)
        square_of_sum = sum(blocks_responseTime) ** 2

        variance = (1 / (num_of_blocks - 1)) * (sum_of_squares - (1 / num_of_blocks) * square_of_sum)
        if variance < 0:
            variance = 0

        blocks_std = math.sqrt(variance)
        epsilon_tao = 4.5 * blocks_std
        epsilon_T = epsilon_tao * math.sqrt(Settings.blockSize / (num_of_blocks * Settings.blockSize))

        # Update Epsilon
        df_blockRespTimes.loc[index, 'epsilon_T'] = epsilon_T