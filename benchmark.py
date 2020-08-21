#!/usr/bin/env python

import os

import brain
from model import Model

DIR = os.path.dirname(__file__)


class MockCard(object):
    def __init__(self, card_id):
        self.id = card_id

    def log_name(self):
        return self.id


if __name__ == "__main__":
    print("initializing...")
    with open(os.path.join(DIR, "test_state.json")) as f:
        raw = f.read()
    game = brain.Status.parse(raw).game_state
    game.screen_type = "CARD_REWARD"
    game.screen_state.cards = list(
        map(MockCard, ["Demon Form", "Whirlwind", "Bloodletting"])
    )
    Model("ironclad")
    assert game.can_predict_card_choice()
    print(list(game.predict_card_choice()))
