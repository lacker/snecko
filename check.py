#!/usr/bin/env python

from connection import Connection
from spire_env import SpireEnv
from stable_baselines3.common.env_checker import check_env

if __name__ == "__main__":
    conn = Connection()
    env = SpireEnv(conn)
    check_env(env)
