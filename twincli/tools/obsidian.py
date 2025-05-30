import os
import re
from pathlib import Path
from typing import List, Dict
from datetime import datetime

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

def search_obsidian(query: str, vault_path: str = None) -> str:
    """Search through Obsidian vault for notes containing the query."""
    if vault_path is None:
        vault_path = _find_obsidian_vault()
        if not vault_path:
            return "No Obsidian vault path configured. Please specify vault_path or set OBSIDIAN_VAULT_PATH environment variable."
    
    vault_path = Path(vault_path)
    if not vault_path.exists():
        return f"Obsidian vault not found at: {vault_path}"
    
    print(f"[DEBUG] Searching for '{query}' in vault: {vault_path}")
    
    matches = []
    query_lower = query.lower()
    
    # Search through all markdown files
    for md_file in vault_path.rglob("*.md"):
        # Skip hidden files and folders
        if any(part.startswith('.') for part in md_file.parts):
            continue
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if query matches in title (filename) or content
            filename_match = query_lower in md_file.stem.lower()
            content_match = query_lower in content.lower()
            
            if filename_match or content_match:
                rel_path = md_file.relative_to(vault_path)
                
                # Create a snippet showing context around matches
                snippet = ""
                if content_match:
                    # Find first occurrence in content
                    content_lower = content.lower()
                    match_pos = content_lower.find(query_lower)
                    if match_pos != -1:
                        # Get context around the match (100 chars before/after)
                        start = max(0, match_pos - 100)
                        end = min(len(content), match_pos + len(query) + 100)
                        snippet = content[start:end].replace('\n', ' ').strip()
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(content):
                            snippet = snippet + "..."
                
                match_info = {
                    'file': str(rel_path),
                    'title': md_file.stem,
                    'filename_match': filename_match,
                    'content_match': content_match,
                    'snippet': snippet
                }
                matches.append(match_info)
                
        except Exception as e:
            print(f"[DEBUG] Error reading {md_file}: {e}")
            continue
    
    if not matches:
        return f"No notes found containing '{query}' in vault: {vault_path}"
    
    # Format results
    result_parts = [f"Found {len(matches)} notes containing '{query}':\n"]
    
    for i, match in enumerate(matches[:10], 1):  # Limit to first 10 results
        result_parts.append(f"{i}. **{match['title']}**")
        result_parts.append(f"   Path: {match['file']}")
        
        match_types = []
        if match['filename_match']:
            match_types.append("title")
        if match['content_match']:
            match_types.append("content")
        result_parts.append(f"   Match in: {', '.join(match_types)}")
        
        if match['snippet']:
            result_parts.append(f"   Context: {match['snippet']}")
        
        result_parts.append("")  # Empty line between results
    
    if len(matches) > 10:
        result_parts.append(f"... and {len(matches) - 10} more matches")
    
    return "\n".join(result_parts)

def read_obsidian_note(note_title: str, vault_path: str = None) -> str:
    """Read the full content of a specific Obsidian note.
    
    Args:
        note_title: The title/name of the note to read. Can include folder path like "Folder/Subfolder/Note Title"
        vault_path: Path to Obsidian vault (if None, will try to detect)
        
    Returns:
        String containing the full note content
    """
    if vault_path is None:
        vault_path = _find_obsidian_vault()
        if not vault_path:
            return "No Obsidian vault path configured. Please specify vault_path or set OBSIDIAN_VAULT_PATH environment variable."
    
    vault_path = Path(vault_path)
    if not vault_path.exists():
        return f"Obsidian vault not found at: {vault_path}"
    
    print(f"[DEBUG] Looking for note: '{note_title}' in vault: {vault_path}")
    
    # Clean the note title and handle different formats
    note_title_clean = note_title.strip()
    
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
    if '/' in note_title or '\\' in note_title:
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
        if any(part.startswith('.') for part in md_file.parts):
            continue
        
        rel_path = md_file.relative_to(vault_path)
        rel_path_no_ext = str(rel_path)[:-3] if str(rel_path).endswith('.md') else str(rel_path)
        
        if rel_path_no_ext.lower() == note_title_lower:
            print(f"[DEBUG] Found case-insensitive match: {md_file}")
            return (md_file, "case-insensitive match")
    
    return None

def _search_filename_only(vault_path: Path, note_title: str) -> tuple:
    """Search by filename only, ignoring folder structure."""
    if '/' in note_title:
        filename_only = note_title.split('/')[-1]
    elif '\\' in note_title:
        filename_only = note_title.split('\\')[-1]
    else:
        filename_only = note_title
    
    filename_lower = filename_only.lower()
    
    for md_file in vault_path.rglob("*.md"):
        if any(part.startswith('.') for part in md_file.parts):
            continue
        
        if md_file.stem.lower() == filename_lower:
            print(f"[DEBUG] Found filename match: {md_file}")
            return (md_file, "filename match")
    
    return None

def _search_partial_match(vault_path: Path, note_title: str) -> tuple:
    """Search for partial matches."""
    note_title_lower = note_title.lower()
    partial_matches = []
    
    for md_file in vault_path.rglob("*.md"):
        if any(part.startswith('.') for part in md_file.parts):
            continue
        
        if note_title_lower in md_file.stem.lower():
            partial_matches.append(md_file)
        
        rel_path = md_file.relative_to(vault_path)
        rel_path_str = str(rel_path)[:-3] if str(rel_path).endswith('.md') else str(rel_path)
        if note_title_lower in rel_path_str.lower():
            partial_matches.append(md_file)
    
    partial_matches = list(set(partial_matches))
    
    if len(partial_matches) == 1:
        print(f"[DEBUG] Found single partial match: {partial_matches[0]}")
        return (partial_matches[0], "partial match")
    elif len(partial_matches) > 1:
        print(f"[DEBUG] Found multiple partial matches: {[str(f) for f in partial_matches]}")
        return (partial_matches[0], f"partial match (1 of {len(partial_matches)})")
    
    return None

def _generate_debug_info(vault_path: Path, note_title: str) -> str:
    """Generate detailed debugging information when note is not found."""
    debug_info = [f"No note found with title '{note_title}' in Obsidian vault: {vault_path}"]
    
    debug_info.append("\nDebugging Information:")
    debug_info.append(f"Vault path exists: {vault_path.exists()}")
    debug_info.append(f"Vault path is directory: {vault_path.is_dir()}")
    
    md_files = list(vault_path.rglob("*.md"))
    debug_info.append(f"Total .md files found: {len(md_files)}")
    
    if md_files:
        debug_info.append("\nFirst 10 markdown files found:")
        for i, md_file in enumerate(md_files[:10]):
            rel_path = md_file.relative_to(vault_path)
            debug_info.append(f"  {i+1}. {rel_path}")
        
        if len(md_files) > 10:
            debug_info.append(f"  ... and {len(md_files) - 10} more files")
    
    if '/' in note_title:
        folder_parts = note_title.split('/')[:-1]
        folder_path = vault_path
        debug_info.append(f"\nChecking folder structure for: {note_title}")
        
        for part in folder_parts:
            folder_path = folder_path / part
            debug_info.append(f"  {folder_path}: exists={folder_path.exists()}")
    
    return "\n".join(debug_info)

def create_obsidian_note(title: str, content: str, vault_path: str = None, folder: str = None) -> str:
    """Create a new note in Obsidian vault."""
    if vault_path is None:
        vault_path = _find_obsidian_vault()
        if not vault_path:
            return "No Obsidian vault path configured."
    
    vault_path = Path(vault_path)
    if not vault_path.exists():
        return f"Obsidian vault not found at: {vault_path}"
    
    # Determine the full path for the new note
    if folder:
        note_folder = vault_path / folder
        note_folder.mkdir(parents=True, exist_ok=True)
        note_path = note_folder / f"{title}.md"
    else:
        note_path = vault_path / f"{title}.md"
    
    try:
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        rel_path = note_path.relative_to(vault_path)
        return f"Created note: {rel_path}"
        
    except Exception as e:
        return f"Error creating note: {e}"

def update_obsidian_note(title: str, content: str, append: bool = False, vault_path: str = None) -> str:
    """Update an existing note or append to it."""
    if vault_path is None:
        vault_path = _find_obsidian_vault()
        if not vault_path:
            return "No Obsidian vault path configured."
    
    vault_path = Path(vault_path)
    
    # First try to find the existing note
    note_title_clean = title.strip()
    if note_title_clean.endswith('.md'):
        note_title_clean = note_title_clean[:-3]
    
    # Try to find the existing note
    search_strategies = [
        lambda: _search_exact_path(vault_path, note_title_clean),
        lambda: _search_case_insensitive(vault_path, note_title_clean),
        lambda: _search_filename_only(vault_path, note_title_clean),
    ]
    
    note_path = None
    for strategy in search_strategies:
        result = strategy()
        if result:
            note_path, _ = result
            break
    
    if not note_path:
        # Note doesn't exist, create it
        return create_obsidian_note(title, content, str(vault_path))
    
    try:
        if append:
            # Read existing content and append
            with open(note_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            new_content = existing_content + "\n\n" + content
        else:
            # Replace content
            new_content = content
        
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        rel_path = note_path.relative_to(vault_path)
        action = "Appended to" if append else "Updated"
        return f"{action} note: {rel_path}"
        
    except Exception as e:
        return f"Error updating note: {e}"

def create_daily_note(content: str = None, vault_path: str = None) -> str:
    """Create today's daily note with optional content."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    if content is None:
        content = f"# {today}\n\n## Tasks\n- \n\n## Notes\n\n"
    
    return create_obsidian_note(today, content, vault_path, "Daily Notes")

def list_recent_notes(vault_path: str = None, limit: int = 10) -> str:
    """List recently modified notes in Obsidian vault."""
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
        mod_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        
        result_parts.append(f"{i+1}. **{title}**\n   Path: {rel_path}\n   Modified: {mod_date}\n")
    
    return "\n".join(result_parts)