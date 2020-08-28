#!/usr/bin/env python

import io
import json
import os
import random
import requests
import sys
import tarfile
import urllib

from cards import CARDS
from relics import RELICS
from xjson import *

ITEMS = CARDS.union(RELICS)

CACHE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cache")
TMP = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tmp")

MONTHS = [
    "2019-02",
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

CHARACTERS = ["IRONCLAD", "THE_SILENT", "DEFECT", "WATCHER"]


def closeness(word, target):
    answer = 0
    for i in range(len(word)):
        chunk = word[i : i + 3]
        if len(chunk) < 3:
            break
        if chunk in target:
            answer += 1
    return answer


def guess_name(item, targets):
    best_guess = "absolutely no idea"
    best_score = 0
    for guess in targets:
        score = closeness(item, guess)
        if score > best_score:
            best_guess = guess
            best_score = score
    return best_guess


def cachefile(name):
    return os.path.join(CACHE, name)


def get_fname(month):
    return os.path.join(CACHE, month + ".tar.gz")


def download_all():
    # Act like we're not a bot
    opener = urllib.request.build_opener()
    opener.addheaders = [("User-agent", "Mozilla/5.0")]
    urllib.request.install_opener(opener)

    for month in MONTHS:
        fname = get_fname(month)
        if os.path.exists(fname):
            continue
        url = f"https://spirelogs.com/archive/{month}.tar.gz"
        print("downloading", url)
        urllib.request.urlretrieve(url, fname)


class BossRelicChoice(object):
    def __init__(self):
        pass


BossRelicChoice.parser = xobj(
    BossRelicChoice, {"not_picked": xlist(xstr), "picked?": xstr}
)


class CardChoice(object):
    def __init__(self):
        pass


CardChoice.parser = xobj(
    CardChoice, {"not_picked": xlist(xstr), "picked": xstr, "floor": xint}
)


class EventChoice(object):
    def __init__(self):
        pass


EventChoice.parser = xobj(
    EventChoice,
    {
        "cards_removed?": xlist(xstr),
        "cards_transformed?": xlist(xstr),
        "cards_obtained?": xlist(xstr),
        "event_name": xstr,
        "player_choice": xstr,
        "floor": xint,
    },
)


class CampfireChoice(object):
    def __init__(self):
        pass


CampfireChoice.parser = xobj(
    CampfireChoice, {"data?": xstr, "floor": xint, "key": xstr}
)


class RelicObtained(object):
    def __init__(self):
        pass


RelicObtained.parser = xobj(RelicObtained, {"floor": xint, "key": xstr})


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
            GameLog.parser = xobj(
                GameLog,
                {
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
                    "relics_obtained": xlist(RelicObtained.parser),
                },
            )

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
            return (
                ["Strike_G"] * 5
                + ["Defend_G"] * 5
                + ["Neutralize", "Survivor", "AscendersBane"]
            )
        elif self.character_chosen == "DEFECT":
            return (
                ["Strike_B"] * 4
                + ["Defend_B"] * 4
                + ["Dualcast", "Zap", "AscendersBane"]
            )
        elif self.character_chosen == "WATCHER":
            return (
                ["Strike_P"] * 4
                + ["Defend_P"] * 4
                + ["Eruption", "Vigilance", "AscendersBane"]
            )
        else:
            raise ValueError(f"character_chosen is {self.character_chosen}")
        return answer

    def simulate(self):
        """
        Yields one tuple for each card/relic choice.
        (current floor, current decklist, current relics, picked-list, not-picked-list).

        This might be more convenient as a "game state" object.
        """
        # The types of action.
        # Upgrades are represented as an addition and removal for the same floor.
        # Order is important.
        ADD_NORMAL_RELIC = 0
        CARD_CHOICE = 1
        ADD_CARD = 2
        REMOVE_CARD = 3
        RELIC_CHOICE = 4
        ADD_BOSS_RELIC = 5

        # actions is a list of floor, type, data tuples.
        # For choices, data is a tuple of lists, (picked, not_picked).
        # Otherwise, data is the card name.

        actions = []
        for choice in self.card_choices:
            if choice.picked == "SKIP":
                picked = []
            else:
                picked = [choice.picked]
            actions.append((choice.floor, CARD_CHOICE, (picked, choice.not_picked)))

            if choice.picked not in ["SKIP", "Singing Bowl"]:
                actions.append((choice.floor, ADD_CARD, choice.picked))

        for choice in self.event_choices:
            if choice.event_name == "Liars Game" and choice.player_choice == "agreed":
                actions.append((choice.floor, ADD_CARD, "Doubt"))
            if choice.cards_removed:
                for card in choice.cards_removed:
                    actions.append((choice.floor, REMOVE_CARD, card))
            if choice.cards_transformed:
                for card in choice.cards_transformed:
                    actions.append((choice.floor, REMOVE_CARD, card))
            if choice.cards_obtained:
                for card in choice.cards_obtained:
                    actions.append((choice.floor, ADD_CARD, card))

        for choice in self.campfire_choices:
            if choice.key == "SMITH":
                actions.append((choice.floor, REMOVE_CARD, choice.data))
                actions.append((choice.floor, ADD_CARD, upgrade(choice.data)))

        for floor, item in zip(self.item_purchase_floors, self.items_purchased):
            if item in CARDS:
                actions.append((floor, ADD_CARD, item))
        for floor, item in zip(self.items_purged_floors, self.items_purged):
            if item in CARDS:
                actions.append((floor, REMOVE_CARD, item))

        # Track the floor for any relic with a known floor
        relicmap = {}
        boss_relics = set()
        for floor, choice in zip([16, 33, 50], self.boss_relics):
            relicmap[choice.picked] = floor
            boss_relics.add(choice.picked)
            if not choice.picked:
                picked = []
            else:
                picked = [choice.picked]
            actions.append((floor, RELIC_CHOICE, (picked, choice.not_picked)))

            if choice.picked == "Calling Bell":
                actions.append((floor, ADD_CARD, "CurseOfTheBell"))

        for obtained in self.relics_obtained:
            relicmap[obtained.key] = obtained.floor

        # Any relic with an unknown floor, we approximate with the floor of the last known relic
        floor = 0
        for relic in self.relics:
            floor = relicmap.get(relic, floor)
            if relic in boss_relics:
                actions.append((floor, ADD_BOSS_RELIC, relic))
            else:
                actions.append((floor, ADD_NORMAL_RELIC, relic))

        deck = self.initial_deck()
        relics = []
        actions.sort()
        for floor, action_type, data in actions:
            if action_type in [ADD_NORMAL_RELIC, ADD_BOSS_RELIC]:
                if data not in RELICS:
                    # Probably modded
                    return
                relics.append(data)
            elif action_type in [CARD_CHOICE, RELIC_CHOICE]:
                picked, not_picked = data
                yield floor, deck, relics, picked, not_picked
            elif action_type == REMOVE_CARD:
                if data not in deck:
                    continue
                if data not in CARDS:
                    raise ValueError(f"cannot remove bad card: {data}")
                deck.remove(data)
            elif action_type == ADD_CARD:
                if data not in CARDS:
                    # Probably modded
                    return
                deck.append(data)
            else:
                raise ValueError(f"unknown action_type: {action_type}")


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


def iter_wins():
    """It counts as a win if you beat the regular boss. Heart not required"""
    for game in iter_local():
        if game.floor_reached > 50:
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


def csv_header(cards, relics):
    return "Character,Floor,Deck Size,Choice1,Choice2,Choice3,Picked," + ",".join(
        cards + relics
    )


def validate_names(names, targets):
    for name in names:
        if name not in targets:
            guess = guess_name(name, targets)
            raise ValueError(f'bad name: {name}. Did you mean "{guess}"?')


def mini_csv(character, floor, deck, relics, choices):
    """
    Returns a fake csv file with one row
    """
    validate_names(deck, CARDS)
    validate_names(relics, RELICS)
    validate_names(choices, ITEMS)

    all_cards = sorted(list(CARDS))
    all_relics = sorted(list(RELICS))
    header = csv_header(all_cards, all_relics)
    deck_entries = [str(deck.count(card)) for card in all_cards]
    relic_entries = [str(relics.count(relic)) for relic in all_relics]
    line = (
        [character, str(floor), str(len(deck))]
        + choices
        + ["skip"]
        + deck_entries
        + relic_entries
    )
    return io.StringIO(header + "\n" + ",".join(line) + "\n")


def generate_csv(character=None, file=sys.stdout):
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
    One column per card, with counts
    One column per relic, with counts
    """
    all_cards = sorted(list(CARDS))
    all_relics = sorted(list(RELICS))
    header = csv_header(all_cards, all_relics)
    num_commas = header.count(",")
    print(header, file=file)
    games = 0
    for game in iter_wins():
        if character and game.character_chosen != character:
            continue
        if not game.is_good():
            continue
        for floor, deck, relics, picked, not_picked in game.simulate():
            choices = picked + not_picked
            if len(choices) != 3:
                continue
            random.shuffle(choices)
            if picked and picked[0] in choices:
                picked_value = str(choices.index(picked[0]) + 1)
            else:
                picked_value = "skip"
            deck_entries = [str(deck.count(card)) for card in all_cards]
            relic_entries = [str(relics.count(relic)) for relic in all_relics]
            row = (
                [game.character_chosen, str(floor), str(len(deck))]
                + choices
                + [picked_value]
                + deck_entries
                + relic_entries
            )
            line = ",".join(row)
            if line.count(",") != num_commas:
                raise ValueError(f"bad line: {line}")
            print(line, file=file)
        games += 1
        if games % 1000 == 0:
            print(f"processed {games} games", file=sys.stderr)


def character_filename(char):
    return os.path.join(TMP, char.lower() + ".csv")


def generate_csvs(chars=CHARACTERS):
    for char in chars:
        fname = character_filename(char)
        f = open(fname, "w")
        print(f"aggregating data for {fname}")
        generate_csv(character=char, file=f)


def generate_combined():
    fname = character_filename("combined")
    f = open(fname, "w")
    print(f"aggregating data for all characters")
    generate_csv(character=None, file=f)


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


def count_relics():
    """
    Useful for printing out the least frequent relics, so we can clean up the data.
    """
    count = {}
    for game in iter_local():
        if not game.is_good():
            continue
        for relic in game.relics:
            count[relic] = count.get(relic, 0) + 1

    counts = [(value, key) for key, value in count.items()]
    counts.sort()
    for count in counts:
        print(count)


def show_json(n):
    count = 0
    for game in iter_wins():
        count += 1
        if count >= n:
            game.show()
            break


if __name__ == "__main__":
    generate_csvs()
