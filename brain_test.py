#!/usr/bin/env python

import os
import unittest

import mod

DIR = os.path.dirname(__file__)


class TestGameState(unittest.TestCase):
    def test_parsing(self):
        f = open(os.path.join(DIR, "test_state.json"))
        raw = f.read()
        f.close()
        status = mod.Status.parse(raw)
        self.assertEqual(len(status.game_state.potions), 3)


if __name__ == "__main__":
    unittest.main()
