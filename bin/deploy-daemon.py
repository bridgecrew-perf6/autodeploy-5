#!/usr/bin/env python3

from autodeploy.daemon import SyncServer
from autodeploy.util import run_serverclass_thread

if __name__ == "__main__":
    run_serverclass_thread(SyncServer())
