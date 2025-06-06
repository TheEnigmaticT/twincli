# twincli/tools/filesystem.py
from pathlib import Path
import os

def write_file(file_path: str, content: str, append: bool = False) -> str:
    """Write content to a file."""
    try:
        mode = 'a' if append else 'w'
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content)
        action = "Appended to" if append else "Created"
        return f"{action} file: {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"

def read_file(file_path: str) -> str:
    """Read content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def create_directory(dir_path: str) -> str:
    """Create a directory structure."""
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        return f"Created directory: {dir_path}"
    except Exception as e:
        return f"Error creating directory: {e}"
    
def list_directory(directory_path: str) -> str:
    """List contents of a directory."""
    try:
        items = os.listdir(directory_path)
        dirs = [f"{item}/" for item in items if os.path.isdir(os.path.join(directory_path, item))]
        files = [item for item in items if os.path.isfile(os.path.join(directory_path, item))]
        
        result = f"Directory: {directory_path}\n\nDirectories:\n"
        result += "\n".join(f"  {d}" for d in sorted(dirs))
        result += "\n\nFiles:\n"
        result += "\n".join(f"  {f}" for f in sorted(files))
        return result
    except Exception as e:
        return f"Error listing directory: {e}"