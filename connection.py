#!/usr/bin/env python

import random
import requests
import sys
import time

from game import BadCommandError, Status


class Connection(object):
    def __init__(self):
        self.status = None

    def send(self, command):
        """
        Raises a BadCommandError if there is a bad command.
        self.status ends up set iff the send worked.
        Returns whether the send worked.
        """
        self.status = None
        try:
            r = requests.post("http://127.0.0.1:7777/", data=command, timeout=10)
        except requests.exceptions.ConnectionError:
            print("could not connect to the mod. is it running?")
            return False
        except requests.exceptions.ReadTimeout:
            print("request timed out.")
            return False

        self.status = Status.parse(r.text)
        return True

    def issue_command(self, command):
        """
        Like send, but ensures that status is up-to-date afterwards.
        """
        success = self.send(command)
        if not success:
            self.get_status()
        return self.status

    def start_game(self):
        self.issue_command("START IRONCLAD")

    def get_status(self):
        """
        Retries as needed to figure out the game status.
        """
        while self.status is None:
            self.send("STATE")
            if not self.status:
                print("state command failed. is the game running?")
                time.sleep(2)
        return self.status

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
        self.get_status()
        if not self.status.has_game():
            self.start_game()
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
