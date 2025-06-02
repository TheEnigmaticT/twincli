# twincli/utils/config_loader.py
import json
from pathlib import Path

def load_key_facts() -> dict:
    """
    Loads key facts and configurations from the key_facts.json file.
    """
    config_dir = Path(__file__).parent.parent / "config"
    key_facts_path = config_dir / "key_facts.json"

    if not key_facts_path.exists():
        # Create default config directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)
        # Create a default key_facts.json if it doesn't exist
        default_content = {
            "kanban_aliases": {},
            "general_preferences": {},
            "tool_settings": {},
            "general_memory": {}
        }
        with open(key_facts_path, 'w') as f:
            json.dump(default_content, f, indent=4)
        return default_content

    try:
        with open(key_facts_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Error decoding JSON from {key_facts_path}. Returning empty config.")
        return {}
    except Exception as e:
        print(f"Warning: Could not load key facts from {key_facts_path}: {e}. Returning empty config.")
        return {}

def save_key_facts(data: dict):
    """
    Saves key facts and configurations to the key_facts.json file.
    """
    config_dir = Path(__file__).parent.parent / "config"
    key_facts_path = config_dir / "key_facts.json"
    
    config_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists
    
    try:
        with open(key_facts_path, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving key facts to {key_facts_path}: {e}")
