#!/usr/bin/env python

from datetime import timedelta
import gym
from gym import spaces
import numpy as np
import random
import time

from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3 import PPO
from stable_baselines3.ppo import MlpPolicy

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

        self.total_games = 0
        self.total_floors = 0

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
            # This action is invalid. Usually do nothing
            if random.random() > 0.05:
                command = None
            else:
                # But we don't want to get stuck so sometimes move randomly
                commands = status.get_commands()
                command = random.choice(commands)

        pre_score = status.score()
        pre_floor = status.floor()
        if command:
            status = self.conn.issue_command(command)
        post_score = status.score()
        post_floor = status.floor()
        reward = post_score - pre_score

        if post_floor > pre_floor:
            self.total_floors += 1
        if status.has_game():
            done = False
        else:
            self.total_games += 1
            done = True

        return (self.observe(), reward, done, {})

    def render(self, mode="human"):
        if mode != "human":
            raise NotImplementedError
        self.conn.show()


class TensorboardCallback(BaseCallback):
    def __init__(self, env):
        verbose = 0
        super(TensorboardCallback, self).__init__(verbose)
        self.env = env

    def _on_step(self):
        status = self.env.conn.get_status()
        if status.is_death():
            self.logger.record("max_floor", status.floor())
        return True


def train():
    conn = Connection()
    env = Monitor(SpireEnv(conn), "./tmp/")
    model_name = "ppo_default"
    logdir = "./tboard_log"
    try:
        model = PPO.load(model_name, env=env, tensorboard_log=logdir)
    except FileNotFoundError:
        model = PPO(MlpPolicy, env, verbose=1, tensorboard_log=logdir)
    start = time.time()
    steps = 10000
    callback = TensorboardCallback(env)
    model.learn(total_timesteps=steps, reset_num_timesteps=False, callback=callback)
    model.save("ppo_default")

    elapsed = time.time() - start
    print(f"{steps} steps processed")
    print(f"{timedelta(seconds=elapsed)} time elapsed")
    print(f"{env.total_floors} floors climbed")
    print(f"{env.total_games} games played")
    print("{:.2f} floors per game".format(env.total_floors / env.total_games))


if __name__ == "__main__":
    train()
