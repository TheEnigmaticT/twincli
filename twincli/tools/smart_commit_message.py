# twincli/tools/smart_commit_message.py
"""
Intelligent commit message generator that analyzes changes and creates descriptive messages.

Category: version_control
Created: 2025-06-01
"""

import subprocess
import json
import os
import re
from typing import List, Dict, Optional, Tuple
from twincli.tools.smart_path_finder import smart_find_path


def analyze_git_changes(repo_path: str) -> str:
    """
    Analyze git changes and generate an intelligent commit message.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        JSON string with change analysis and suggested commit message
    """
    import json
    
    # Resolve the repository path
    path_result = json.loads(smart_find_path(repo_path))
    if not path_result.get("success"):
        return json.dumps({
            "error": f"Could not resolve repository path: {repo_path}",
            "path_resolution": path_result
        })
    
    resolved_path = path_result["resolved_path"]
    
    try:
        # Get git status
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=resolved_path,
            capture_output=True,
            text=True
        )
        
        if status_result.returncode != 0:
            return json.dumps({
                "error": "Not a git repository or git command failed",
                "stderr": status_result.stderr
            })
        
        # Get diff stats for staged changes (this is the key improvement!)
        staged_diff_stat = subprocess.run(
            ["git", "diff", "--staged", "--stat"],
            cwd=resolved_path,
            capture_output=True,
            text=True
        )
        
        # Get diff stats for unstaged changes
        unstaged_diff_stat = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=resolved_path,
            capture_output=True,
            text=True
        )
        
        # Parse the changes
        analysis = _analyze_file_changes_with_stats(status_result.stdout, staged_diff_stat.stdout, resolved_path)
        
        # Generate commit message based on actual diff stats
        commit_message = _generate_commit_message_from_diff(analysis)
        
        return json.dumps({
            "success": True,
            "resolved_path": resolved_path,
            "change_analysis": analysis,
            "suggested_commit_message": commit_message,
            "git_status_output": status_result.stdout,
            "staged_diff_stat": staged_diff_stat.stdout,
            "unstaged_diff_stat": unstaged_diff_stat.stdout
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to analyze git changes: {e}",
            "resolved_path": resolved_path
        })


def _analyze_file_changes(git_status_output: str, repo_path: str) -> Dict:
    """Analyze the git status output to understand what changed."""
    
    analysis = {
        "modified_files": [],
        "new_files": [],
        "deleted_files": [],
        "renamed_files": [],
        "categories": {
            "tools": [],
            "core": [],
            "config": [],
            "tests": [],
            "docs": [],
            "cache": []
        },
        "summary": {
            "total_files": 0,
            "main_category": None,
            "has_new_features": False,
            "has_fixes": False,
            "has_refactoring": False
        }
    }
    
    lines = git_status_output.strip().split('\n')
    if not lines or lines == ['']:
        return analysis
    
    for line in lines:
        if len(line) < 3:
            continue
            
        status = line[:2]
        filepath = line[3:]
        
        # Categorize by change type
        if status.startswith('M'):
            analysis["modified_files"].append(filepath)
        elif status.startswith('A') or status.startswith('??'):
            analysis["new_files"].append(filepath)
        elif status.startswith('D'):
            analysis["deleted_files"].append(filepath)
        elif status.startswith('R'):
            analysis["renamed_files"].append(filepath)
        
        # Categorize by file type/location
        category = _categorize_file(filepath)
        if category:
            analysis["categories"][category].append(filepath)
    
    # Calculate summary
    analysis["summary"]["total_files"] = len(analysis["modified_files"]) + len(analysis["new_files"]) + len(analysis["deleted_files"])
    
    # Determine main category
    category_counts = {k: len(v) for k, v in analysis["categories"].items() if v}
    if category_counts:
        analysis["summary"]["main_category"] = max(category_counts.items(), key=lambda x: x[1])[0]
    
    # Detect nature of changes
    analysis["summary"]["has_new_features"] = len(analysis["new_files"]) > 0
    analysis["summary"]["has_fixes"] = any("fix" in f.lower() or "bug" in f.lower() for f in analysis["modified_files"])
    analysis["summary"]["has_refactoring"] = any("refactor" in f.lower() for f in analysis["modified_files"])
    
    return analysis


def _categorize_file(filepath: str) -> Optional[str]:
    """Categorize a file based on its path and name."""
    filepath_lower = filepath.lower()
    
    # Cache files
    if "__pycache__" in filepath or ".pyc" in filepath or ".cache" in filepath:
        return "cache"
    
    # Tools
    if "tools/" in filepath or "tool" in filepath_lower:
        return "tools"
    
    # Core system files
    if any(core in filepath_lower for core in ["repl.py", "__main__.py", "main.py", "core/", "engine/"]):
        return "core"
    
    # Configuration
    if any(config in filepath_lower for config in ["config", "setup", ".toml", ".json", ".yml", ".yaml"]):
        return "config"
    
    # Documentation
    if any(doc in filepath_lower for doc in ["readme", "doc", ".md", "license"]):
        return "docs"
    
    # Tests
    if any(test in filepath_lower for test in ["test", "spec"]):
        return "tests"
    
    return None


def _analyze_file_changes_with_stats(git_status_output: str, staged_diff_stat: str, repo_path: str) -> Dict:
    """Analyze the git status and diff stats to understand what changed."""
    
    analysis = {
        "modified_files": [],
        "new_files": [],
        "deleted_files": [],
        "renamed_files": [],
        "file_stats": {},  # filename -> {insertions, deletions, type}
        "categories": {
            "tools": [],
            "core": [],
            "config": [],
            "tests": [],
            "docs": [],
            "cache": []
        },
        "summary": {
            "total_files": 0,
            "total_insertions": 0,
            "total_deletions": 0,
            "main_category": None,
            "change_magnitude": "minor",  # minor, moderate, major
            "has_new_features": False,
            "has_fixes": False,
            "has_refactoring": False
        }
    }
    
    # Parse git status for file changes
    lines = git_status_output.strip().split('\n')
    if not lines or lines == ['']:
        return analysis
    
    for line in lines:
        if len(line) < 3:
            continue
            
        status = line[:2]
        filepath = line[3:]
        
        # Categorize by change type
        if status.startswith('M'):
            analysis["modified_files"].append(filepath)
        elif status.startswith('A') or status.startswith('??'):
            analysis["new_files"].append(filepath)
        elif status.startswith('D'):
            analysis["deleted_files"].append(filepath)
        elif status.startswith('R'):
            analysis["renamed_files"].append(filepath)
        
        # Categorize by file type/location
        category = _categorize_file(filepath)
        if category:
            analysis["categories"][category].append(filepath)
    
    # Parse diff stats to get insertion/deletion counts
    if staged_diff_stat.strip():
        stat_lines = staged_diff_stat.strip().split('\n')
        for line in stat_lines:
            # Parse lines like: " twincli/repl.py | 3 +++"
            # or " twincli/tools/smart_commit_message.py | 90 +++++++++++++++++++++++------------"
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    filename = parts[0].strip()
                    stats_part = parts[1].strip()
                    
                    # Extract numbers and change indicators
                    insertions = stats_part.count('+')
                    deletions = stats_part.count('-')
                    
                    # Try to extract actual numbers if present
                    import re
                    numbers = re.findall(r'\d+', stats_part)
                    if numbers:
                        total_changes = int(numbers[0])
                        # If we have both + and -, try to split intelligently
                        if '+' in stats_part and '-' in stats_part:
                            # This is a modification with both additions and deletions
                            analysis["file_stats"][filename] = {
                                "insertions": insertions,
                                "deletions": deletions,
                                "total_changes": total_changes,
                                "type": "modified"
                            }
                        elif '+' in stats_part:
                            analysis["file_stats"][filename] = {
                                "insertions": total_changes,
                                "deletions": 0,
                                "total_changes": total_changes,
                                "type": "added" if filename in analysis["new_files"] else "modified"
                            }
                        elif '-' in stats_part:
                            analysis["file_stats"][filename] = {
                                "insertions": 0,
                                "deletions": total_changes,
                                "total_changes": total_changes,
                                "type": "deleted"
                            }
                    
                    analysis["summary"]["total_insertions"] += insertions
                    analysis["summary"]["total_deletions"] += deletions
    
    # Calculate summary
    analysis["summary"]["total_files"] = len(analysis["modified_files"]) + len(analysis["new_files"]) + len(analysis["deleted_files"])
    
    # Determine change magnitude based on total changes
    total_changes = analysis["summary"]["total_insertions"] + analysis["summary"]["total_deletions"]
    if total_changes > 100:
        analysis["summary"]["change_magnitude"] = "major"
    elif total_changes > 20:
        analysis["summary"]["change_magnitude"] = "moderate"
    else:
        analysis["summary"]["change_magnitude"] = "minor"
    
    # Determine main category
    category_counts = {k: len(v) for k, v in analysis["categories"].items() if v}
    if category_counts:
        analysis["summary"]["main_category"] = max(category_counts.items(), key=lambda x: x[1])[0]
    
    # Detect nature of changes
    analysis["summary"]["has_new_features"] = len(analysis["new_files"]) > 0
    analysis["summary"]["has_fixes"] = any("fix" in f.lower() or "bug" in f.lower() for f in analysis["modified_files"])
    analysis["summary"]["has_refactoring"] = total_changes > 50  # Large changes likely indicate refactoring
    
    return analysis


def _generate_commit_message_from_diff(analysis: Dict) -> str:
    """Generate a commit message based on git diff stats."""
    
    if analysis["summary"]["total_files"] == 0:
        return "chore: no changes to commit"
    
    main_category = analysis["summary"]["main_category"]
    change_magnitude = analysis["summary"]["change_magnitude"]
    has_new = analysis["summary"]["has_new_features"]
    total_changes = analysis["summary"]["total_insertions"] + analysis["summary"]["total_deletions"]
    
    # Choose commit type prefix
    if has_new and len(analysis["new_files"]) > len(analysis["modified_files"]):
        prefix = "feat"
    elif analysis["summary"]["has_fixes"]:
        prefix = "fix"
    elif change_magnitude == "major":
        prefix = "refactor" if main_category == "core" else "enhance"
    elif main_category == "tools":
        prefix = "enhance"
    elif main_category == "config":
        prefix = "config"
    elif main_category == "docs":
        prefix = "docs"
    else:
        prefix = "update"
    
    # Generate description based on specific files and their changes
    descriptions = []
    
    # Look at the most significant changes
    significant_files = []
    for filename, stats in analysis["file_stats"].items():
        if stats["total_changes"] > 5:  # Only files with meaningful changes
            component_name = _extract_component_name(filename)
            change_size = "major" if stats["total_changes"] > 50 else "minor"
            significant_files.append((component_name, change_size, stats["total_changes"]))
    
    if significant_files:
        # Sort by change size (descending)
        significant_files.sort(key=lambda x: x[2], reverse=True)
        
        if len(significant_files) == 1:
            component, size, changes = significant_files[0]
            if size == "major":
                descriptions.append(f"rework {component}")
            else:
                descriptions.append(f"update {component}")
        elif len(significant_files) == 2:
            comp1, size1, _ = significant_files[0]
            comp2, size2, _ = significant_files[1]
            if size1 == "major":
                descriptions.append(f"rework {comp1}; update {comp2}")
            else:
                descriptions.append(f"update {comp1} and {comp2}")
        else:
            # Multiple files - group by type
            major_files = [comp for comp, size, _ in significant_files if size == "major"]
            minor_files = [comp for comp, size, _ in significant_files if size == "minor"]
            
            if major_files:
                descriptions.append(f"rework {major_files[0]}")
                if minor_files:
                    descriptions.append(f"minor updates on {', '.join(minor_files[:2])}")
            else:
                descriptions.append(f"minor updates on {', '.join([comp for comp, _, _ in significant_files[:3]])}")
    else:
        # Fallback for small changes
        all_files = analysis["modified_files"] + analysis["new_files"]
        if len(all_files) == 1:
            component = _extract_component_name(all_files[0])
            descriptions.append(f"minor update to {component}")
        else:
            descriptions.append(f"minor updates to {len(all_files)} files")
    
    # Build the final message
    description = "; ".join(descriptions)
    commit_msg = f"{prefix}: {description}"
    
    # Add context for significant changes
    if total_changes > 50:
        commit_msg += f"\n\n({analysis['summary']['total_insertions']}+ {analysis['summary']['total_deletions']}- lines across {analysis['summary']['total_files']} files)"
    
    return commit_msg
    """Generate an intelligent commit message based on the analysis."""
    
    if analysis["summary"]["total_files"] == 0:
        return "chore: no changes to commit"
    
    # Get the specific files that changed
    all_changed_files = analysis["modified_files"] + analysis["new_files"]
    main_category = analysis["summary"]["main_category"]
    has_new = analysis["summary"]["has_new_features"]
    has_fixes = analysis["summary"]["has_fixes"]
    
    # Choose commit type prefix
    if has_new and len(analysis["new_files"]) > len(analysis["modified_files"]):
        prefix = "feat"
    elif has_fixes:
        prefix = "fix"
    elif main_category == "tools":
        prefix = "feat" if has_new else "enhance"
    elif main_category == "core":
        prefix = "refactor" if analysis["summary"]["has_refactoring"] else "improve"
    elif main_category == "config":
        prefix = "config"
    elif main_category == "docs":
        prefix = "docs"
    else:
        prefix = "update"
    
    # Generate intelligent descriptions based on specific files
    if main_category == "tools":
        if has_new:
            new_tools = [f for f in analysis["new_files"] if "tool" in f.lower()]
            if new_tools:
                tool_names = [_extract_tool_name(f) for f in new_tools[:3]]
                tool_names = [name for name in tool_names if name]
                if tool_names:
                    description = f"add {', '.join(tool_names)} tool{'s' if len(tool_names) > 1 else ''}"
                else:
                    description = f"add {len(new_tools)} new tool{'s' if len(new_tools) > 1 else ''}"
            else:
                description = "add new tools and functionality"
        else:
            # Look at what specific tool files were modified
            modified_tools = [f for f in analysis["modified_files"] if "tool" in f.lower()]
            if modified_tools:
                tool_names = [_extract_tool_name(f) for f in modified_tools[:3]]
                tool_names = [name for name in tool_names if name]
                if tool_names:
                    description = f"enhance {', '.join(tool_names)} tool{'s' if len(tool_names) > 1 else ''}"
                else:
                    description = f"enhance tools system ({len(modified_tools)} files)"
            else:
                description = f"enhance tools system ({len(analysis['categories']['tools'])} files)"
    
    elif main_category == "core":
        # Be specific about core changes
        core_files = [f for f in all_changed_files if any(core in f.lower() for core in ["repl.py", "__main__.py", "main.py"])]
        if "repl.py" in str(core_files):
            description = "enhance REPL functionality and tool dispatcher"
        elif "__main__.py" in str(core_files):
            description = "update main application logic"
        else:
            description = "refactor core system components"
    
    elif main_category == "config":
        # Look at what config files changed
        config_files = [f for f in all_changed_files if any(cfg in f.lower() for cfg in ["config", "setup", ".toml", ".json", "__init__.py"])]
        if any("__init__.py" in f for f in config_files):
            description = "update tool configuration and imports"
        else:
            description = "update configuration and setup files"
    
    else:
        # For other categories, be more specific
        if len(all_changed_files) == 1:
            # Single file change - be very specific
            file = all_changed_files[0]
            filename = _extract_component_name(file)
            if has_new:
                description = f"add {filename}"
            else:
                description = f"update {filename}"
        else:
            # Multiple files - summarize intelligently
            if has_new:
                description = f"add {len(analysis['new_files'])} new file{'s' if len(analysis['new_files']) > 1 else ''}"
                if analysis["modified_files"]:
                    description += f" and update {len(analysis['modified_files'])} existing"
            else:
                # Look for important files that might indicate the purpose
                important_files = []
                for file in all_changed_files:
                    if any(important in file.lower() for important in ["git", "search", "path", "enhanced", "smart"]):
                        important_files.append(_extract_component_name(file))
                
                if important_files:
                    description = f"enhance {', '.join(set(important_files[:2]))}"
                    if len(important_files) > 2:
                        description += f" and {len(important_files) - 2} more"
                else:
                    description = f"update {len(analysis['modified_files'])} file{'s' if len(analysis['modified_files']) > 1 else ''}"
    
    # Add specific details for context
    details = []
    
    # Mention if we removed obsolete files
    if analysis["deleted_files"]:
        deleted_names = [_extract_component_name(f) for f in analysis["deleted_files"][:2]]
        details.append(f"remove {', '.join(deleted_names)}")
    
    # Build final message
    commit_msg = f"{prefix}: {description}"
    
    if details:
        commit_msg += f" ({'; '.join(details)})"
    
    # Add context for significant changes
    if analysis["summary"]["total_files"] > 3:
        commit_msg += f"\n\nUpdates {analysis['summary']['total_files']} files in {main_category} system"
    
    return commit_msg


def _extract_tool_name(filepath: str) -> Optional[str]:
    """Extract tool name from filepath."""
    filename = os.path.basename(filepath)
    if filename.endswith('.py'):
        name = filename[:-3]
        # Clean up common suffixes
        for suffix in ['_tool', 'tool_', '_tools', 'tools_']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
            elif name.startswith(suffix):
                name = name[len(suffix):]
        return name.replace('_', ' ').title()
    return None


def _extract_component_name(filepath: str) -> str:
    """Extract component name from filepath."""
    filename = os.path.basename(filepath)
    if filename.endswith('.py'):
        name = filename[:-3]
        return name.replace('_', ' ')
    return filename


def smart_commit_with_analysis(repo_path: str, custom_message: Optional[str] = None) -> str:
    """
    Perform git staging and commit with intelligent message generation.
    
    Args:
        repo_path: Path to the repository
        custom_message: Optional custom commit message (if None, will be generated)
        
    Returns:
        JSON result of the commit operation with analysis
    """
    # First analyze the changes
    analysis_result = analyze_git_changes(repo_path)
    analysis_data = json.loads(analysis_result)
    
    if not analysis_data.get("success"):
        return analysis_result
    
    resolved_path = analysis_data["resolved_path"]
    suggested_message = analysis_data["suggested_commit_message"]
    
    # Use custom message or generated one
    commit_message = custom_message or suggested_message
    
    try:
        # Stage all changes
        stage_result = subprocess.run(
            ["git", "add", "."],
            cwd=resolved_path,
            capture_output=True,
            text=True
        )
        
        if stage_result.returncode != 0:
            return json.dumps({
                "error": "Failed to stage changes",
                "stderr": stage_result.stderr,
                "analysis": analysis_data
            })
        
        # Commit changes
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=resolved_path,
            capture_output=True,
            text=True
        )
        
        return json.dumps({
            "success": True,
            "resolved_path": resolved_path,
            "commit_message_used": commit_message,
            "commit_output": commit_result.stdout,
            "commit_stderr": commit_result.stderr,
            "commit_returncode": commit_result.returncode,
            "change_analysis": analysis_data["change_analysis"],
            "suggested_message": suggested_message
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to commit changes: {e}",
            "analysis": analysis_data
        })


# Export the smart commit tools
smart_commit_tools = [
    analyze_git_changes,
    smart_commit_with_analysis
]