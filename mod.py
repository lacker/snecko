#!/usr/bin/env python

import json
import requests
import sys

if __name__ == "__main__":
    print("ready", flush=True)
    for line in sys.stdin:
        r = requests.post("http://127.0.0.1:7777/", data=line)
        response = json.loads(r.content.decode())
        if response["command"]:
            print(response["command"])
