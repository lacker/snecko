#!/usr/bin/env python

import random
import requests
import sys

from game import BadCommandError, Status


class Connection(object):
    def __init__(self):
        self.status = None

    def send(self, command):
        """
        Raises a BadCommandError if there is a bad command.
        """
        try:
            r = requests.post("http://127.0.0.1:7777/", data=command, timeout=10)
        except requests.exceptions.ConnectionError:
            print("could not connect to the mod. is it running?")
            return False
        except requests.exceptions.ReadTimeout:
            print("request timed out.")
            return False

        self.status = Status.parse(r.text)

    def make_random_move(self):
        """
        Returns whether we could make a random move.
        """
        if not self.status.has_commands():
            return False
        commands = self.status.get_commands()
        command = random.choice(commands)
        print("randomly choosing:", command)
        self.send(command)
        return True

    def random_playout(self):
        if not self.status:
            self.send("STATE")
        if not self.status.has_game():
            self.send("START IRONCLAD")
        while self.status.has_commands():
            self.make_random_move()

    def handle_command_line(self, command):
        if command == "random":
            self.random_playout()
            return

        if command == "show":
            self.show()
            return

        if command == "json":
            if self.status:
                print(self.status.dumps())
            else:
                print("null")
            return

        try:
            self.send(command)
        except BadCommandError as e:
            print(e)
        self.show()

    def show(self):
        if not self.status:
            print("(no game data yet)")
        elif not self.status.has_game():
            print("we are between games")
        elif self.status.in_settings():
            print("in the settings screen")
        elif self.status.has_commands():
            commands = self.status.get_commands()
            print("possible commands:")
            for c in commands:
                print("  " + c)
        else:
            self.status.show()
            print("unrecognized game state")


if __name__ == "__main__":
    print("type commands to issue them to the STS process.")
    conn = Connection()
    for line in sys.stdin:
        conn.handle_command_line(line.strip())
