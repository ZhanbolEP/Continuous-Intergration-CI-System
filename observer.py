import argparse
import os
import socket
import subprocess
import sys
import time

import helpers

def poll():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dispatcher-server",
        help="dispatcher host: port, by default it uses localhost: 8888",
        default="localhost:8888",
    )
    parser.add_argument(
        "repo", 
        metavar="REPO", 
        type=str,
        help="path to the repository this will observe"
    )
    args = parser.parse_args()
    dispatcher_host, dispatcher_port = args.dispatcher_server.split(":")
    
    while True:
        try:
            subprocess.check_output(["./update_repo.sh", args.repo])
        except subprocess.CalledProcessError as e:
            raise Exception("Could not update and check repository. Reason: %s" % e.output.decode())
        if os.path.isfile(".commit_hash"):
            try:
                response = helpers.communicate(dispatcher_host, int(dispatcher_port), "status")
            except socket.error as e:
                raise Exception("Could not communicate with dispatcher: %s" % e)
            if response == "OK":
                with open(".commit_hash", "r") as f:
                    commit = f.readline().strip()
            print("dispatched")
        else:
            raise Exception("Could not dispatch the test: %s" % response)
        
    time.sleep(5)

if __name__ == "__main__":
    poll()
