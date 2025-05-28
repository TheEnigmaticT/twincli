import os
import json

CONFIG_PATH = os.path.expanduser("~/.twincli/config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError("Config file not found. Run `twincli config` to set it up.")
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(api_key, serper_key):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({
            "api_key": api_key,
            "serper_api_key": serper_key
        }, f)
