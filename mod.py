#!/usr/bin/env python

import json
import os
import sys

# A hack because when a Slay The Spire mod invokes this Python script, it doesn't have a nice pythonpath.
DIR = os.path.dirname(__file__)
sys.path.append(DIR)

from xjson import *


class Card(object):
    def __init__(self):
        pass


Card.parser = xobj(
    Card,
    {
        "exhausts": xbool,
        "is_playable": xbool,
        "cost": xint,
        "name": xstr,
        "id": xstr,
        "type": xstr,
        "upgrades": xint,
        "rarity": xstr,
        "has_target": xbool,
    },
)


class Relic(object):
    def __init__(self):
        pass


Relic.parser = xobj(Relic, {"name": xstr, "id": xstr, "counter": xint})


class Potion(object):
    def __init__(self):
        pass


Potion.parser = xobj(
    Potion,
    {
        "requires_target": xbool,
        "can_use": xbool,
        "can_discard": xbool,
        "name": xstr,
        "id": xstr,
    },
)


class GameState(object):
    def __init__(self):
        pass


GameState.parser = xobj(
    GameState,
    {
        "choice_list": xlist(xstr),
        "screen_type": xstr,
        "screen_state": xany,
        "seed": xint,
        "deck": xlist(Card.parser),
        "relics": xlist(Relic.parser),
        "max_hp": xint,
        "act_boss": xstr,
        "gold": xint,
        "action_phase": xstr,
        "act": xint,
        "screen_name": xstr,
        "room_phase": xstr,
        "is_screen_up": xbool,
        "potions": xlist(Potion.parser),
        "current_hp": xint,
        "floor": xint,
        "ascension_level": xint,
        "class": xstr,
        "map": xany,
        "room_type": xstr,
    },
)


class Status(object):
    parser = None

    def __init__(self):
        pass

    @staticmethod
    def parse(string):
        if not Status.parser:
            Status.parser = xobj(
                Status,
                {
                    "available_commands": xlist(xstr),
                    "ready_for_command": xbool,
                    "in_game": xbool,
                    "game_state": GameState.parser,
                },
            )

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

        log(f"\nstatus: {status.dumps()}")
        log(f"screen type: {status.game_state.screen_type}")

        # TODO: check if we need this
        print("WAIT 100")
