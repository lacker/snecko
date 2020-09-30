#!/usr/bin/env python
# The data-gathering phase.

import os
import random

from connection import Connection

if os.name == "nt":
    RUNLOGDIR = "d:/runlogs"
elif os.name == "posix":
    raise ValueError("mount the runlogs somewhere")
else:
    raise ValueError("please implement RUNLOGDIR for this OS")


def logname(run_id, seed):
    return os.path.join(RUNLOGDIR, f"run{run_id}-{seed}.jlog")


def gather(conn, run_id, seed):
    fname = logname(run_id, seed)
    if os.path.exists(fname):
        print(f"skipping {fname}")
        return
    random.seed(seed)
    status = conn.get_status()
    if status.has_game():
        raise ValueError("gather must be called when there is no active game")
    conn.start_game(seed=seed)
    while conn.get_status().has_game():
        conn.make_random_move()
    f = open(fname, "w")
    for line in conn.log:
        f.write(line + "\n")
    f.close()


if __name__ == "__main__":
    conn = Connection()
    for seed in range(1000):
        gather(conn, 1, seed)
