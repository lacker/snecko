#!/usr/bin/env python


import os
import unittest

import brain

DIR = os.path.dirname(__file__)


class TestBrain(unittest.TestCase):
    def test_parsing(self):
        with open(os.path.join(DIR, "test_state.json")) as f:
            raw = f.read()
            status = brain.Status.parse(raw)
        self.assertEqual(len(status.game_state.potions), 3)


if __name__ == "__main__":
    unittest.main()
