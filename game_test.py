#!/usr/bin/env python


import os
import unittest

from game import *

DIR = os.path.dirname(__file__)


class TestBrain(unittest.TestCase):
    def test_parsing(self):
        with open(os.path.join(DIR, "test_state.json")) as f:
            raw = f.read()
            status = Status.parse(raw)
        self.assertEqual(len(status.game_state.potions), 3)

    def test_vectorizing(self):
        size = len(Status.vectorizer)

        # Status.vectorizer.debug_size()

        for name in ["deadguy", "midcombat", "neow", "state"]:
            status = Status.load_test_file(name)
            vector = Status.vectorizer.vectorize(status)
            self.assertEqual(len(vector), size, f"size check for {name}")
            self.assertEqual(min(vector), 0, f"min check for {name}")
            self.assertEqual(max(vector), 1, f"max check for {name}")


if __name__ == "__main__":
    unittest.main()
