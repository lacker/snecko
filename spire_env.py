#!/usr/bin/env python

import gym
import spaces

from connection import Connection
from game import MAX_CHOICES, MAX_MONSTERS, NUM_ACTIONS


class SpireEnv(gym.Env):
    metadata = {"render.modes": ["human"]}

    def __init__(self, conn):
        super(SpireEnv, self).__init__()
        self.conn = conn

        self.action_space = spaces.MultiDiscrete(
            [NUM_ACTIONS, MAX_CHOICES, MAX_MONSTERS]
        )

