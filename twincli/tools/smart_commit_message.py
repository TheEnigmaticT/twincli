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
        
        # Get diff summary for staged and unstaged changes
        diff_result = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=resolved_path,
            capture_output=True,
            text=True
        )
        
        # Get staged diff summary
        staged_diff_result = subprocess.run(
            ["git", "diff", "--cached", "--stat"],
            cwd=resolved_path,
            capture_output=True,
            text=True
        )
        
        # Parse the changes
        analysis = _analyze_file_changes(status_result.stdout, resolved_path)
        
        # Generate commit message
        commit_message = _generate_commit_message(analysis)
        
        return json.dumps({
            "success": True,
            "resolved_path": resolved_path,
            "change_analysis": analysis,
            "suggested_commit_message": commit_message,
            "git_status_output": status_result.stdout,
            "diff_summary": diff_result.stdout,
            "staged_diff_summary": staged_diff_result.stdout
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


def _generate_commit_message(analysis: Dict) -> str:
    """Generate an intelligent commit message based on the analysis."""
    
    if analysis["summary"]["total_files"] == 0:
        return "chore: no changes to commit"
    
    # Start building the commit message
    parts = []
    
    # Determine the primary action
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
    
    # Generate the main description
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
            description = f"enhance tools system ({len(analysis['categories']['tools'])} files)"
    
    elif main_category == "core":
        if "repl.py" in analysis["modified_files"]:
            description = "improve REPL functionality"
        elif "__main__.py" in analysis["modified_files"]:
            description = "update main application logic"
        else:
            description = "refactor core system"
    
    elif main_category == "config":
        description = "update configuration and setup"
    
    else:
        # Generic description based on file changes
        if has_new:
            description = f"add {len(analysis['new_files'])} new file{'s' if len(analysis['new_files']) > 1 else ''}"
        else:
            description = f"update {len(analysis['modified_files'])} file{'s' if len(analysis['modified_files']) > 1 else ''}"
    
    # Add details if relevant
    details = []
    
    # Mention specific important changes
    important_files = []
    for file in analysis["modified_files"] + analysis["new_files"]:
        if any(important in file.lower() for important in ["git", "search", "path", "enhanced"]):
            important_files.append(_extract_component_name(file))
    
    if important_files:
        details.append(f"including {', '.join(set(important_files[:3]))}")
    
    # Mention deletions if significant
    if analysis["deleted_files"]:
        details.append(f"remove {len(analysis['deleted_files'])} obsolete file{'s' if len(analysis['deleted_files']) > 1 else ''}")
    
    # Build final message
    commit_msg = f"{prefix}: {description}"
    
    if details:
        commit_msg += f" ({'; '.join(details)})"
    
    # Add file count for context
    if analysis["summary"]["total_files"] > 5:
        commit_msg += f"\n\nAffects {analysis['summary']['total_files']} files across {main_category} system"
    
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