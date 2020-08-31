#!/usr/bin/env python

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import random
import os
import sys

import fastai
from fastai.tabular import pd

from xjson import *
import logs
from model import Model


class Card(object):
    def __init__(self):
        pass

    def log_name(self):
        if self.upgrades > 0:
            return self.id + "+" + str(self.upgrades)
        else:
            return self.id


Card.parser = xobj(
    Card,
    {
        "exhausts": xbool,
        "is_playable?": xbool,
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


class ScreenState(object):
    def __init__(self):
        pass


ScreenState.parser = xobj(
    ScreenState,
    {
        "cards?": xlist(Card.parser),
        "bowl_available?": xbool,
        "skip_available?": xbool,
        "relics?": xlist(Relic.parser),
    },
)


class CombatState(object):
    def __init__(self):
        pass

    def possible_plays(self):
        """
        Returns a list of (card index, target index) tuples.
        Card index is 1-indexed for compatibility with communication mod.
        Target index is None if this card doesn't target.
        """
        answer = []
        for zero_indexed_card_index, card in enumerate(self.hand):
            card_index = zero_indexed_card_index + 1
            if not card.is_playable:
                continue
            if card.has_target:
                for target_index in range(len(self.monsters)):
                    answer.append((card_index, target_index))
            else:
                answer.append((card_index, None))
        return answer


CombatState.parser = xobj(
    CombatState,
    {
        "draw_pile": xlist(Card.parser),
        "discard_pile": xlist(Card.parser),
        "exhaust_pile": xlist(Card.parser),
        "cards_discarded_this_turn": xint,
        "monsters": xlist(xany),
        "limbo": xany,
        "turn": xint,
        "hand": xlist(Card.parser),
        "player": xany,
    },
)


class CurrentGameState(object):
    def __init__(self):
        pass

    def can_predict_card_choice(self):
        if self.screen_type != "CARD_REWARD":
            return False
        if not self.screen_state.cards or len(self.screen_state.cards) != 3:
            return False
        return True

    def card_choices(self):
        return [card.log_name() for card in self.screen_state.cards]

    def relic_choices(self):
        return [relic.id for relic in self.screen_state.relics]

    def predict_choice(self, choices):
        """
        learn is an already-trained learning model. see the jupyter notebook for more info
        Returns a list of (card, probability) tuples
        """
        deck = self.deck_for_prediction()
        relics = self.relics_for_prediction()
        testcsv = logs.mini_csv(self._class.upper(), self.floor, deck, relics, choices)
        testf = pd.read_csv(testcsv)
        model = Model(self._class)
        values = model.predict_iloc(testf.iloc[0])
        return zip(choices + ["Skip"], values)

    def predict_card_choice(self):
        return self.predict_choice(self.card_choices())

    def predict_relic_choice(self):
        return self.predict_choice(self.relic_choices())

    def can_predict_relic_choice(self):
        if self.screen_type != "BOSS_REWARD":
            return False
        if not self.screen_state.relics or len(self.screen_state.relics) != 3:
            return False
        return True

    def deck_for_prediction(self):
        answer = [card.log_name() for card in self.deck]
        if "AscendersBane" not in answer:
            answer.append("AscendersBane")
        return answer

    def relics_for_prediction(self):
        return [r.id for r in self.relics]


CurrentGameState.parser = xobj(
    CurrentGameState,
    {
        "choice_list?": xlist(xstr),
        "screen_type": xstr,
        "screen_state": ScreenState.parser,
        "combat_state?": CombatState.parser,
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


def play_command(card_index, target_index):
    if target_index is None:
        return f"PLAY {card_index}"
    return f"PLAY {card_index} {target_index}"


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
                    "game_state?": CurrentGameState.parser,
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

    def can_play(self):
        return "play" in self.available_commands

    def dumps(self):
        return json.dumps(self.data, indent=2)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Hello world! I should put some status information here.")

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length).decode()
        status = Status.parse(body.strip())
        game = status.game_state
        command = None

        if game is None:
            print("status.game_state is None")
        elif game.screen_name == "SETTINGS":
            print("in settings screen")
        elif status.can_play():
            plays = game.combat_state.possible_plays()
            print("XXX", plays)
            commands = [
                play_command(card_index, target_index)
                for card_index, target_index in plays
            ]

            if commands:
                print("choices:")
                for command in commands:
                    print(command)
                command = random.choice(commands)
                print("choosing:", command)
            else:
                # print(status.dumps())
                print("no plays")
        elif game.can_predict_card_choice():
            print("predicting card choice...")
            for card, value in game.predict_card_choice():
                print("{:5.3f} {}".format(value, card))
        elif game.can_predict_relic_choice():
            print("predicting relic choice...")
            for relic, value in game.predict_relic_choice():
                print("{:5.3f} {}".format(value, relic))
        else:
            print(status.dumps())
            print("don't know what to do")

        self.send_response(200)
        self.end_headers()
        message = {"command": command}
        self.wfile.write(json.dumps(message).encode())


if __name__ == "__main__":
    port = 7777
    httpd = HTTPServer(("", port), Handler)
    print(f"running brain on port {port}....")
    httpd.serve_forever()
