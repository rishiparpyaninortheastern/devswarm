import os

from devswarm.shared.persistence import SQLiteStore


def store() -> SQLiteStore:
    return SQLiteStore(os.environ.get("DEVSWARM_DB", ".data/devswarm.db"))
