#!/usr/bin/env python

import os
import unittest

import brain

DIR = os.path.dirname(__file__)


def test_parsing():
    with open(os.path.join(DIR, "test_state.json")) as f:
        raw = f.read()
    status = brain.Status.parse(raw)
    assert len(status.game_state.potions) == 3
