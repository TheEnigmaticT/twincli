def run_shell(command: str) -> str:
    import subprocess
    try:
        output = subprocess.getoutput(command)
        return output
    except Exception as e:
        return f"Error: {e}"

shell_tool = {
    "function": run_shell,
    "name": "run_shell",
    "description": "Run a Linux shell command and return the output.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to run"
            }
        },
        "required": ["command"]
    }
}
