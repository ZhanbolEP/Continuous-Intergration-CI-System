import argparse
import os
import re
import socket
import time
import threading

import helpers

def dispatch_test(server, commit_hash):
    while True:
        print("Trying to dispatch")
        for runner in server.runners:
            response = helpers.communicate(runner["host"],
                                           int(runner["port"]),
                                           "runtest: %s" % commit_hash)
            
            if response == "OK":
                print("adding hash %s" % commit_hash)
                server.dispatch_commits[commit_hash]


def serve():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",
                        help="dispatcher's, by default it uses localhost",
                        default="localhost" )
    
    parser.add_argument("--port",
                        help="dispatcher's port -> by default 8888",
                        default=8888)
    
    args = parser.parse_args()

    server = ThreadingTCPServer((args.host, int(args.port)), DisPatcherHandler)
    print('serving on %s:%s' % (args.host, int(args.port)))
    
    def runner_checker(runner):
        def manage_commit_lists(runner):    
            for commit, assigned_runner in list(server.dispatched_commits.items()):
                if assigned_runner == runner:
                    del server.dispatched_commits[commit]
                    server.pending_commits.append(commit)
                    break
                server.runners.remove(runner)

        while not server.dead:
            time.sleep(1)
            for runner in server.runners:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    response = helpers.communicate(runner["host"],
                                                   int(runner["port"]),
                                                   "ping")
                    if response != "pong":
                        print("removing runner %s" % runner)
                        manage_commit_lists(runner)
                except socket.error as e:
                    manage_commit_lists(runner)

    def redistribute(server):
        while not server.dead:
            for commit in server.pending_commits:
                print("running redistribute")
                print(server.pending_commits)
                dispatch_test(server, commit)
                time.sleep(5)
    
    runner_heartbeat = threading.Thread(target=runner_checker, args=(server,))
    redistributor = threading.Thread(target=redistribute, args=(server,))
    try:
        runner_heartbeat.start()
        redistributor.start()
        server.serve_forever()
    except (KeyboardInterrupt, Exception):
        server.dead = True
        server_heartbeat.join()
        redistributor.join()


        