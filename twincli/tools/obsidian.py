import os
import re
from pathlib import Path
from typing import List, Dict

def read_obsidian_note(note_title: str, vault_path: str = None) -> str:
    """Read the full content of a specific Obsidian note.
    
    Args:
        note_title: The title/name of the note to read (without .md extension)
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
    
    # Try to find the note (case-insensitive search)
    note_title_lower = note_title.lower()
    
    for md_file in vault_path.rglob("*.md"):
        # Skip hidden files and folders
        if any(part.startswith('.') for part in md_file.parts):
            continue
            
        # Check if filename matches (with or without .md)
        file_title = md_file.stem.lower()
        if file_title == note_title_lower:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                rel_path = md_file.relative_to(vault_path)
                return f"**Note: {md_file.stem}**\nPath: {rel_path}\n\n{content}"
                
            except Exception as e:
                return f"Error reading note '{note_title}': {e}"
    
    # If exact match not found, try partial matching
    partial_matches = []
    for md_file in vault_path.rglob("*.md"):
        if any(part.startswith('.') for part in md_file.parts):
            continue
            
        file_title = md_file.stem.lower()
        if note_title_lower in file_title:
            partial_matches.append(md_file)
    
    if len(partial_matches) == 1:
        # Single partial match, return it
        md_file = partial_matches[0]
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            rel_path = md_file.relative_to(vault_path)
            return f"**Note: {md_file.stem}** (partial match)\nPath: {rel_path}\n\n{content}"
            
        except Exception as e:
            return f"Error reading note '{md_file.stem}': {e}"
    
    elif len(partial_matches) > 1:
        # Multiple partial matches, show options
        match_list = [f"- {md_file.stem}" for md_file in partial_matches[:10]]
        return f"Multiple notes found matching '{note_title}':\n" + "\n".join(match_list) + "\n\nPlease be more specific."
    
    else:
        return f"No note found with title '{note_title}' in your Obsidian vault."


def search_obsidian(query: str, vault_path: str = None) -> str:
    """Search through Obsidian vault for notes containing the query.
    
    Searches note titles, content, and tags for the given query.
    
    Args:
        query: The search term to look for
        vault_path: Path to Obsidian vault (if None, will try to detect)
        
    Returns:
        String containing matching notes with excerpts
    """
    # Try to find vault path if not provided
    if vault_path is None:
        vault_path = _find_obsidian_vault()
        if not vault_path:
            return "No Obsidian vault path configured. Please specify vault_path or set OBSIDIAN_VAULT_PATH environment variable."
    
    vault_path = Path(vault_path)
    if not vault_path.exists():
        return f"Obsidian vault not found at: {vault_path}"
    
    # Search for markdown files
    matches = []
    query_lower = query.lower()
    
    # Walk through all .md files in the vault
    for md_file in vault_path.rglob("*.md"):
        # Skip hidden files and folders
        if any(part.startswith('.') for part in md_file.parts):
            continue
            
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if query matches title (filename)
            title = md_file.stem
            title_match = query_lower in title.lower()
            
            # Check if query matches content
            content_match = query_lower in content.lower()
            
            if title_match or content_match:
                # Extract relevant excerpt
                excerpt = _extract_excerpt(content, query, max_length=200)
                
                # Get tags if any
                tags = _extract_tags(content)
                tags_str = f" Tags: {', '.join(tags)}" if tags else ""
                
                # Get relative path for cleaner display
                rel_path = md_file.relative_to(vault_path)
                
                match_info = {
                    'title': title,
                    'path': str(rel_path),
                    'excerpt': excerpt,
                    'tags': tags_str,
                    'title_match': title_match
                }
                matches.append(match_info)
                
        except Exception as e:
            # Skip files that can't be read
            continue
    
    if not matches:
        return f"No notes found containing '{query}' in your Obsidian vault."
    
    # Sort by relevance (title matches first, then by filename)
    matches.sort(key=lambda x: (not x['title_match'], x['title'].lower()))
    
    # Format results
    result_parts = [f"Found {len(matches)} notes containing '{query}':\n"]
    
    for i, match in enumerate(matches[:10]):  # Limit to top 10 results
        title_indicator = " ⭐" if match['title_match'] else ""
        result_parts.append(
            f"**{i+1}. {match['title']}**{title_indicator}\n"
            f"Path: {match['path']}{match['tags']}\n"
            f"Excerpt: {match['excerpt']}\n"
        )
    
    if len(matches) > 10:
        result_parts.append(f"... and {len(matches) - 10} more results")
    
    return "\n".join(result_parts)


def _find_obsidian_vault() -> str:
    """Try to find Obsidian vault path automatically."""
    # Check TwinCLI config first
    from twincli.config import load_config
    config = load_config()
    config_path = config.get('obsidian_vault_path')
    if config_path and Path(config_path).exists():
        return config_path
    
    # Check environment variable
    env_path = os.getenv('OBSIDIAN_VAULT_PATH')
    if env_path and Path(env_path).exists():
        return env_path
    
    # Common locations to check
    home = Path.home()
    common_paths = [
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


def _extract_excerpt(content: str, query: str, max_length: int = 200) -> str:
    """Extract a relevant excerpt containing the query."""
    query_lower = query.lower()
    content_lower = content.lower()
    
    # Find the query in the content
    query_pos = content_lower.find(query_lower)
    if query_pos == -1:
        # If not found in content, return beginning
        return content[:max_length].strip() + ("..." if len(content) > max_length else "")
    
    # Extract context around the query
    start = max(0, query_pos - max_length // 2)
    end = min(len(content), query_pos + len(query) + max_length // 2)
    
    excerpt = content[start:end].strip()
    
    # Clean up excerpt
    excerpt = re.sub(r'\n+', ' ', excerpt)  # Replace newlines with spaces
    excerpt = re.sub(r'\s+', ' ', excerpt)  # Normalize whitespace
    
    # Add ellipsis if needed
    if start > 0:
        excerpt = "..." + excerpt
    if end < len(content):
        excerpt = excerpt + "..."
    
    return excerpt


def _extract_tags(content: str) -> List[str]:
    """Extract hashtags from content."""
    # Find hashtags (simple regex)
    tags = re.findall(r'#(\w+)', content)
    return list(set(tags))  # Remove duplicates


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