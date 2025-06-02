# twincli/tools/smart_path_finder.py
"""
Intelligent path finder that tries multiple strategies to locate files and directories.

Category: filesystem
Created: 2025-06-01
"""

import os
import glob
from pathlib import Path
from typing import List, Optional, Dict, Tuple


def smart_find_path(search_path: str, path_type: str = "auto") -> str:
    """
    Intelligently finds a file or directory by trying multiple path resolution strategies.
    
    Args:
        search_path: The path to search for (can be partial, relative, or absolute)
        path_type: "file", "directory", or "auto" to detect automatically
        
    Returns:
        JSON string with the resolved path and search details, or suggestions if not found
    """
    import json
    
    results = {
        "original_query": search_path,
        "resolved_path": None,
        "search_strategies": [],
        "candidates_found": [],
        "success": False
    }
    
    # Strategy 1: Try the path as-is
    results["search_strategies"].append("exact_path")
    if os.path.exists(search_path):
        results["resolved_path"] = os.path.abspath(search_path)
        results["success"] = True
        return json.dumps(results)
    
    # Strategy 2: Try with home directory expansion
    results["search_strategies"].append("home_expansion")
    expanded_path = os.path.expanduser(search_path)
    if os.path.exists(expanded_path):
        results["resolved_path"] = os.path.abspath(expanded_path)
        results["success"] = True
        return json.dumps(results)
    
    # Strategy 3: Try common path prefixes with proper path structure preservation
    results["search_strategies"].append("common_prefixes")
    home_dir = os.path.expanduser("~")
    
    # Handle paths that start with username (like /tlongino/...)
    if search_path.startswith('/') and len(search_path.split('/')) > 1:
        path_parts = search_path.strip('/').split('/')
        username = path_parts[0]
        
        # Check if this looks like a username path pattern
        if username and not username.startswith(('usr', 'var', 'opt', 'etc', 'bin')):
            # Try replacing the username with the home directory path
            remaining_path = '/'.join(path_parts[1:]) if len(path_parts) > 1 else ''
            candidate_with_home = os.path.join(home_dir, remaining_path)
            
            if os.path.exists(candidate_with_home):
                results["candidates_found"].append(candidate_with_home)
                if not results["resolved_path"]:
                    results["resolved_path"] = os.path.abspath(candidate_with_home)
                    results["success"] = True
    
    # Standard prefix checking
    common_prefixes = [
        home_dir,
        f"{home_dir}/development",
        f"{home_dir}/dev", 
        f"{home_dir}/projects",
        f"{home_dir}/code",
        f"{home_dir}/Documents",
        f"{home_dir}/Desktop",
        "/opt",
        "/usr/local",
        "/var",
        "/tmp"
    ]
    
    # Clean the search path for standard prefix checking
    clean_search = search_path.lstrip('/')
    
    for prefix in common_prefixes:
        candidate_paths = [
            os.path.join(prefix, clean_search),
            os.path.join(prefix, search_path.split('/')[-1]),  # Just the final component as fallback
        ]
        
        for candidate in candidate_paths:
            if os.path.exists(candidate):
                results["candidates_found"].append(candidate)
                if not results["resolved_path"]:  # Take the first match
                    results["resolved_path"] = os.path.abspath(candidate)
                    results["success"] = True
    
    # Strategy 4: Glob pattern matching for partial names
    if not results["success"]:
        results["search_strategies"].append("glob_search")
        
        # Try glob patterns in common locations
        search_patterns = [
            f"**/*{os.path.basename(search_path)}*",
            f"**/{os.path.basename(search_path)}",
            f"*{os.path.basename(search_path)}*"
        ]
        
        search_locations = [home_dir, f"{home_dir}/development", f"{home_dir}/Documents"]
        
        for location in search_locations:
            if not os.path.exists(location):
                continue
                
            for pattern in search_patterns:
                try:
                    matches = list(Path(location).glob(pattern))
                    for match in matches[:5]:  # Limit to first 5 matches
                        match_str = str(match)
                        results["candidates_found"].append(match_str)
                        if not results["resolved_path"] and _is_good_match(match_str, search_path):
                            results["resolved_path"] = os.path.abspath(match_str)
                            results["success"] = True
                except Exception:
                    continue
    
    # Strategy 5: Case-insensitive search
    if not results["success"]:
        results["search_strategies"].append("case_insensitive")
        
        # Search in common directories with case insensitive matching
        for search_dir in [home_dir, f"{home_dir}/development", f"{home_dir}/Documents"]:
            if not os.path.exists(search_dir):
                continue
                
            try:
                for root, dirs, files in os.walk(search_dir):
                    # Check directories
                    for dir_name in dirs:
                        if dir_name.lower() == os.path.basename(search_path).lower():
                            candidate = os.path.join(root, dir_name)
                            results["candidates_found"].append(candidate)
                            if not results["resolved_path"]:
                                results["resolved_path"] = os.path.abspath(candidate)
                                results["success"] = True
                    
                    # Check files
                    for file_name in files:
                        if file_name.lower() == os.path.basename(search_path).lower():
                            candidate = os.path.join(root, file_name)
                            results["candidates_found"].append(candidate)
                            if not results["resolved_path"]:
                                results["resolved_path"] = os.path.abspath(candidate)
                                results["success"] = True
                    
                    # Don't search too deep to avoid performance issues
                    if root.count(os.sep) - search_dir.count(os.sep) > 3:
                        del dirs[:]
                        
            except Exception:
                continue
    
    return json.dumps(results)


def _is_good_match(found_path: str, search_path: str) -> bool:
    """Determine if a found path is a good match for the search."""
    search_basename = os.path.basename(search_path).lower()
    found_basename = os.path.basename(found_path).lower()
    
    # Exact match on basename
    if search_basename == found_basename:
        return True
    
    # Search term is contained in found path
    if search_basename in found_basename:
        return True
    
    # Path contains key components
    search_parts = search_path.lower().split('/')
    found_parts = found_path.lower().split('/')
    
    # Count matching parts
    matching_parts = sum(1 for part in search_parts if part in found_parts)
    return matching_parts >= len(search_parts) * 0.6  # 60% of parts should match


def resolve_path_intelligently(user_path: str, operation_context: str = "general") -> str:
    """
    High-level function that resolves a user-provided path intelligently.
    
    Args:
        user_path: The path provided by the user
        operation_context: Context like "git", "file_operation", etc. for better suggestions
        
    Returns:
        Human-readable result with the resolved path or helpful suggestions
    """
    import json
    
    # First try the smart path finder
    search_result = smart_find_path(user_path)
    result_data = json.loads(search_result)
    
    if result_data["success"]:
        resolved = result_data["resolved_path"]
        strategies = ", ".join(result_data["search_strategies"])
        
        return f"""✅ **Path Resolved Successfully**

**Original:** `{user_path}`
**Resolved:** `{resolved}`
**Method:** {strategies}

The path has been found and can be used for {operation_context} operations."""
    
    else:
        # Path not found, provide helpful suggestions
        candidates = result_data.get("candidates_found", [])
        strategies_tried = ", ".join(result_data["search_strategies"])
        
        suggestion_text = f"""❌ **Path Not Found: `{user_path}`**

**Search Strategies Tried:** {strategies_tried}

"""
        
        if candidates:
            suggestion_text += f"**Similar Paths Found:**\n"
            for i, candidate in enumerate(candidates[:5], 1):
                suggestion_text += f"{i}. `{candidate}`\n"
            suggestion_text += "\n**Suggestion:** Did you mean one of the above paths?\n\n"
        
        # Add context-specific suggestions
        if operation_context == "git":
            suggestion_text += "**Git Repository Suggestions:**\n"
            suggestion_text += "- Check if you're in the right directory\n"
            suggestion_text += "- Try: `~/development/project-name` or `/home/username/development/project-name`\n"
            suggestion_text += "- Verify the repository exists with: `ls -la /path/to/repository`\n"
        
        elif operation_context == "file_operation":
            suggestion_text += "**File Operation Suggestions:**\n"
            suggestion_text += "- Use absolute paths starting with `/` or `~/`\n"
            suggestion_text += "- Check current directory with: `pwd`\n"
            suggestion_text += "- List files with: `ls -la`\n"
        
        suggestion_text += f"\n**Quick Fixes to Try:**\n"
        suggestion_text += f"1. `{os.path.expanduser('~')}/{user_path.lstrip('/')}`\n"
        suggestion_text += f"2. `{os.path.expanduser('~/development')}/{os.path.basename(user_path)}`\n"
        suggestion_text += f"3. `{os.path.expanduser('~/Documents')}/{os.path.basename(user_path)}`\n"
        
        return suggestion_text


def smart_git_path_resolver(repo_path: str) -> str:
    """
    Specifically resolve Git repository paths with Git-specific logic.
    
    Args:
        repo_path: Repository path provided by user
        
    Returns:
        Resolved repository path or detailed suggestions
    """
    import json
    
    # Try smart path resolution first
    search_result = smart_find_path(repo_path)
    result_data = json.loads(search_result)
    
    if result_data["success"]:
        resolved_path = result_data["resolved_path"]
        
        # Verify it's actually a Git repository
        git_dir = os.path.join(resolved_path, '.git')
        if os.path.exists(git_dir):
            return f"""✅ **Git Repository Found**

**Path:** `{resolved_path}`
**Status:** Valid Git repository (.git directory confirmed)
**Ready for:** staging, committing, pushing operations"""
        else:
            return f"""⚠️ **Directory Found But Not a Git Repository**

**Path:** `{resolved_path}`
**Issue:** No .git directory found
**Suggestion:** Initialize with `git init` or check if this is the correct repository path"""
    
    else:
        # Repository not found, provide Git-specific suggestions
        candidates = result_data.get("candidates_found", [])
        
        # Check if any candidates are Git repositories
        git_repos = []
        for candidate in candidates:
            if os.path.exists(os.path.join(candidate, '.git')):
                git_repos.append(candidate)
        
        suggestion = f"""❌ **Git Repository Not Found: `{repo_path}`**

"""
        
        if git_repos:
            suggestion += "**Git Repositories Found Nearby:**\n"
            for repo in git_repos[:3]:
                suggestion += f"• `{repo}`\n"
            suggestion += "\n"
        
        suggestion += f"""**Common Git Repository Locations to Check:**
• `~/development/{os.path.basename(repo_path)}`
• `~/projects/{os.path.basename(repo_path)}`
• `~/code/{os.path.basename(repo_path)}`
• `~/Documents/{os.path.basename(repo_path)}`

**Next Steps:**
1. Verify the repository exists: `ls -la /path/to/repo`
2. Check for .git directory: `ls -la /path/to/repo/.git`
3. Clone if needed: `git clone <repository-url>`"""
        
        return suggestion


# Export the smart path tools
smart_path_tools = [
    smart_find_path,
    resolve_path_intelligently,
    smart_git_path_resolver
]