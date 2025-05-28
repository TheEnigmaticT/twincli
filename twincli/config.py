import json
import os
from pathlib import Path

def get_config_path():
    """Get the path to the config file."""
    return Path.home() / ".twincli" / "config.json"

def load_config():
    """Load configuration from the config file."""
    config_path = get_config_path()
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r') as f:
        return json.load(f)

def save_config(gemini_key, serper_key):
    """Save configuration to the config file."""
    config_path = get_config_path()
    config_path.parent.mkdir(exist_ok=True)
    
    config = {
        "api_key": gemini_key,
        "serper_api_key": serper_key
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)