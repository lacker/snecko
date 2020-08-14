#!/usr/bin/env python

import json
import os
import sys

from parser import *

DIR = os.path.dirname(__file__)


class Status(object):
    parser = None

    def __init__(self):
        pass

    @staticmethod
    def parse(string):
        if not Status.parser:
            Status.parser = xobj(Status, {})

        data = json.loads(string)
        status = Status.parser(data)
        status.data = data
        try:
            # Just to clean up our debug output
            del status.data["game_state"]["map"]
        except:
            pass
        return status

    def dumps(self):
        return json.dumps(self.data, indent=2)


def log(message):
    logfile = os.path.join(DIR, "tmp", "mod.log")
    log = open(logfile, "a+")
    print(message, file=log)
    log.close()


if __name__ == "__main__":
    log("mod.py running")

    # TODO: check if we need the flush
    print("ready", flush=True)

    for line in sys.stdin:
        try:
            status = Status.parse(line.strip())
        except json.decoder.JSONDecodeError:
            log(f"json decoding error with: {line}")
            continue
        except ValueError as e:
            log(f"ValueError: {e}")
            continue

        log(f"status: {status.dumps()}")

        # TODO: check if we need this
        print("WAIT 100")
