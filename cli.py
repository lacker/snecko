#!/usr/bin/env python

import sys

from connection import Connection

if __name__ == "__main__":
    print("type commands to issue them to the STS process.")
    conn = Connection()
    while True:
        line = input("> ")
        if line.lower() in ["quit", "q", "exit"]:
            break
        conn.handle_command_line(line)
