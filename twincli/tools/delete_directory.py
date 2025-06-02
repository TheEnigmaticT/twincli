import os
import shutil
from typing import Optional
from pathlib import Path

def delete_directory(dir_path: str, recursive: Optional[bool] = False) -> dict:
    """
    Delete a directory from the file system. Can delete non-empty directories if recursive is True.
    
    Args:
        dir_path: The full path to the directory to be deleted.
        recursive: If True, delete the directory and all its contents. If False (default), only delete if the directory is empty.
        
    Returns:
        A dictionary indicating success or failure.
    """
    try:
        if not dir_path or not dir_path.strip():
            return {"error": "Directory path cannot be empty."}
        
        path = Path(dir_path)
        if not path.is_dir():
            return {"error": f"Path is not a directory or does not exist: {dir_path}"}
        
        if recursive:
            shutil.rmtree(dir_path)
            return {"success": f"Successfully deleted directory and its contents: {dir_path}"}
        else:
            os.rmdir(dir_path) # Only deletes empty directories
            return {"success": f"Successfully deleted empty directory: {dir_path}"}
        
    except FileNotFoundError:
        return {"error": f"Directory not found: {dir_path}"}
    except OSError as e:
        if "Directory not empty" in str(e) and not recursive:
            return {"error": f"Directory is not empty. Use recursive=True to delete contents: {dir_path}"}
        return {"error": f"An operating system error occurred: {e}"}
    except PermissionError:
        return {"error": f"Permission denied to delete directory: {dir_path}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}
