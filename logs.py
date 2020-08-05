#!/usr/bin/env python

import json
import os
import requests
import tarfile
import urllib

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
                "card_choices": xlist(CardChoice.parser),
                "campfire_choices": xlist(CampfireChoice.parser),
                "character_chosen": xstr,
                "chose_seed": xbool,
                "event_choices": xlist(EventChoice.parser),
                "floor_reached": xint,
                "is_daily": xbool,
                "is_endless": xbool,
                "items_purchased": xlist(xstr),
                "item_purchase_floors": xlist(xint),
                "items_purged": xlist(xstr),
                "items_purged_floors": xlist(xint),
                "master_deck": xlist(xstr),
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
        if self.is_daily or self.is_endless or self.chose_seed:
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
        elif self.character_chosen == "SILENT":
            return ["Strike_G"] * 5 + ["Defend_G"] * 5 + ["Neutralize", "Survivor", "AscendersBane"]
        elif self.character_chosen == "DEFECT":
            return ["Strike_B"] * 4 + ["Defend_B"] * 4 + ["Dualcast", "Zap", "AscendersBane"]
        elif self.character_chosen == "WATCHER":
            return ["Strike_P"] * 4 + ["Defend_P"] * 4 + ["Eruption", "Vigilance", "AscendersBane"]
        else:
            raise ValueError(f"character_chosen is {self.character_chosen}")
        return answer

    def validate_deck(self):
        # A list of floor, is_remove, card tuples.
        # Upgrades are represented as an add and a remove for the same floor.
        # is_remove is a bool so that sorting will let us handle adds before removes.
        changes = []
        for choice in self.card_choices:
            if choice.picked != "SKIP":
                changes.append((choice.floor, False, choice.picked))
        for choice in self.event_choices:
            if choice.event_name == "Liars Game" and choice.player_choice == "agreed":
                changes.append((choice.floor, False, "Doubt"))
            if choice.cards_removed:
                for card in choice.cards_removed:
                    changes.append((choice.floor, True, card))
        for choice in self.campfire_choices:
            if choice.key == "SMITH":
                changes.append((choice.floor, True, choice.data))
                changes.append((choice.floor, False, choice.data + "+1"))
        for floor, item in zip(self.item_purchase_floors, self.items_purchased):
            changes.append((floor, False, item))
        for floor, item in zip(self.items_purged_floors, self.items_purged):
            changes.append((floor, True, item))
                
        deck = self.initial_deck()
        for floor, is_remove, card in changes:
            if is_remove:
                if card not in deck:
                    self.show()
                    print(f"could not remove {card} at floor {floor} because deck is {deck}")
                    return False
                deck.remove(card)
            else:
                deck.append(card)
                
        master = sorted(self.master_deck)
        repro = sorted(deck)
        if master == repro:
            return True
        
        self.show()
        print(f"reproduced deck: {repro}")
        print(f"the actual deck: {master}")
        return False
        
    
    
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

    
if __name__ == "__main__":
    validated = 0
    for game in iter_local():
        if not game.validate_deck():
            print(f"validated {validated} decks")
            break
        validated += 1
        if validated % 10 == 0:
            print(f"validated {validated}")


