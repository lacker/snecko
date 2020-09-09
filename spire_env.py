#!/usr/bin/env python

import gym
from gym import spaces
import numpy as np
import random
from stable_baselines3.common.env_checker import check_env

from connection import Connection
from game import Status, MAX_CHOICES, MAX_MONSTERS, NUM_ACTIONS

test_status = Status.load_test_file("state")
STATUS_VECTOR_SIZE = len(Status.vectorizer.vectorize(test_status))


class SpireEnv(gym.Env):
    metadata = {"render.modes": ["human"]}

    def __init__(self, conn):
        super(SpireEnv, self).__init__()
        self.conn = conn

        self.action_space = spaces.MultiDiscrete(
            [NUM_ACTIONS, MAX_CHOICES, MAX_MONSTERS]
        )
        self.observation_space = spaces.MultiBinary(STATUS_VECTOR_SIZE)

    def observe(self):
        status = self.conn.get_status()
        vector = Status.vectorizer.vectorize(status)
        return np.array(vector)

    def reset(self):
        """
        This usually does not actually reset the game state.
        If there is a game in progress, this lets the game stay as it is. 
        If there is no game in progress, this does start a new one.
        """
        status = self.conn.get_status()
        if not status.has_game():
            self.conn.start_game()
        return self.observe()

    def step(self, multi_action):
        action, index1, index2 = multi_action
        status = self.conn.get_status()
        if not status.has_commands():
            # The game is over.
            return (self.observe(), 0, True, {})

        try:
            command = status.make_command(action, index1, index2)
        except ValueError:
            # This action is invalid. Move randomly
            commands = status.get_commands()
            command = random.choice(commands)

        pre_floor = status.floor()
        status = self.conn.issue_command(command)
        post_floor = status.floor()
        if post_floor > pre_floor:
            reward = 1
        else:
            reward = 0
        if status.has_game():
            done = False
        else:
            done = True

        return (self.observe(), reward, done, {})

    def render(self, mode="human"):
        if mode != "human":
            raise NotImplementedError
        self.conn.show()


if __name__ == "__main__":
    conn = Connection()
    env = SpireEnv(conn)
    check_env(env)
