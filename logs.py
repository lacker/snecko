#!/usr/bin/env python

import json
import os
import random
import requests
import sys
import tarfile
import urllib

from items import CARDS

CACHE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cache")

MONTHS = ["2019-02",
          "2019-03",
          "2019-04",
          "2019-05",
          "2019-06",
          "2019-07",
          "2019-08",
          "2019-09",
          "2019-10",
          "2019-11",
          "2019-12",
          "2020-01",
          "2020-02",
          "2020-03",
          "2020-04",
          "2020-05",
          ]

def get_fname(month):
    return os.path.join(CACHE, month + ".tar.gz")


def download_all():
    # Act like we're not a bot
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)

    for month in MONTHS:
        fname = get_fname(month)
        if os.path.exists(fname):
            continue
        url = f"https://spirelogs.com/archive/{month}.tar.gz"
        print("downloading", url)
        urllib.request.urlretrieve(url, fname)

def xint(data):
    answer = int(data)
    if answer != data:
        raise ValueError(f"expected int but got {data}")
    return answer

def xstr(data):
    if type(data) != str:
        raise ValueError(f"expected str but got {data}")
    return data

def xbool(data):
    if type(data) != bool:
        raise ValueError(f"expected bool but got {data}")

# Subparser is a function that takes the data and returns the value for a subtype
def xlist(subparser):
    def find_answer(data):
        if type(data) != list:
            raise ValueError(f"expected list but got {data}")
        answer = []
        for value in data:
            answer.append(subparser(value))
        return answer
    return find_answer

# Subparsers has a subparser for each key
# Returns an object of the provided class, constructed with no arguments
# Key ends with "?" to indicate optionality
def xobj(cls, subparsers):
    def find_answer(data):
        if type(data) != dict:
            raise ValueError(f"expected dict but got {data}")
        answer = cls()
        for key, subparser in subparsers.items():
            optional = False
            if key.endswith("?"):
                key = key.strip("?")
                optional = True
            if key not in data:
                if optional:
                    answer.__setattr__(key, None)
                    continue
                raise ValueError(f"expected key {key} but data is {data}")
            value = subparser(data.get(key))
            answer.__setattr__(key, value)
        return answer
    return find_answer

def is_card(s):
    return not s.endswith("Potion")

class BossRelicChoice(object):
    def __init__(self):
        pass
BossRelicChoice.parser = xobj(BossRelicChoice, {
    "not_picked": xlist(xstr),
    "picked?": xstr,
})

class CardChoice(object):
    def __init__(self):
        pass
CardChoice.parser = xobj(CardChoice, {
    "not_picked": xlist(xstr),
    "picked": xstr,
    "floor": xint,
})

class EventChoice(object):
    def __init__(self):
        pass
EventChoice.parser = xobj(EventChoice, {
    "cards_removed?": xlist(xstr),
    "cards_transformed?": xlist(xstr),
    "cards_obtained?": xlist(xstr),
    "event_name": xstr,
    "player_choice": xstr,
    "floor": xint,
})

class CampfireChoice(object):
    def __init__(self):
        pass
CampfireChoice.parser = xobj(CampfireChoice, {
    "data?": xstr,
    "floor": xint,
    "key": xstr,
})

def upgrade(card):
    if "+" not in card:
        return card + "+1"
    left, right = card.split("+")
    answer = left + "+" + str(int(right) + 1)
    if answer not in CARDS:
        # Guess
        return card
    return answer

class GameLog(object):
    parser = None
    
    def __init__(self):
        pass

    def ascension(self):
        return self.data.get("ascension_level", 0)

    def is_high_level(self):
        return self.ascension_level >= 17

    @staticmethod
    def parse(name, bytestring):
        if not GameLog.parser:
            GameLog.parser = xobj(GameLog, {
                "ascension_level": xint,
                "boss_relics": xlist(BossRelicChoice.parser),
                "card_choices": xlist(CardChoice.parser),
                "campfire_choices": xlist(CampfireChoice.parser),
                "character_chosen": xstr,
                "chose_seed": xbool,
                "daily_mods?": xlist(xstr),
                "event_choices": xlist(EventChoice.parser),
                "floor_reached": xint,
                "is_daily": xbool,
                "is_endless": xbool,
                "items_purchased": xlist(xstr),
                "item_purchase_floors": xlist(xint),
                "items_purged": xlist(xstr),
                "items_purged_floors": xlist(xint),
                "master_deck": xlist(xstr),
                "neow_bonus": xstr,
                "relics": xlist(xstr),
            })
        
        string = bytestring.decode(encoding="utf-8", errors="replace")
        data = json.loads(string)
        game = GameLog.parser(data)

        # For easy future saving
        game.name = name
        game.bytestring = bytestring
        game.data = data
        return game
    
    @staticmethod
    def get_fname(name):
        return os.path.join(CACHE, "local", name)

    @staticmethod
    def load(name):
        fname = GameLog.get_fname(name)
        bs = open(fname).read()
        return GameLog.parse(name, bs)

    @staticmethod
    def from_json(self, data):
        pass

    def is_good(self):        
        if self.is_daily or self.is_endless or self.chose_seed or self.daily_mods:
            return False
        for card in self.master_deck:
            if card not in CARDS:
                return False
        return self.ascension_level >= 17 
    
    def save(self):
        fname = GameLog.get_fname(self.name)
        f = open(fname, "wb")
        f.write(self.bytestring)
        f.close()

    def show(self):
        print(f"run {self.name}:")
        print(json.dumps(self.data, indent=2))

    def initial_deck(self):
        if self.character_chosen == "IRONCLAD":
            return ["Strike_R"] * 5 + ["Defend_R"] * 4 + ["Bash", "AscendersBane"]
        elif self.character_chosen == "THE_SILENT":
            return ["Strike_G"] * 5 + ["Defend_G"] * 5 + ["Neutralize", "Survivor", "AscendersBane"]
        elif self.character_chosen == "DEFECT":
            return ["Strike_B"] * 4 + ["Defend_B"] * 4 + ["Dualcast", "Zap", "AscendersBane"]
        elif self.character_chosen == "WATCHER":
            return ["Strike_P"] * 4 + ["Defend_P"] * 4 + ["Eruption", "Vigilance", "AscendersBane"]
        else:
            raise ValueError(f"character_chosen is {self.character_chosen}")
        return answer

    def simulate(self):
        """
        Yields one tuple for each card choice.
        (current floor, current decklist, picked cards, not picked cards).
        """
        # The types of action.
        # Upgrades are represented as an addition and removal for the same floor.
        # Order is important.
        DECISION = 0
        ADDITION = 1
        REMOVAL = 2
        
        # actions is a list of floor, type, data tuples.
        # For decision, data is a tuple of lists, (picked, not_picked).
        # Otherwise, data is the card name.
        
        actions = []
        for choice in self.card_choices:
            if choice.picked == "SKIP":
                picked = []
            else:
                picked = [choice.picked]
            actions.append((choice.floor, DECISION, (picked, choice.not_picked)))

            if choice.picked not in ["SKIP", "Singing Bowl"]:
                actions.append((choice.floor, ADDITION, choice.picked))

        for choice in self.event_choices:
            if choice.event_name == "Liars Game" and choice.player_choice == "agreed":
                actions.append((choice.floor, ADDITION, "Doubt"))
            if choice.cards_removed:
                for card in choice.cards_removed:
                    actions.append((choice.floor, REMOVAL, card))
            if choice.cards_transformed:
                for card in choice.cards_transformed:
                    actions.append((choice.floor, REMOVAL, card))
            if choice.cards_obtained:
                for card in choice.cards_obtained:
                    actions.append((choice.floor, ADDITION, card))

        for choice in self.campfire_choices:
            if choice.key == "SMITH":
                actions.append((choice.floor, REMOVAL, choice.data))
                actions.append((choice.floor, ADDITION, upgrade(choice.data)))
                
        for floor, item in zip(self.item_purchase_floors, self.items_purchased):
            if item in CARDS:
                actions.append((floor, ADDITION, item))
        for floor, item in zip(self.items_purged_floors, self.items_purged):
            if item in CARDS:
                actions.append((floor, REMOVAL, item))

        for floor, choice in zip([17, 33, 50], self.boss_relics):
            if choice.picked == "Calling Bell":
                actions.append((floor, ADDITION, "CurseOfTheBell"))

        deck = self.initial_deck()
        actions.sort()
        for floor, action_type, data in actions:
            if action_type == DECISION:
                picked, not_picked = data
                yield floor, deck, picked, not_picked
            elif action_type == REMOVAL:
                if data not in deck:
                    continue
                if data not in CARDS:
                    raise ValueError(f"cannot remove bad card: {data}")
                deck.remove(data)
            elif action_type == ADDITION:
                if data not in CARDS:
                    # This was probably a modded game. Just ditch
                    return
                deck.append(data)
            else:
                raise ValueError(f"unknown action_type: {action_type}")
                
        master = sorted(self.master_deck)
        repro = sorted(deck)
        # You can check if master==repro here to see how accurate the simulation was.
        
    
    
def iter_logs():
    for month in MONTHS:
        fname = get_fname(month)
        tf = tarfile.open(fname)
        # Each member is a <id>.run.json file
        for member in tf.getmembers():
            if member.isdir():
                continue
            name = os.path.basename(member.name)
            f = tf.extractfile(member)
            if f is None:
                print(member)
                raise Exception("could not extract")
            bs = f.read()
            if not bs:
                continue

            try:
                game = GameLog.parse(name, bs)
            except json.decoder.JSONDecodeError:
                # Some of this input data is bad json
                continue
            except ValueError:
                # Used for my own format skips
                continue
            
            yield game
            
def iter_local():
    for entry in os.scandir(os.path.join(CACHE, "local")):
        name = os.path.basename(entry.name)
        f = open(entry, "rb")
        bs = f.read()
        game = GameLog.parse(name, bs)
        yield game
        
def save_good_games_locally():
    counter = 0
    for game in iter_logs():
        if game.is_good():
            game.save()
            counter += 1
            if counter % 100 == 0:
                print(counter, "games saved locally")
    print("done. total:", counter)

    
def generate_csv(character):
    """
    Prints out one big csv with all training data.
    The columns are:
    Character
    Floor
    Deck Size
    Choice1
    Choice2
    Choice3
    Picked - 1, 2, 3, or skip
    Hundreds of columns for cards, with a count of how many are in the deck
    """
    cards = sorted(list(CARDS))
    header = "Character,Floor,Deck Size,Choice1,Choice2,Choice3,Picked," + ",".join(cards)
    print(header)
    games = 0
    for game in iter_local():
        if not game.is_good() or game.character_chosen != character:
            continue
        for floor, deck, picked, not_picked in game.simulate():
            choices = picked + not_picked
            if len(choices) != 3:
                continue
            random.shuffle(choices)
            if picked and picked[0] in choices:
                picked_value = str(choices.index(picked[0]) + 1)
            else:
                picked_value = "skip"
            deck_entries = []
            for card in cards:
                deck_entries.append(str(deck.count(card)))
            row = [game.character_chosen, str(floor), str(len(deck))] + choices + [picked_value] + deck_entries
            print(",".join(row))
        games += 1
        if games % 100 == 0:
            print(f"processed {games} games", file=sys.stderr)
                               
def count_cards():
    """
    Useful for printing out the least frequent cards, so we can clean up the data.
    """
    count = {}
    for game in iter_local():
        if not game.is_good():
            continue
        for card in game.master_deck:
            count[card] = count.get(card, 0) + 1

    counts = [(value, key) for key, value in count.items()]
    counts.sort()
    for count in counts:
        print(count)
            
if __name__ == "__main__":
    generate_csv("THE_SILENT")
