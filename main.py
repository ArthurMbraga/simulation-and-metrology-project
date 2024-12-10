import argparse

from src.Simulation import Simulation

# Example python3 main.py --burstiness 5 --simulation_time 10000 --periodPrintLR 10 --blockSize 10
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

    parser.add_argument('--barPosition', type=int, required=False,
                        help='Optional bar position for the simulation', default=0)

    args = parser.parse_args()

    Simulation.run_simulation(
        args.burstiness, args.simulation_time, args.periodPrintLR, args.blockSize, args.barPosition)
