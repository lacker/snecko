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

        
class GameLog(object):
    def __init__(self, name, bytestring):
        self.name = name
        self.bytestring = bytestring
        string = self.bytestring.decode(encoding="utf-8", errors="replace")
        self.data = json.loads(string)
        if not self.data:
            raise ValueError("game log should not be null")
        if type(self.data) == list:
            raise ValueError("game log should not be a list")

    def ascension(self):
        return self.data.get("ascension_level", 0)

    def is_high_level(self):
        return self.ascension() >= 17

    @staticmethod
    def get_fname(name):
        return os.path.join(CACHE, "local", name)

    @staticmethod
    def load(name):
        fname = GameLog.get_fname(name)
        bs = open(fname).read()
        return GameLog(name, bs)
    
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
                game = GameLog(name, bs)
            except json.decoder.JSONDecodeError:
                # Some of this input data is bad json
                continue
            except ValueError:
                # Used for my own format skips
                continue
            
            yield game
            
# TODO: write iter_local, to loop over the local games
        
def save_high_levels_locally():
    counter = 0
    for game in iter_logs():
        if game.is_high_level():
            game.save()
            counter += 1
            if counter % 100 == 0:
                print(counter, "games saved locally")
    print("done")

    
if __name__ == "__main__":
    pass
