#!/usr/bin/env python

# The data-gathering phase.
from connection import Connection
from spire_env import SpireEnv


def gather(run_name, seed):
    conn = Connection()
    env = SpireEnv(conn)


if __name__ == "__main__":
    for seed in range(1000):
        pass
