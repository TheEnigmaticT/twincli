
import os
import re
from pathlib import Path
from typing import List, Dict

def read_obsidian_note(note_title: str, vault_path: str = None) -> str:
    """Read the full content of a specific Obsidian note.
    
    Args:
        note_title: The title/name of the note to read. Can include folder path like "Folder/Subfolder/Note Title"
        vault_path: Path to Obsidian vault (if None, will try to detect)
        
    Returns:
        String containing the full note content
    """
    # Try to find vault path if not provided
    if vault_path is None:
        vault_path = _find_obsidian_vault()
        if not vault_path:
            return "No Obsidian vault path configured. Please specify vault_path or set OBSIDIAN_VAULT_PATH environment variable."
    
    vault_path = Path(vault_path)
    if not vault_path.exists():
        return f"Obsidian vault not found at: {vault_path}"
    
    # Debug: Show what we're looking for
    print(f"[DEBUG] Looking for note: '{note_title}' in vault: {vault_path}")
    
    # Clean the note title and handle different formats
    note_title_clean = note_title.strip()
    
    # Handle different input formats:
    # 1. "Note Title" -> look for "Note Title.md"
    # 2. "Folder/Note Title" -> look for "Folder/Note Title.md"
    # 3. "Note Title.md" -> look for "Note Title.md"
    
    # Remove .md extension if present for consistent handling
    if note_title_clean.endswith('.md'):
        note_title_clean = note_title_clean[:-3]
    
    # Try multiple search strategies
    search_strategies = [
        # Strategy 1: Exact path match (if note_title includes folder structure)
        lambda: _search_exact_path(vault_path, note_title_clean),
        # Strategy 2: Case-insensitive exact match
        lambda: _search_case_insensitive(vault_path, note_title_clean),
        # Strategy 3: Filename-only search (ignore folder structure)
        lambda: _search_filename_only(vault_path, note_title_clean),
        # Strategy 4: Partial match search
        lambda: _search_partial_match(vault_path, note_title_clean),
    ]
    
    for strategy in search_strategies:
        result = strategy()
        if result:
            md_file, match_type = result
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                rel_path = md_file.relative_to(vault_path)
                return f"**Note: {md_file.stem}** ({match_type})\nPath: {rel_path}\nVault: {vault_path}\n\n{content}"
                
            except Exception as e:
                return f"Error reading note '{md_file.name}': {e}"
    
    # If no strategies worked, provide detailed debugging info
    return _generate_debug_info(vault_path, note_title_clean)

def _search_exact_path(vault_path: Path, note_title: str) -> tuple:
    """Search for exact path match."""
    # If note_title contains slashes, treat it as a relative path
    if '/' in note_title or '\\' in note_title:
        # Normalize path separators
        note_path = note_title.replace('\\', '/')
        full_path = vault_path / f"{note_path}.md"
        
        print(f"[DEBUG] Trying exact path: {full_path}")
        if full_path.exists():
            return (full_path, "exact path match")
    
    return None

def _search_case_insensitive(vault_path: Path, note_title: str) -> tuple:
    """Search for case-insensitive match."""
    note_title_lower = note_title.lower()
    
    for md_file in vault_path.rglob("*.md"):
        # Skip hidden files and folders
        if any(part.startswith('.') for part in md_file.parts):
            continue
        
        # Get the relative path from vault root (without .md extension)
        rel_path = md_file.relative_to(vault_path)
        rel_path_no_ext = str(rel_path)[:-3] if str(rel_path).endswith('.md') else str(rel_path)
        
        # Check if it matches (case-insensitive)
        if rel_path_no_ext.lower() == note_title_lower:
            print(f"[DEBUG] Found case-insensitive match: {md_file}")
            return (md_file, "case-insensitive match")
    
    return None

def _search_filename_only(vault_path: Path, note_title: str) -> tuple:
    """Search by filename only, ignoring folder structure."""
    # Extract just the filename if note_title includes path
    if '/' in note_title:
        filename_only = note_title.split('/')[-1]
    elif '\\' in note_title:
        filename_only = note_title.split('\\')[-1]
    else:
        filename_only = note_title
    
    filename_lower = filename_only.lower()
    
    for md_file in vault_path.rglob("*.md"):
        # Skip hidden files and folders
        if any(part.startswith('.') for part in md_file.parts):
            continue
        
        # Check if filename matches (case-insensitive)
        if md_file.stem.lower() == filename_lower:
            print(f"[DEBUG] Found filename match: {md_file}")
            return (md_file, "filename match")
    
    return None

def _search_partial_match(vault_path: Path, note_title: str) -> tuple:
    """Search for partial matches."""
    note_title_lower = note_title.lower()
    partial_matches = []
    
    for md_file in vault_path.rglob("*.md"):
        # Skip hidden files and folders
        if any(part.startswith('.') for part in md_file.parts):
            continue
        
        # Check filename for partial match
        if note_title_lower in md_file.stem.lower():
            partial_matches.append(md_file)
        
        # Also check the full relative path
        rel_path = md_file.relative_to(vault_path)
        rel_path_str = str(rel_path)[:-3] if str(rel_path).endswith('.md') else str(rel_path)
        if note_title_lower in rel_path_str.lower():
            partial_matches.append(md_file)
    
    # Remove duplicates
    partial_matches = list(set(partial_matches))
    
    if len(partial_matches) == 1:
        print(f"[DEBUG] Found single partial match: {partial_matches[0]}")
        return (partial_matches[0], "partial match")
    elif len(partial_matches) > 1:
        print(f"[DEBUG] Found multiple partial matches: {[str(f) for f in partial_matches]}")
        # Return the first one, but this could be improved with better ranking
        return (partial_matches[0], f"partial match (1 of {len(partial_matches)})")
    
    return None

def _generate_debug_info(vault_path: Path, note_title: str) -> str:
    """Generate detailed debugging information when note is not found."""
    debug_info = [f"No note found with title '{note_title}' in Obsidian vault: {vault_path}"]
    
    # List all markdown files in the vault for debugging
    debug_info.append("\nDebugging Information:")
    debug_info.append(f"Vault path exists: {vault_path.exists()}")
    debug_info.append(f"Vault path is directory: {vault_path.is_dir()}")
    
    # Find all .md files
    md_files = list(vault_path.rglob("*.md"))
    debug_info.append(f"Total .md files found: {len(md_files)}")
    
    if md_files:
        debug_info.append("\nFirst 10 markdown files found:")
        for i, md_file in enumerate(md_files[:10]):
            rel_path = md_file.relative_to(vault_path)
            debug_info.append(f"  {i+1}. {rel_path}")
        
        if len(md_files) > 10:
            debug_info.append(f"  ... and {len(md_files) - 10} more files")
    
    # Check if the specific folder structure exists
    if '/' in note_title:
        folder_parts = note_title.split('/')[:-1]  # All but the last part
        folder_path = vault_path
        debug_info.append(f"\nChecking folder structure for: {note_title}")
        
        for part in folder_parts:
            folder_path = folder_path / part
            debug_info.append(f"  {folder_path}: exists={folder_path.exists()}")
    
    return "\n".join(debug_info)

def _find_obsidian_vault() -> str:
    """Try to find Obsidian vault path automatically."""
    # Check TwinCLI config first
    try:
        from twincli.config import load_config
        config = load_config()
        config_path = config.get('obsidian_vault_path')
        if config_path and Path(config_path).exists():
            return config_path
    except:
        pass
    
    # Check environment variable
    env_path = os.getenv('OBSIDIAN_VAULT_PATH')
    if env_path and Path(env_path).exists():
        return env_path
    
    # Common locations to check
    home = Path.home()
    common_paths = [
        home / "Documents" / "CrowdTamers Obsidian Vault",  # Based on your specific case
        home / "Obsidian",
        home / "Documents" / "Obsidian",
        home / "obsidian-vault",
        home / "vault",
        home / "notes",
    ]
    
    for path in common_paths:
        if path.exists() and any(path.glob("*.md")):
            return str(path)
    
    return None

# Keep all the other functions from the original obsidian.py file...
def search_obsidian(query: str, vault_path: str = None) -> str:
    """Search through Obsidian vault for notes containing the query."""
    # [Keep the original implementation]
    pass

def create_obsidian_note(title: str, content: str, vault_path: str = None, folder: str = None) -> str:
    """Create a new note in Obsidian vault."""
    # [Keep the original implementation] 
    pass

def update_obsidian_note(title: str, content: str, append: bool = False) -> str:
    """Update an existing note or append to it."""
    # Implementation for updating notes
    pass

def create_daily_note(content: str = None) -> str:
    """Create today's daily note with optional content."""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    if content is None:
        content = f"# {today}\n\n## Tasks\n- \n\n## Notes\n\n"
    
    return create_obsidian_note(today, content, folder="Daily Notes")

def list_recent_notes(vault_path: str = None, limit: int = 10) -> str:
    """List recently modified notes in Obsidian vault.
    
    Args:
        vault_path: Path to Obsidian vault
        limit: Number of recent notes to show
        
    Returns:
        String with list of recent notes
    """
    if vault_path is None:
        vault_path = _find_obsidian_vault()
        if not vault_path:
            return "No Obsidian vault path configured."
    
    vault_path = Path(vault_path)
    if not vault_path.exists():
        return f"Obsidian vault not found at: {vault_path}"
    
    # Get all markdown files with modification times
    md_files = []
    for md_file in vault_path.rglob("*.md"):
        if any(part.startswith('.') for part in md_file.parts):
            continue
        try:
            mtime = md_file.stat().st_mtime
            md_files.append((md_file, mtime))
        except:
            continue
    
    # Sort by modification time (newest first)
    md_files.sort(key=lambda x: x[1], reverse=True)
    
    if not md_files:
        return "No markdown files found in vault."
    
    result_parts = [f"Recently modified notes (top {limit}):\n"]
    
    for i, (md_file, mtime) in enumerate(md_files[:limit]):
        rel_path = md_file.relative_to(vault_path)
        title = md_file.stem
        
        # Format modification time
        import datetime
        mod_date = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        
        result_parts.append(f"{i+1}. **{title}**\n   Path: {rel_path}\n   Modified: {mod_date}\n")
    
    return "\n".join(result_parts)