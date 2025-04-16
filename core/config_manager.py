# app/core/config_manager.py

import json
import os
from typing import Any

# Directory where all config files reside.
# Adjust if you prefer a different structure.
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")

def load_json_config(filename: str) -> Any:
    """
    Loads a JSON file from the config directory.
    Returns the parsed JSON data (dict or list).
    If the file does not exist or is invalid, returns an empty dict by default.
    """
    filepath = os.path.join(CONFIG_DIR, filename)
    if not os.path.isfile(filepath):
        return {}  # or return [] if you expect arrays
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, IOError):
        return {}  # fallback if file is corrupted or unreadable

def save_json_config(filename: str, data: Any) -> None:
    """
    Writes data as JSON to the specified config file.
    Overwrites any existing content.
    """
    filepath = os.path.join(CONFIG_DIR, filename)
    # Ensure the config directory exists
    os.makedirs(CONFIG_DIR, exist_ok=True)

    # Write data in a pretty JSON format
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
