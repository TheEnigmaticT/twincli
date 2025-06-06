# twincli/tools/enhanced_git_command.py
"""
Enhanced Git command execution with intelligent path resolution and user-friendly error handling.

Category: version_control
Created: 2025-06-01
"""

import subprocess
import json
import os
from typing import Optional, List, Union
from twincli.tools.smart_path_finder import smart_git_path_resolver, smart_find_path


def smart_git_command(command: str, args: Optional[List[str]] = None, repo_path: Optional[str] = None, auto_resolve_path: bool = True) -> str:
    """
    Executes Git commands with intelligent path resolution and helpful error messages.
    
    Args:
        command: The Git command to execute (e.g., "pull", "push", "merge")
        args: Optional list of arguments for the Git command
        repo_path: Optional path to the Git repository (will be auto-resolved if provided)
        auto_resolve_path: Whether to automatically try to resolve repository paths
        
    Returns:
        JSON string containing the stdout, stderr, return code, and helpful context
    """
    # Handle args properly - convert protobuf RepeatedComposite to list if needed
    if args is None:
        args = []
    else:
        # Safe conversion that handles both lists and protobuf objects
        try:
            # If it's already a list, use it as-is
            if isinstance(args, list):
                pass  # args is already a list
            else:
                # Convert protobuf RepeatedComposite or other iterable to list
                args = list(args)
        except Exception:
            # If conversion fails, default to empty list
            args = []
    
    # Smart path resolution
    resolved_repo_path = None
    resolution_info = ""
    
    if repo_path and auto_resolve_path:
        resolution_result = smart_git_path_resolver(repo_path)
        
        if "✅" in resolution_result:
            # Successful resolution - extract the path
            import re
            path_match = re.search(r'`([^`]+)`', resolution_result)
            if path_match:
                resolved_repo_path = path_match.group(1)
                resolution_info = f"Auto-resolved '{repo_path}' to '{resolved_repo_path}'"
        else:
            # Failed resolution - return the helpful error message
            return json.dumps({
                "command": f"git {command} {' '.join(args)}",
                "error": "Path resolution failed",
                "resolution_help": resolution_result,
                "returncode": -1
            })
    else:
        resolved_repo_path = repo_path
    
    # Build the Git command
    git_command = ["git", command] + args
    
    try:
        # Execute the Git command
        process = subprocess.run(
            git_command,
            cwd=resolved_repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        
        # Prepare the result
        result = {
            "command": " ".join(git_command),
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "returncode": process.returncode,
            "working_directory": resolved_repo_path or os.getcwd()
        }
        
        # Add resolution info if path was auto-resolved
        if resolution_info:
            result["path_resolution"] = resolution_info
        
        # Add user-friendly interpretation of common errors
        if process.returncode != 0:
            result["error_help"] = _interpret_git_error(command, process.stderr, resolved_repo_path)
        
        # Add success context for successful operations
        if process.returncode == 0:
            result["success_info"] = _interpret_git_success(command, process.stdout, args)
        
        return json.dumps(result, indent=2)
        
    except FileNotFoundError:
        return json.dumps({
            "command": " ".join(git_command),
            "error": "Git command not found. Please ensure Git is installed and in your PATH.",
            "error_help": "Install Git: sudo apt install git (Ubuntu/Debian) or brew install git (macOS)",
            "returncode": -1
        })
    except Exception as e:
        return json.dumps({
            "command": " ".join(git_command),
            "error": f"An unexpected error occurred: {e}",
            "returncode": -1
        })


def _interpret_git_error(command: str, stderr: str, repo_path: Optional[str]) -> str:
    """Provide user-friendly interpretation of Git errors."""
    stderr_lower = stderr.lower()
    
    if "not a git repository" in stderr_lower:
        return f"""
🔍 **Not a Git Repository Error**
• The directory '{repo_path or 'current directory'}' is not a Git repository
• Solution: Navigate to a Git repository or run 'git init' to create one
• Check: ls -la .git (should exist in a Git repository)
"""
    
    elif "no such file or directory" in stderr_lower:
        return f"""
📁 **Path Not Found Error**
• The specified path does not exist
• Check the path spelling and ensure the directory exists
• Current working directory: {os.getcwd()}
"""
    
    elif "nothing to commit" in stderr_lower:
        return f"""
✅ **Nothing to Commit**
• All changes are already staged and committed
• Use 'git status' to see the current state
• This is normal when the repository is up to date
"""
    
    elif "working tree clean" in stderr_lower:
        return f"""
✅ **Working Tree Clean**
• No changes to commit
• Repository is in a clean state
• All files are tracked and up to date
"""
    
    elif "authentication failed" in stderr_lower or "permission denied" in stderr_lower:
        return f"""
🔐 **Authentication Error**
• Git credentials are missing or incorrect
• Solution: Set up SSH keys or personal access tokens
• Check: git config --list | grep user
"""
    
    elif "merge conflict" in stderr_lower or "conflict" in stderr_lower:
        return f"""
🔀 **Merge Conflict**
• Manual resolution required
• Edit conflicted files and remove conflict markers
• Then: git add . && git commit
"""
    
    elif "remote origin already exists" in stderr_lower:
        return f"""
🌐 **Remote Already Exists**
• The remote 'origin' is already configured
• Use 'git remote -v' to see current remotes
• Use 'git remote set-url origin <url>' to change it
"""
    
    else:
        return f"""
❌ **Git Error Occurred**
• Command: git {command}
• Error: {stderr[:200]}
• Try: git status to check repository state
• Help: git help {command}
"""


def _interpret_git_success(command: str, stdout: str, args: List[str]) -> str:
    """Provide context for successful Git operations."""
    if command == "add":
        return "✅ Files successfully staged for commit"
    
    elif command == "commit":
        if "files changed" in stdout or "insertion" in stdout:
            return f"✅ Commit created successfully with changes"
        else:
            return "✅ Commit completed"
    
    elif command == "push":
        if "up-to-date" in stdout.lower():
            return "✅ Repository is already up to date"
        else:
            return "✅ Changes pushed to remote repository successfully"
    
    elif command == "pull":
        if "up-to-date" in stdout.lower():
            return "✅ Local repository is already up to date"
        else:
            return "✅ Remote changes pulled and merged successfully"
    
    elif command == "status":
        return "📊 Repository status retrieved"
    
    elif command == "clone":
        return "✅ Repository cloned successfully"
    
    else:
        return f"✅ Git {command} completed successfully"


def quick_git_operations(operation: str, repo_path: str, commit_message: Optional[str] = None, auto_generate_message: bool = True) -> str:
    """
    Perform common Git operations with a single command.
    
    Args:
        operation: "stage_all", "commit_all", "push", "pull", "status", or "full_commit_push"
        repo_path: Path to the Git repository
        commit_message: Commit message (if None and auto_generate_message=True, will be generated automatically)
        auto_generate_message: Whether to automatically generate commit messages based on file changes
        
    Returns:
        Combined results of the Git operations
    """
    results = []
    
    # Import the smart commit message generator
    try:
        from twincli.tools.smart_commit_message import analyze_git_changes, smart_commit_with_analysis
        smart_commit_available = True
    except ImportError:
        smart_commit_available = False
    
    if operation == "stage_all":
        result = smart_git_command("add", ["."], repo_path)
        results.append(("Stage All", result))
    
    elif operation == "commit_all":
        if not commit_message and auto_generate_message and smart_commit_available:
            # Use smart commit with analysis
            result = smart_commit_with_analysis(repo_path, commit_message)
            results.append(("Smart Commit", result))
        else:
            if not commit_message:
                commit_message = f"Auto-commit: Updates from {os.getlogin()} on {os.uname().nodename}"
            
            # Stage all changes first
            stage_result = smart_git_command("add", ["."], repo_path)
            results.append(("Stage All", stage_result))
            
            # Then commit
            commit_result = smart_git_command("commit", ["-m", commit_message], repo_path)
            results.append(("Commit", commit_result))
    
    elif operation == "full_commit_push":
        if not commit_message and auto_generate_message and smart_commit_available:
            # Analyze changes first to generate a good commit message
            analysis_result = analyze_git_changes(repo_path)
            try:
                analysis_data = json.loads(analysis_result)
                if analysis_data.get("success"):
                    commit_message = analysis_data["suggested_commit_message"]
                    results.append(("Change Analysis", analysis_result))
            except:
                pass
        
        if not commit_message:
            commit_message = f"Auto-commit: Updates from {os.getlogin()} on {os.uname().nodename}"
        
        # Stage, commit, and push
        operations = [
            ("Stage All", smart_git_command("add", ["."], repo_path)),
            ("Commit", smart_git_command("commit", ["-m", commit_message], repo_path)),
            ("Push", smart_git_command("push", [], repo_path))
        ]
        results.extend(operations)
    
    elif operation == "status":
        result = smart_git_command("status", [], repo_path)
        results.append(("Status", result))
    
    elif operation == "pull":
        result = smart_git_command("pull", [], repo_path)
        results.append(("Pull", result))
    
    elif operation == "push":
        result = smart_git_command("push", [], repo_path)
        results.append(("Push", result))
    
    else:
        return json.dumps({"error": f"Unknown operation: {operation}"})
    
    # Compile results
    compiled_results = {
        "operation": operation,
        "repo_path": repo_path,
        "steps_completed": len(results),
        "results": {},
        "commit_message_used": commit_message if commit_message else None
    }
    
    for step_name, step_result in results:
        try:
            step_data = json.loads(step_result)
            compiled_results["results"][step_name] = {
                "success": step_data.get("returncode", -1) == 0 or step_data.get("success", False),
                "command": step_data.get("command", ""),
                "output": step_data.get("stdout", "") or step_data.get("commit_output", ""),
                "error": step_data.get("stderr", "") or step_data.get("error", ""),
                "help": step_data.get("error_help", "") or step_data.get("success_info", "")
            }
            
            # Extract commit message if this was a smart commit
            if step_name == "Smart Commit" and step_data.get("commit_message_used"):
                compiled_results["commit_message_used"] = step_data["commit_message_used"]
                
        except:
            compiled_results["results"][step_name] = {
                "success": False,
                "error": "Failed to parse result",
                "raw_result": step_result
            }
    
    return json.dumps(compiled_results, indent=2)


# Export the enhanced git tools
enhanced_git_tools = [
    smart_git_command,
    quick_git_operations
]

# Also import and re-export smart commit tools
try:
    from twincli.tools.smart_commit_message import smart_commit_tools
    enhanced_git_tools.extend(smart_commit_tools)
except ImportError:
    pass