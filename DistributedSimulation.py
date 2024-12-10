import getpass
import os
from platform import machine
import select
import paramiko
from paramiko import SSHClient
from scp import SCPClient
import threading
import time

# Remember to build the project before distributing it
# $ pyinstaller --onefile main.py

# Prompt for the login
login = input("Enter login: ")

# Prompt for the password securely
password = getpass.getpass("Enter password for {}: ".format(login))

remote_folder = "/tmp/{}/sim-and-metrology/".format(login)

# List of computers
allComputers = [
    "tp-1a201-01", "tp-1a201-02", "tp-1a201-04", "tp-1a201-16", "tp-1a201-17",
    "tp-1a201-18", "tp-1a201-19", "tp-1a201-20", "tp-1a201-21", "tp-1a201-23",
    "tp-1a201-25", "tp-1a201-26", "tp-1a201-27", "tp-1a201-28", "tp-1a201-29",
    "tp-1a201-30", "tp-1a201-31", "tp-1a201-32", "tp-1a201-33", "tp-1a201-34",
    "tp-1a201-36", "tp-1a201-37", "tp-1a201-38", "tp-1a201-39", "tp-1a207-01",
    "tp-1a207-02", "tp-1a207-03", "tp-1a207-04", "tp-1a207-05", "tp-1a207-06",
    "tp-1a207-07", "tp-1a207-08", "tp-1a207-11", "tp-1a207-12", "tp-1a207-13",
    "tp-1a207-14", "tp-1a207-15", "tp-1a207-19", "tp-1a207-17", "tp-1a207-18",
]

# Clear the terminal
os.system("clear")

# Check if there is some repeated computer
if len(allComputers) != len(set(allComputers)):
    print("There are repeated computers")
    exit(0)


burstiness_values = [2, 5, 10]  # 20, 30, 70, 100]
simulation_time = 10**3
periodPrintLR = 10**3
blockSize = 10**1

# Select some computers to run the simulation
computers = allComputers[:len(burstiness_values)]


def stream_output(channel):
    while not channel.exit_status_ready():
        if channel.recv_ready():
            line = channel.recv(1024).decode('utf-8')
            if line:
                print(line, end='')  # Print to keep output visible
            else:
                break
        time.sleep(0.1)  # Avoid busy-waiting

# Deploy the python project on computer
def deploy_project(ssh, remote_folder, machineId=None):
    repo_url = "https://github.com/ArthurMbraga/simulation-and-metrology-project.git"

    def exec_command_with_error_check(command):
        _, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            print(f"Error executing command: {command}")
            print(stderr.read().decode())
            exit(exit_status)
        return stdout

    # Check if remote_folder exists
    exec_command_with_error_check(
        "if [ ! -d {} ]; then mkdir -p {}; fi".format(remote_folder, remote_folder))

    # Check if repository already exists
    stdout = exec_command_with_error_check(
        "cd {} && if [ -d .git ]; then echo 'exists'; fi".format(remote_folder))
    if 'exists' in stdout.read().decode():
        print("Repository already exists in {}".format(machineId))
        print("Pulling repository on {}".format(machineId))
        exec_command_with_error_check(
            "cd {} && git pull".format(remote_folder))
    else:
        print("Cloning repository on {}".format(machineId))
        exec_command_with_error_check(
            "cd {} && git clone {} .".format(remote_folder, repo_url))

    # Check if virtual environment already exists
    stdout = exec_command_with_error_check(
        "cd {} && if [ -d venv ]; then echo 'exists'; fi".format(remote_folder))
    if 'exists' in stdout.read().decode():
        print("Virtual environment already exists in {}".format(machineId))
    else:
        print("Creating virtual environment on {}".format(machineId))
        exec_command_with_error_check(
            "cd {} && python3 -m venv venv".format(remote_folder))

    print("Installing requirements on {}".format(machineId))
    exec_command_with_error_check(
        "cd {} && source venv/bin/activate && pip install -r requirements.txt".format(remote_folder))


# Attach the terminal to the process and print all output until python process ends
def attach_and_run_simulation(ssh, burstiness, simulation_time, periodPrintLR, blockSize, index):
    command = (
        f"cd {remote_folder} && source venv/bin/activate && python3 main.py "
        f"--burstiness {burstiness} "
        f"--simulation_time {simulation_time} "
        f"--periodPrintLR {periodPrintLR} "
        f"--blockSize {blockSize}"
        f"--barPosition {index}"
    )
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)

    # Start a thread to stream the stdout
    stdout_thread = threading.Thread(
        target=stream_output, args=(stdout.channel,))
    stderr_thread = threading.Thread(
        target=stream_output, args=(stderr.channel,))
    stdout_thread.start()
    stderr_thread.start()

    # Wait for the process to end
    stdout.channel.recv_exit_status()
    stderr.channel.recv_exit_status()

    print("Simulation finished for burstiness {}".format(burstiness))

    # Update local metrics file
    print("Downloading results for burstiness {}".format(burstiness))
    with SCPClient(ssh.get_transport()) as scp:
        scp.get(
            f"{remote_folder}results/response_times_burstiness_{burstiness}.csv", "./results/")
        scp.get(
            f"{remote_folder}results/block_response_times_burstiness_{burstiness}.csv", "./results/")


# Run the simulation on the computer
def run_simulation_on_computer(index, c):
    try:
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(c, username=login, password=password)
        print("Connected to {}".format(c))

        print("Deploying project on {}".format(c))
        deploy_project(ssh, remote_folder, c)
        print("Project deployed on {}".format(c))

        attach_and_run_simulation(
            ssh, burstiness_values[index], simulation_time, periodPrintLR, blockSize, index)
    except paramiko.AuthenticationException:
        print("Authentication failed for {}".format(c))
    except paramiko.SSHException as ssh_exception:
        print("SSH connection failed for {}: {}".format(c, str(ssh_exception)))
    finally:
        ssh.close()


threads = []
for idx, c in enumerate(computers):
    thread = threading.Thread(
        target=run_simulation_on_computer, args=(idx, c))
    print("Starting thread for {}".format(c))
    thread.start()
    threads.append(thread)  # Add the thread to the list

# Wait for all threads to finish in reverse order
for t in reversed(threads):
    t.join()


# Kill all processes
for c in computers:
    try:
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(c, username=login, password=password)
        ssh.exec_command("pkill -u {}".format(login))
    except paramiko.AuthenticationException:
        print("Authentication failed for {}".format(c))
        break
    except paramiko.SSHException as ssh_exception:
        print("SSH connection failed for {}: {}".format(c, str(ssh_exception)))
    finally:
        ssh.close()
