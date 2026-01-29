"""Configuration and path management for Mnemonic."""

import os
from pathlib import Path
from typing import Optional


def get_data_dir() -> Path:
    """
    Get the data directory for Mnemonic storage.

    Priority:
    1. MNEMONIC_DATA_DIR environment variable
    2. ~/.mnemonic/
    """
    env_dir = os.environ.get("MNEMONIC_DATA_DIR")
    if env_dir:
        data_dir = Path(env_dir)
    else:
        data_dir = Path.home() / ".mnemonic"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    """Get the SQLite database path."""
    return get_data_dir() / "memories.db"


def get_license_key() -> Optional[str]:
    """Get the premium license key if set."""
    return os.environ.get("MNEMONIC_LICENSE_KEY")


# Constants
DEFAULT_WEIGHT = 0.8
MIN_WEIGHT = 0.1
MAX_WEIGHT = 1.0
DECAY_RATE = 0.99  # Weight multiplier per day without access
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
