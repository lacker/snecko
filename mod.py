#!/usr/bin/env python

import os
import sys

DIR = os.path.dirname(__file__)

if __name__ == "__main__":
    logfile = os.path.join(DIR, "tmp", "mod.log")
    log = open(logfile, "w")
    print("ready to log stuff", file=log)
    print("Ready")
    for line in sys.stdin:
        print(f"received: {line}", file=log, flush=True)
        print("WAIT 100")
