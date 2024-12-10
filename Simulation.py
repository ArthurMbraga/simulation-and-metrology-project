import os
import simpy
import pandas as pd
from QueueClass import QueueClass
from sources.ConstantSource import ConstantSource
from sources.PoissonSource import PoissonSource
from sources.BurstySource import BurstySource
import Globals
from tqdm import tqdm
import argparse


class Simulation:
    @staticmethod
    def run_simulation(burstiness, simulation_time, periodPrintLR, blockSize):
        env = simpy.Environment()

        Globals.periodPrintLR = periodPrintLR
        Globals.blockSize = blockSize

        q = QueueClass(env, serviceRate=100 * 10**6)

        # Remove the sources from the dataframes
        Globals.df_responseTimes = pd.DataFrame(
            columns=['sourceId', 'time', 'responseTime'])
        Globals.df_blockRespTimes = pd.DataFrame(
            columns=['sourceId', 'time', 'responseTime', 'epsilon_T'])
        Globals.sources = {}

        df_responseTimes = Globals.df_responseTimes
        df_blockRespTimes = Globals.df_blockRespTimes

        dataSource = PoissonSource(
            env, q, ident=1, transmissionRate=30 * 10**6)
        Globals.sources[dataSource.ident] = dataSource

        voiceSource = ConstantSource(
            env, q, ident=2, transmissionRate=20 * 10**6, packetSize=800)
        Globals.sources[voiceSource.ident] = voiceSource

        videoSource = BurstySource(env, q, ident=3, transmissionRate=30 * 10**6,
                                   packetSize=8000, avgPeriodOn=10**-3, burstiness=burstiness)
        Globals.sources[videoSource.ident] = videoSource

        simulation_progress = tqdm(
            total=simulation_time, desc=f"Simulation Burstiness {burstiness}")
        env.process(Simulation.progress_bar(env, simulation_progress))
        env.run(until=simulation_time)
        simulation_progress.close()

        df_responseTimes['burstiness'] = burstiness
        df_blockRespTimes['burstiness'] = burstiness

        Simulation.save_results(
            df_responseTimes, df_blockRespTimes, burstiness)

    @staticmethod
    def save_results(df_responseTimes, df_blockRespTimes, burstiness):
        os.makedirs('results', exist_ok=True)
        response_times_file = f'results/response_times_burstiness_{burstiness}.csv'
        block_response_times_file = f'results/block_response_times_burstiness_{burstiness}.csv'

        df_responseTimes.to_csv(response_times_file, index=False)
        df_blockRespTimes.to_csv(block_response_times_file, index=False)

    @staticmethod
    def progress_bar(env, progress):
        while True:
            progress.update(1)
            yield env.timeout(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Run simulation with given parameters.')
    parser.add_argument('--burstiness', type=int, required=True,
                        help='Burstiness value for the simulation')
    parser.add_argument('--simulation_time', type=int,
                        required=True, help='Total simulation time')
    parser.add_argument('--periodPrintLR', type=int,
                        required=True, help='Period to print learning rate')
    parser.add_argument('--blockSize', type=int, required=True,
                        help='Block size for the simulation')

    args = parser.parse_args()

    Simulation.run_simulation(
        args.burstiness, args.simulation_time, args.periodPrintLR, args.blockSize)
