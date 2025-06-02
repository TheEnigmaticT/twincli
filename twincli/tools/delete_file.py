
import os
from typing import Optional
from pathlib import Path

def delete_file(file_path: str) -> dict:
    """
    Delete a file from the file system.
    
    Args:
        file_path: The full path to the file to be deleted.
        
    Returns:
        A dictionary indicating success or failure.
    """
    try:
        if not file_path or not file_path.strip():
            return {"error": "File path cannot be empty."}
        
        path = Path(file_path)
        if not path.is_file():
            return {"error": f"Path is not a file or does not exist: {file_path}"}
        
        os.remove(file_path)
        return {"success": f"Successfully deleted file: {file_path}"}
        
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except PermissionError:
        return {"error": f"Permission denied to delete file: {file_path}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

