#!/usr/bin/env python

import os
import sys

DIR = os.path.dirname(__file__)


def log(message):
    logfile = os.path.join(DIR, "tmp", "mod.log")
    log = open(logfile, "a+")
    print(message, file=log)
    log.close()


if __name__ == "__main__":
    log("mod.py running")
    print("ready", flush=True)
    for line in sys.stdin:
        log(f"received: {line}")
        print("WAIT 100")
