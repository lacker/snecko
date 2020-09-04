#!/usr/bin/env python

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import queue
import sys
import threading

# For json-encoded lines of text sent to the mod
QUEUE = queue.Queue()


def log(message):
    f = open(os.path.expanduser("~/mod.log"), "a+")
    f.write(message + "\n")
    f.close()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Hello world! I should put some status information here.")

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        command = self.rfile.read(content_length).decode().strip()

        # Clear the queue
        while not QUEUE.empty():
            try:
                QUEUE.get_nowait()
            except:
                pass

        log("command: " + command)
        print(command, flush=True)

        try:
            line = QUEUE.get(block=True, timeout=3.0)
        except:
            line = json.dumps({"error": "no response"}).encode()

        self.send_response(200)
        self.end_headers()
        self.wfile.write(line)


def server():
    port = 7777
    httpd = HTTPServer(("", port), Handler)
    httpd.serve_forever()


def game_communicator():
    log("ready")
    print("ready", flush=True)
    for line in sys.stdin:
        QUEUE.put(line)


if __name__ == "__main__":
    t1 = threading.Thread(target=server)
    t1.start()
    t2 = threading.Thread(target=game_communicator)
    t2.start()

    # We should exit when the game exits. The server thread never exits on its own
    t2.join()
