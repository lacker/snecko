#!/usr/bin/env python

import gym
import spaces

from connection import Connection
from game import Status, MAX_CHOICES, MAX_MONSTERS, NUM_ACTIONS

test_status = Status.load_test_file("state")
STATUS_VECTOR_SIZE = len(Status.vectorizer.vectorize(status))


class SpireEnv(gym.Env):
    metadata = {"render.modes": ["human"]}

    def __init__(self, conn):
        super(SpireEnv, self).__init__()
        self.conn = conn

        self.action_space = spaces.MultiDiscrete(
            [NUM_ACTIONS, MAX_CHOICES, MAX_MONSTERS]
        )
        self.observation_space = spaces.MultiBinary(STATUS_VECTOR_SIZE)

