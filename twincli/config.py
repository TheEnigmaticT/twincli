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

def save_config(gemini_key=None, serper_key=None, obsidian_vault=None):
    """Save configuration to the config file."""
    config_path = get_config_path()
    config_path.parent.mkdir(exist_ok=True)
    
    # Load existing config first
    existing_config = load_config()
    
    # Only update keys that aren't empty/None
    if gemini_key and gemini_key.strip():
        existing_config["api_key"] = gemini_key.strip()
    if serper_key and serper_key.strip():
        existing_config["serper_api_key"] = serper_key.strip()
    if obsidian_vault and obsidian_vault.strip():
        # Expand ~ to home directory
        vault_path = Path(obsidian_vault.strip()).expanduser()
        existing_config["obsidian_vault_path"] = str(vault_path)
    
    with open(config_path, 'w') as f:
        json.dump(existing_config, f, indent=2)

def validate_obsidian_path(path_str: str) -> tuple[bool, str]:
    """Validate that the Obsidian vault path exists and contains .md files.
    
    Returns:
        (is_valid, message)
    """
    if not path_str:
        return False, "Path cannot be empty"
    
    try:
        path = Path(path_str).expanduser().resolve()
        
        if not path.exists():
            return False, f"Path does not exist: {path}"
        
        if not path.is_dir():
            return False, f"Path is not a directory: {path}"
        
        # Check if it looks like an Obsidian vault (contains .md files)
        md_files = list(path.rglob("*.md"))
        if not md_files:
            return False, f"No markdown files found in: {path}\nThis doesn't appear to be an Obsidian vault."
        
        return True, f"Valid Obsidian vault with {len(md_files)} markdown files"
        
    except Exception as e:
        return False, f"Error validating path: {e}"