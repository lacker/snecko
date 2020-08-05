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
def xobj(cls, subparsers):
    def find_answer(data):
        if type(data) != dict:
            raise ValueError(f"expected dict but got {data}")
        answer = cls()
        for key, subparser in subparsers.items():
            if key not in data:
                raise ValueError(f"expected key {key} but data is {data}")
            value = subparser(data.get(key))
            answer.__setattr__(key, value)
        return answer
    return find_answer

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
                "chose_seed": xbool,
                "is_daily": xbool,
                "is_endless": xbool,
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
    num = 0
    den = 0
    for game in iter_local():
        den += 1
        if game.is_good():
            num += 1
        if den % 1000 == 0:
            print(f"{num}/{den} = {num/den} are good")
    print(f"{num}/{den} = {num/den} are good")

