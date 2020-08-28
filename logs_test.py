#!/usr/bin/env python


import os
import unittest

import logs

DIR = os.path.dirname(__file__)


class TestLogs(unittest.TestCase):
    def test_parsing(self):
        with open(os.path.join(DIR, "test_log.json"), "rb") as f:
            raw = f.read()
            log = logs.GameLog.parse("unused-name", raw)
        self.assertEqual(log.ascension_level, 20)


if __name__ == "__main__":
    unittest.main()
