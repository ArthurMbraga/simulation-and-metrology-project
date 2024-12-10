import getpass
import os
import select
import paramiko
from paramiko import SSHClient
from scp import SCPClient
import threading

# Remember to build the project before distributing it
# $ pyinstaller --onefile main.py

# Prompt for the login
login = input("Enter login: ")

# Prompt for the password securely
password = getpass.getpass("Enter password for {}: ".format(login))

remote_folder = "/tmp/{}/".format(login)

# List of computers
allComputers = [
    "tp-1a201-01", "tp-1a201-03", "tp-1a201-04", "tp-1a201-16", "tp-1a201-17",
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


burstiness_values = [1]  # , 2, 5, 10, 20, 30, 70, 100]
simulation_time = 10**4
periodPrintLR = 10**3
blockSize = 10**1

# Select some computers to run the simulation
computers = allComputers[:len(burstiness_values)]


# Deploy the python project on computer
def deploy_project(ssh, remote_folder):
    repo_url = "https://github.com/ArthurMbraga/simulation-and-metrology-project.git"

    # Check if repository already exists
    _, stdout, _ = ssh.exec_command(
        "cd {} && if [ -d .git ]; then echo 'exists'; fi".format(remote_folder))
    if 'exists' in stdout.read().decode():
        print("Repository already exists in {}".format(remote_folder))
    else:
        print("Cloning repository on {}".format(remote_folder))
        _, stdout, _ = ssh.exec_command(
            "cd {} && git clone {} .".format(remote_folder, repo_url))
        stdout.channel.recv_exit_status()

    # Check if virtual environment already exists
    _, stdout, _ = ssh.exec_command(
        "cd {} && if [ -d venv ]; then echo 'exists'; fi".format(remote_folder))
    if 'exists' in stdout.read().decode():
        print("Virtual environment already exists in {}".format(remote_folder))
    else:
        print("Creating virtual environment on {}".format(remote_folder))
        _, stdout, _ = ssh.exec_command(
            "cd {} && python3 -m venv venv".format(remote_folder))
        stdout.channel.recv_exit_status()

    print("Installing requirements on {}".format(remote_folder))
    _, stdout, _ = ssh.exec_command(
        "cd {} && source venv/bin/activate && pip install -r requirements.txt".format(remote_folder))
    stdout.channel.recv_exit_status()

# Attach the terminal to the process and print all output until python process ends


def attach_and_run_simulation(ssh, burstiness, simulation_time, periodPrintLR, blockSize):
    command = (
        f"cd {remote_folder} && source venv/bin/activate && python3 main.py "
        f"--burstiness {burstiness} "
        f"--simulation_time {simulation_time} "
        f"--periodPrintLR {periodPrintLR} "
        f"--blockSize {blockSize}"
    )
    stdin, stdout, stderr = ssh.exec_command(command)

   # Print stdout and stderr in real-time
    while True:
        # Use select to wait for data to be available on either stdout or stderr
        ready, _, _ = select.select([stdout.channel, stderr.channel], [], [])
        if stdout.channel in ready:
            line = stdout.readline()
            if line:
                print(line, end='')
            else:
                break
        if stderr.channel in ready:
            line = stderr.readline()
            if line:
                print(line, end='')
            else:
                break

    # Update local metrics file
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
        deploy_project(ssh, remote_folder)
        print("Project deployed on {}".format(c))

        attach_and_run_simulation(
            ssh, burstiness_values[index], simulation_time, periodPrintLR, blockSize)
    except paramiko.AuthenticationException:
        print("Authentication failed for {}".format(c))
    except paramiko.SSHException as ssh_exception:
        print("SSH connection failed for {}: {}".format(c, str(ssh_exception)))
    finally:
        ssh.close()


index = -1
threads = []
for index, c in enumerate(computers):
    thread = threading.Thread(
        target=run_simulation_on_computer, args=(index, c))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()


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
