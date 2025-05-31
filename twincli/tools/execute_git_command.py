
# twincli/tools/execute_git_command.py
"""
Executes common Git commands safely.

Category: version_control
Created: 2025-05-30
"""

import subprocess
import json
from typing import Optional, List

def execute_git_command(command: str, args: Optional[List[str]] = None, repo_path: Optional[str] = None) -> str:
    """
    Executes common Git commands safely.
    
    Args:
        command: The Git command to execute (e.g., "pull", "push", "merge").
        args: Optional list of arguments for the Git command.
        repo_path: Optional path to the Git repository. If None, the current working directory is used.
        
    Returns:
        A JSON string containing the stdout, stderr, and return code of the Git command execution.
    """
    if args is None:
        args = []

    git_command = ["git", command] + args
    
    try:
        process = subprocess.run(
            git_command,
            cwd=repo_path,  # Execute in specified repository path if provided
            capture_output=True,
            text=True,  # Decode stdout/stderr as text
            check=False  # Do not raise an exception for non-zero exit codes
        )
        
        result = {
            "command": " ".join(git_command),
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "returncode": process.returncode
        }
        return json.dumps(result)

    except FileNotFoundError:
        return json.dumps({"error": "Git command not found. Please ensure Git is installed and in your PATH."})
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {e}"})


# Tool registration for TwinCLI
execute_git_command_metadata = {
    "function": execute_git_command,
    "name": "execute_git_command",
    "description": "Executes common Git commands safely.",
    "category": "version_control",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The Git command to execute (e.g., \"pull\", \"push\", \"merge\")."
            },
            "args": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of arguments for the Git command."
            },
            "repo_path": {
                "type": "string",
                "description": "Optional path to the Git repository. If None, the current working directory is used."
            }
        },
        "required": ["command"]
    }
}
