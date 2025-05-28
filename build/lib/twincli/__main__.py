# twincli/__main__.py

import os
import sys
import json
import readline  # enables up-arrow history in REPL
import google.generativeai as genai
from rich.console import Console
from rich.markdown import Markdown
from twincli.tools import TOOLS

CONFIG_PATH = os.path.expanduser("~/.twincli/config.json")
console = Console()

def load_config():
    if not os.path.exists(CONFIG_PATH):
        console.print("[red]No config found. Run `twincli --config` to set API key.[/red]")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)

def save_config(api_key):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({"api_key": api_key}, f)
    console.print("[green]API key saved.[/green]")

def configure():
    console.print("[bold yellow]Enter your Gemini API key:[/bold yellow]")
    key = input("> ").strip()
    save_config(key)
    sys.exit(0)
def start_repl():
    config = load_config()
    genai.configure(api_key=config["api_key"])
    model = genai.GenerativeModel(
        model_name="models/gemini-2.5-pro-preview-05-06",
        tools=TOOLS,
        generation_config={
            "temperature": 0.7,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 4096,
        },
        safety_settings={
            "HARASSMENT": "BLOCK_LOW_AND_ABOVE",
            "HATE": "BLOCK_LOW_AND_ABOVE",
            "SEXUAL": "BLOCK_LOW_AND_ABOVE",
            "DANGEROUS": "BLOCK_LOW_AND_ABOVE",
        }
    )
    chat = model.start_chat(
        enable_automatic_function_calling=True,
        enable_search=True
    )

    console.print("[bold blue]TwinCLI Chat Mode — Gemini 2.5 Pro[/bold blue]\n")

    while True:
        try:
            prompt = input("[bold cyan]You > [/bold cyan]").strip()
            if prompt.lower() in ("exit", "quit"):
                break
            response = chat.send_message(prompt)
            console.print(Markdown(response.text))
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Exiting TwinCLI.[/bold yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        configure()
    elif len(sys.argv) == 1:
        start_repl()
    else:
        console.print("[blue]Usage:[/blue] twincli to chat, or twincli --config to set API key")

if __name__ == "__main__":
    main()
