#!/usr/bin/env python


import json
import random
import os

from vectorize import *
from xjson import *
import logs

MAX_CHOICES = 30
MAX_MONSTERS = 5
LOG = open(os.path.expanduser("~/brain.log"), "a+")

END = 0
PLAY = 1
CHOOSE = 2
NUM_ACTIONS = 3


def log(message):
    LOG.write(message + "\n")


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
        "cost": xint,
        "exhausts": xbool,
        "has_target": xbool,
        "id": xstr,
        "is_playable?": xbool,
        "name": xstr,
        "rarity": xstr,
        "type": xstr,
        "upgrades": xint,
    },
)

Card.vectorizer = VObj(
    {
        "cost": VInt(size=3),
        "exhausts": VBool,
        "has_target": VBool,
        "is_playable": VBool,
        "name": VStr(size=3),
        "rarity": VStr(size=1),
        "type": VStr(size=1),
        "upgrades": VInt(size=5),
    },
)


class Relic(object):
    def __init__(self):
        pass


Relic.parser = xobj(Relic, {"name": xstr, "id": xstr, "counter": xint})

Relic.vectorizer = VObj({"counter": VInt(size=4), "name": VStr(size=3),})


class Potion(object):
    def __init__(self):
        pass


Potion.parser = xobj(
    Potion,
    {
        "can_discard": xbool,
        "can_use": xbool,
        "id": xstr,
        "name": xstr,
        "requires_target": xbool,
    },
)

Potion.vectorizer = VObj(
    {
        "can_discard": VBool,
        "can_use": VBool,
        "id": VStr(),
        "name": VStr(),
        "requires_target": VBool,
    }
)


class ScreenState(object):
    def __init__(self):
        pass


ScreenState.parser = xobj(
    ScreenState,
    {
        "bowl_available?": xbool,
        "cards?": xlist(Card.parser),
        "relics?": xlist(Relic.parser),
        "skip_available?": xbool,
    },
)

ScreenState.vectorizer = VObj(
    {
        "bowl_available": VBool,
        "cards": VList(Card.vectorizer),
        "relics": VList(Relic.vectorizer),
        "skip_available": VBool,
    }
)


class Monster(object):
    def __init__(self):
        pass


Monster.parser = xobj(
    Monster,
    {
        "block": xint,
        "current_hp": xint,
        "half_dead": xbool,
        "id": xstr,
        "intent": xstr,
        "is_gone": xbool,
        "max_hp": xint,
        "move_adjusted_damage": xint,
        "move_base_damage": xint,
        "move_hits": xint,
        "move_id": xint,
        "name": xstr,
        "powers": xany,
    },
)

Monster.vectorizer = VObj(
    {
        "block": VInt(),
        "current_hp": VInt(),
        "half_dead": VBool,
        "intent": VStr(size=1),
        "is_gone": VBool,
        "max_hp": VInt(),
        "move_adjusted_damage": VInt(),
        "move_base_damage": VInt(),
        "move_hits": VInt(),
        "move_id": VInt(),
        "name": VStr(size=3),
    }
)


class PlayerState(object):
    def __init__(self):
        pass


PlayerState.parser = xobj(
    PlayerState,
    {
        "block": xint,
        "current_hp": xint,
        "energy": xint,
        "max_hp": xint,
        "orbs": xany,
        "powers": xany,
    },
)

PlayerState.vectorizer = VObj(
    {"block": VInt(), "current_hp": VInt(), "energy": VInt(), "max_hp": VInt(),}
)


class CombatState(object):
    def __init__(self):
        pass

    def targets(self):
        answer = []
        for index, monster in enumerate(self.monsters):
            if not monster.is_gone:
                answer.append(index)
        return answer

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
                for target_index in self.targets():
                    answer.append((card_index, target_index))
            else:
                answer.append((card_index, None))
        return answer


CombatState.parser = xobj(
    CombatState,
    {
        "cards_discarded_this_turn": xint,
        "discard_pile": xlist(Card.parser),
        "draw_pile": xlist(Card.parser),
        "exhaust_pile": xlist(Card.parser),
        "hand": xlist(Card.parser),
        "limbo": xany,
        "monsters": xlist(Monster.parser),
        "player": PlayerState.parser,
        "turn": xint,
    },
)

CombatState.vectorizer = VObj(
    {
        "cards_discarded_this_turn": VInt(),
        "hand": VList(Card.vectorizer, size=10),
        "monsters": VList(Monster.vectorizer, size=5),
        "player": PlayerState.vectorizer,
        "turn": VInt(),
    }
)


class GameState(object):
    def __init__(self):
        pass


GameState.parser = xobj(
    GameState,
    {
        "act_boss": xstr,
        "act": xint,
        "action_phase": xstr,
        "ascension_level": xint,
        "choice_list?": xlist(xstr),
        "class": xstr,
        "combat_state?": CombatState.parser,
        "current_hp": xint,
        "deck": xlist(Card.parser),
        "floor": xint,
        "gold": xint,
        "is_screen_up": xbool,
        "map?": xany,
        "max_hp": xint,
        "potions": xlist(Potion.parser),
        "relics": xlist(Relic.parser),
        "room_phase": xstr,
        "room_type": xstr,
        "screen_name": xstr,
        "screen_state": ScreenState.parser,
        "screen_type": xstr,
        "seed": xint,
    },
)

GameState.vectorizer = VObj(
    {
        "act_boss": VStr(),
        "act": VInt(size=3),
        "action_phase": VStr(),
        "ascension_level": VInt(size=5),
        "choice_list": VList(VStr(size=3), size=MAX_CHOICES),
        "class": VStr(),
        "combat_state": CombatState.vectorizer,
        "current_hp": VInt(),
        "deck": VList(Card.vectorizer, size=40),
        "floor": VInt(),
        "gold": VInt(),
        "is_screen_up": VBool,
        "max_hp": VInt(),
        "potions": VList(Potion.vectorizer, size=5),
        "relics": VList(Relic.vectorizer, size=20),
        "room_phase": VStr(),
        "room_type": VStr(),
        "screen_name": VStr(),
        "screen_state": ScreenState.vectorizer,
        "screen_type": VStr(),
    }
)


def play_command(card_index, target_index):
    if target_index is None:
        return f"PLAY {card_index}"
    return f"PLAY {card_index} {target_index}"


class BadCommandError(Exception):
    pass


class Status(object):
    def __init__(self):
        pass

    @staticmethod
    def parse(string):
        data = json.loads(string)
        if "error" in data:
            print(json.dumps(data, indent=2))
            raise BadCommandError(data["error"])
        status = Status.parser(data)
        status.data = data
        try:
            # Just to clean up our debug output
            del status.data["game_state"]["map"]
        except:
            pass
        return status

    def make_command(action, index1, index2):
        """
        Raises a ValueError if this isn't a valid command for the game state.
        """
        if action == END:
            # END is a catchall that includes every command that does nothing.
            if self.can_end():
                return "END"
            if self.can_proceed():
                return "PROCEED"
            if self.can_confirm():
                return "CONFIRM"
            if self.can_leave():
                return "LEAVE"
            raise ValueError("cannot END")

        if action == PLAY:
            if not self.can_play():
                raise ValueError("cannot PLAY")
            # The first play index is 1-indexed
            command = make_command(index1 + 1, index2)
            if command not in self.game_state.combat_state.possible_plays():
                raise ValueError("invalid PLAY")
            return command

        if action == CHOOSE:
            # index2 is ignored
            if not self.can_choose():
                raise ValueError("cannot CHOOSE")
            choices = self.game_state.choice_list
            if index1 >= len(choices):
                raise ValueError("invalid CHOOSE")
            return f"CHOOSE {choices[index1]}"

    def can_proceed(self):
        return "proceed" in self.available_commands

    def can_play(self):
        return "play" in self.available_commands

    def can_choose(self):
        return "choose" in self.available_commands

    def can_end(self):
        return "end" in self.available_commands

    def can_confirm(self):
        return "confirm" in self.available_commands

    def can_leave(self):
        return "leave" in self.available_commands

    def has_commands(self):
        """
        Whether we can generate a list of possible commands from this state.
        """
        return any(
            [
                self.can_proceed(),
                self.can_play(),
                self.can_choose(),
                self.can_end(),
                self.can_confirm(),
                self.can_leave(),
            ]
        )

    def potions_full(self):
        return all([potion.can_discard for potion in self.game_state.potions])

    def get_commands(self):
        """
        Returns a list of possible commands.
        """
        commands = []

        if self.can_play():
            plays = self.game_state.combat_state.possible_plays()
            commands += [
                play_command(card_index, target_index)
                for card_index, target_index in plays
            ]

        if self.can_end():
            commands.append("END")

        if self.can_choose():
            for choice in self.game_state.choice_list:
                if choice == "potion" and self.potions_full():
                    pass
                else:
                    commands.append(f"CHOOSE {choice}")

        if self.can_proceed():
            commands.append("PROCEED")

        if self.can_confirm():
            commands.append("CONFIRM")

        if self.can_leave():
            commands.append("LEAVE")

        return commands

    def has_game(self):
        return self.game_state is not None

    def in_settings(self):
        return self.has_game() and self.game_state.screen_name == "SETTINGS"

    def is_death(self):
        return self.has_game() and self.game_state.screen_name == "DEATH"

    def dumps(self):
        return json.dumps(self.data, indent=2)


Status.parser = xobj(
    Status,
    {
        "available_commands": xlist(xstr),
        "game_state?": GameState.parser,
        "in_game": xbool,
        "ready_for_command": xbool,
    },
)

Status.vectorizer = VObj(
    {
        "game_state": GameState.vectorizer,
        "in_game": VBool,
        "ready_for_command": VBool,
        "available_commands": VList(VStr()),
    }
)
