# Simulation and Metrology Project

This project simulates a metrology system with various parameters to analyze response times and block averages.

## Requirements

- Python 3.x
- Required Python packages (install using `pip install -r requirements.txt`)

## Usage

Run the simulation with the following command:

```sh
python main.py --burstiness <burstiness_value> --simulation_time <simulation_time> --periodPrintLR <period_print_lr> --blockSize <block_size> [--barPosition <bar_position>]
```

### Parameters

- `--burstiness`: Burstiness value for the simulation (required, float)
- `--simulation_time`: Total simulation time (required, int)
- `--periodPrintLR`: Period to print learning rate (required, int)
- `--blockSize`: Block size for the simulation (required, int)
- `--barPosition`: Optional bar position for the simulation (optional, int, default=0)

### Example

```sh
python main.py --burstiness 5 --simulation_time 10000 --periodPrintLR 10 --blockSize 10
```

## Project Structure

- `src/`: Contains the source code for the simulation.
  - `sources/Source.py`: Defines the `Source` class and its methods for handling emissions and calculating response times.
  - `Simulation.py`: Contains the main simulation logic, including the setup and execution of the simulation environment.
  - `LimitCounter.py`: Implements a counter with a limit to trigger actions after a certain number of increments.
  - `Globals.py`: Defines global variables and dataframes used across the project.
- `main.py`: Entry point for running the simulation, parses command-line arguments and starts the simulation with the specified parameters.
- `DistributedSimulation.py`: Script for running distributed simulations.
- `results/`: Contains the results of the simulations in CSV format.
- `singleSimulation.ipynb`: Jupyter notebook for running a single simulation and analyzing the results.
- `plotResults.ipynb`: Jupyter notebook for plotting the results of the simulations.
