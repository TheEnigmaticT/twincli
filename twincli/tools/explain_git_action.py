
# twincli/tools/explain_git_action.py
"""
Explains common Git actions and their effects.

Category: version_control
Created: 2025-05-30
"""

import json
from typing import Optional

def explain_git_action(git_action: str) -> str:
    """
    Explains common Git actions and their effects.
    
    Args:
        git_action: The Git action to explain (e.g., "pull", "push", "merge", "stash", "rebase").
        
    Returns:
        A JSON string containing the explanation of the Git action, or an error message if the action is not recognized.
    """
    git_explanations = {
        "pull": {
            "command": "git pull",
            "description": "Fetches changes from a remote repository and integrates them into the current branch. It's a combination of 'git fetch' and 'git merge'.",
            "effects": [
                "Downloads new commits, files, and refs from the specified remote repository.",
                "Merges the fetched changes into your current local branch.",
                "Can cause merge conflicts if local changes overlap with remote changes.",
                "Updates your local branch to reflect the remote's state."
            ]
        },
        "push": {
            "command": "git push",
            "description": "Uploads local branch commits to the corresponding remote repository.",
            "effects": [
                "Transfers your local commits to the remote branch.",
                "Updates the remote repository with your changes.",
                "Requires write access to the remote repository.",
                "Can be rejected if the remote branch has new commits that you haven't pulled (fast-forward vs. non-fast-forward push)."
            ]
        },
        "merge": {
            "command": "git merge <branch_name>",
            "description": "Integrates changes from one branch into another.",
            "effects": [
                "Combines the commit histories of two or more branches.",
                "Creates a new merge commit if there are divergent changes (a 3-way merge).",
                "Can result in merge conflicts that need to be resolved manually.",
                "Preserves the history of both branches."
            ]
        },
        "stash": {
            "command": "git stash",
            "description": "Temporarily saves changes that you don't want to commit immediately, allowing you to switch branches or work on something else.",
            "effects": [
                "Saves your modified tracked files and staged changes onto a stack of incomplete changes.",
                "Reverts your working directory to the HEAD commit, making it clean.",
                "You can reapply the stashed changes later using 'git stash apply' or 'git stash pop'.",
                "Stashes are local to your repository and not part of the commit history."
            ]
        },
        "rebase": {
            "command": "git rebase <base_branch>",
            "description": "Rewrites commit history by moving or combining a sequence of commits to a new base commit.",
            "effects": [
                "Reapplies commits from your current branch onto a new base branch.",
                "Creates a linear history, making the commit log cleaner.",
                "**DANGEROUS if used on public/shared branches** as it rewrites history, which can cause issues for collaborators.",
                "Can lead to rebase conflicts that need to be resolved.",
                "Avoid rebasing commits that have already been pushed to a shared remote repository."
            ]
        },
        "clone": {
            "command": "git clone <repository_url>",
            "description": "Creates a local copy of a remote Git repository.",
            "effects": [
                "Downloads the entire repository history, including all branches and commits.",
                "Sets up a remote tracking branch for the origin.",
                "Creates a new directory with the repository name in your current location."
            ]
        },
        "add": {
            "command": "git add <file_name> or git add .",
            "description": "Stages changes for the next commit. This moves changes from the working directory to the staging area.",
            "effects": [
                "Marks the specified files or all changes in the current directory (with '.') to be included in the next commit.",
                "Does not save changes to the repository history yet.",
                "You can unstage changes using 'git reset <file_name>'."
            ]
        },
        "commit": {
            "command": "git commit -m 'Your commit message'",
            "description": "Records the staged changes to the repository history as a new commit.",
            "effects": [
                "Creates a new commit object containing the staged changes, a commit message, and metadata (author, timestamp).",
                "Moves the changes from the staging area to the local repository.",
                "Each commit has a unique SHA-1 hash.",
                "Commits are immutable and form the project's history."
            ]
        },
        "status": {
            "command": "git status",
            "description": "Shows the state of the working directory and the staging area.",
            "effects": [
                "Lists which files are staged, unstaged, or untracked.",
                "Provides hints on how to move files between states (e.g., 'git add', 'git restore').",
                "Does not modify the repository or working directory."
            ]
        },
        "branch": {
            "command": "git branch <branch_name> (create) or git branch (list) or git branch -d <branch_name> (delete)",
            "description": "Used to create, list, or delete branches.",
            "effects": [
                "Creating a branch creates a new pointer to the current commit.",
                "Listing branches shows all local branches and the currently active one.",
                "Deleting a branch removes its pointer; changes on that branch are not lost until garbage collected if merged, or if not merged, the commits might become unreachable."
            ]
        },
        "checkout": {
            "command": "git checkout <branch_name> or git checkout -b <new_branch_name>",
            "description": "Switches between branches or restores working tree files.",
            "effects": [
                "Switches your working directory and HEAD to the specified branch.",
                "Can be used to create and switch to a new branch simultaneously ('git checkout -b').",
                "Can also be used to restore files to a previous state."
            ]
        }
    }

    try:
        action_lower = git_action.lower()
        if action_lower in git_explanations:
            result = {"action": action_lower, "explanation": git_explanations[action_lower]}
        else:
            result = {"error": f"Git action '{git_action}' not recognized. Please choose from: {', '.join(git_explanations.keys())}"}
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {e}"})

# Tool registration for TwinCLI
explain_git_action_metadata = {
    "function": explain_git_action,
    "name": "explain_git_action",
    "description": "Explains common Git actions and their effects.",
    "category": "version_control",
    "parameters": {
        "type": "object",
        "properties": {
            "git_action": {
                "type": "string",
                "description": "The Git action to explain (e.g., 'pull', 'push', 'merge', 'stash', 'rebase')."
            }
        },
        "required": ["git_action"]
    }
}
