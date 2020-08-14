#!/usr/bin/env python

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys

import fastai
import torch
from fastai.tabular import *

from xjson import *
import logs


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


class ScreenState(object):
    def __init__(self):
        pass


ScreenState.parser = xobj(
    ScreenState,
    {"cards?": xlist(Card.parser), "bowl_available?": xbool, "skip_available?": xbool},
)


class GameState(object):
    def __init__(self):
        pass

    def can_predict_card_choice(self):
        if self.screen_type != "CARD_REWARD":
            return False
        if not self.screen_state.cards or len(self.screen_state.cards) != 3:
            return False
        return True

    def predict_card_choice(self):
        """
        Returns a list of (card, probability) tuples
        """
        deck = self.deck_for_prediction()
        relics = self.relics_for_prediction()
        choices = [card.log_name() for card in self.screen_state.cards]
        testcsv = logs.mini_csv("IRONCLAD", self.floor, deck, relics, choices)
        testf = pd.read_csv(testcsv)
        prediction = learn.predict(testf.iloc[0])
        print(prediction)
        # TODO: figure out a nicer way to print this

    def deck_for_prediction(self):
        answer = [card.log_name() for card in self.deck]
        if "AscendersBane" not in answer:
            answer.append("AscendersBane")
        return answer

    def relics_for_prediction(self):
        return [r.id for r in self.relics]


GameState.parser = xobj(
    GameState,
    {
        "choice_list?": xlist(xstr),
        "screen_type": xstr,
        "screen_state": ScreenState.parser,
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
                    "game_state?": GameState.parser,
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


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Hello world! I should put some status information here.")

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length).decode()
        status = Status.parse(body.strip())

        if status.game_state is None:
            print("status.game_state is None")
        else:
            if status.game_state.can_predict_card_choice():
                print("predicting card choice...")
                status.game_state.predict_card_choice()
            else:
                print(f"screen type: {status.game_state.screen_type}")

        self.send_response(200)
        self.end_headers()
        message = {"command": None}
        self.wfile.write(json.dumps(message).encode())


if __name__ == "__main__":
    print(f"loading prediction model....")
    Handler.learn = load_learner(logs.CACHE, "ironclad.learn")
    port = 7777
    httpd = HTTPServer(("", port), Handler)
    print(f"running brain on port {port}....")
    httpd.serve_forever()
