#!/usr/bin/env python

from datetime import timedelta
import gym
from gym import spaces
import numpy as np
import os
import random
import time

from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3 import PPO
from stable_baselines3.ppo import MlpPolicy

from connection import Connection
from game import Status, MAX_ACTIONS

test_status = Status.load_test_file("state")
STATUS_VECTOR_SIZE = len(Status.vectorizer.vectorize(test_status))

LOG = open(os.path.expanduser("~/env.log"), "a+")


def log(message):
    LOG.write(message + "\n")


class SpireEnv(gym.Env):
    metadata = {"render.modes": ["human"]}

    def __init__(self, conn):
        super(SpireEnv, self).__init__()
        self.conn = conn

        self.action_space = spaces.Discrete(MAX_ACTIONS)
        self.observation_space = spaces.MultiBinary(STATUS_VECTOR_SIZE)

        self.total_games = 0
        self.total_floors = 0
        self.max_floors = []

    def observe(self):
        status = self.conn.get_status()
        vector = Status.vectorizer.vectorize(status)
        return np.array(vector)

    def reset(self, seed=None):
        """
        This usually does not actually reset the game state.
        If there is a game in progress, this lets the game stay as it is. 
        If there is no game in progress, this does start a new one.
        """
        status = self.conn.get_status()
        if not status.has_game():
            self.conn.start_game(seed=seed)
        if seed is not None:
            raise ValueError("expected to start a new game")
        return self.observe()

    def step(self, action):
        status = self.conn.get_status()
        if not status.has_commands():
            # The game is over.
            return (self.observe(), 0, True, {})

        try:
            command = status.make_command(action)
        except ValueError:
            # This action is invalid. Usually do nothing
            if random.random() > 0.05:
                command = None
            else:
                # But we don't want to get stuck so sometimes move randomly
                commands = status.get_commands()
                command = random.choice(commands)

        pre_hp = status.hit_points()
        pre_floor = status.floor()
        if command:
            status = self.conn.issue_command(command)
        post_hp = status.hit_points()
        post_floor = status.floor()

        reward = post_hp - pre_hp

        if post_floor > pre_floor:
            # print(f"from floor {pre_floor} -> {post_floor}")
            reward += 10 * (post_floor - pre_floor)
            self.total_floors += 1

        if status.has_game():
            done = False
        else:
            # print("dead")
            self.total_games += 1
            done = True

        if status.is_death():
            log(f"seed {status.seed()} got to floor {status.floor()}")
            self.max_floors.append(status.floor())
            if len(self.max_floors) > 30:
                self.max_floors.pop(0)

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
        fs = self.env.max_floors
        if fs:
            max_floor = sum(fs) / len(fs)
            self.logger.record("max_floor", max_floor)
        return True

MODEL_NAME = "ppo_default"

def train(hours):
    conn = Connection()
    env = Monitor(SpireEnv(conn), "./tmp/")
    env.reset()
    logdir = "./tboard_log"
    try:
        model = PPO.load(MODEL_NAME), env=env, tensorboard_log=logdir)
    except FileNotFoundError:
        model = PPO(MlpPolicy, env, verbose=1, tensorboard_log=logdir)
    start = time.time()

    steps_per_hour = 50000
    steps = steps_per_hour * hours

    callback = TensorboardCallback(env)
    model.learn(total_timesteps=steps, reset_num_timesteps=False, callback=callback)
    model.save(MODEL_NAME)

    elapsed = time.time() - start
    print(f"{steps} steps processed")
    print(f"{timedelta(seconds=elapsed)} time elapsed")
    print(f"{env.total_floors} floors climbed")
    print(f"{env.total_games} games played")
    print("{:.2f} floors per game".format(env.total_floors / env.total_games))

def evaluate(seed):
    conn = Connection()
    env = SpireEnv(conn)
    obs = env.reset(seed=seed)
    model = PPO.load(MODEL_NAME, env=env)
    while True:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action)
        if env.status.is_death():
            print(f"on seed {seed} we got to floor {env.status.floor()}")
        if done:
            break

if __name__ == "__main__":
    for _ in range(4):
        train(1)
