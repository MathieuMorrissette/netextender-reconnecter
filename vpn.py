import sys
import getpass
import time
import pty
import os
import subprocess
import threading
import re

#script must be ran as sudo

user = getpass.getpass(prompt='User:', stream=None)
domain = getpass.getpass(prompt='Domain:', stream=None)
server = getpass.getpass(prompt='Server:', stream=None)
password = getpass.getpass(prompt='Password:', stream=None) + "\n"

def get_pid(name):
    try:
        return subprocess.check_output(["pidof", name]).decode().strip()
    except:
        return None

reconnection_count = 0

while True:
    print("reconnection count = " + str(reconnection_count))
    reconnection_count = reconnection_count + 1

    pid = get_pid("netExtender")

    while pid != None:
        print("killing netextender")
        subprocess.run(["kill", pid])
        time.sleep(5)
        pid = get_pid("netExtender")

    # netExtender requires a tty to run else it makes an infinite loop with errors so here we are faking one
    master, slave = pty.openpty()
    process = subprocess.Popen("netExtender -u "+ user +" -d " + domain + " " + server + " --no-routes", shell=True,stdin=slave, stdout=slave, close_fds=True)

    output_stream = os.fdopen(master, 'rb', 0)
    input_stream = os.fdopen(master, 'wb', 0)

    def test():
        warning_count = 0

        while process.poll() is None:

            line = output_stream.read(1000).decode('utf-8').strip()

            if line == '':
                continue

            print(line)

            if "Password:" in line:
                input_stream.write(password.encode("utf-8"))

            if "NetExtender connected successfully" in line:
                time.sleep(2)
                subprocess.run(["ip", "route", "add", "default", "dev", "ppp0"])

            if "Do you want to proceed?" in line:
                yes = "y\n"
                input_stream.write(yes.encode("utf-8"))
            
            if "Client IP Address: " in line:
                time.sleep(2)
                ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', line)
                client_ip = ip[0]

                print("Found ip" + client_ip)

                # ex : add some routes to internal vpn networks
                # subprocess.run(["ip", "route", "add", "192.168.0.0/24", "via", client_ip])

                print("added routes")

            if "ERROR" in line:
                process.terminate()
                time.sleep(10)
                break

            if "SSL VPN connection is terminated." in line:
                process.terminate()
                time.sleep(10)
                break

            

    test()


    # no route prevent netextender from creating bad routes
