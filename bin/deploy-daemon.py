#!/usr/bin/env python3

from autodeploy.daemon import SyncServer, StopServer

import signal
import threading


if __name__ == "__main__":
    s = SyncServer()

    def sighandle(signal, frame):
        raise StopServer()

    signal.signal(signal.SIGTERM, sighandle)
    signal.signal(signal.SIGINT, sighandle)

    server = threading.Thread(target=s.serve_forever)
    server.start()
    while True:
        try:
            signal.pause()
        except StopServer:
            s.shutdown()
            break
    server.join()
