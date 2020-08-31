#!/usr/bin/env python

import json
import os
import requests
import sys


def log(message):
    f = open(os.path.expanduser("~/snecko.log"), "a+")
    f.write(message + "\n")
    f.close()


if __name__ == "__main__":
    log("ready")
    print("ready", flush=True)
    for line in sys.stdin:
        try:
            r = requests.post("http://127.0.0.1:7777/", data=line)
            response = json.loads(r.content.decode())
            if response["command"]:
                log("sending command: '" + response["command"] + "'")
                print(response["command"])
        except:
            err = str(sys.exc_info()[0])
            log("error: " + err)
            print(err, file=sys.stderr)
