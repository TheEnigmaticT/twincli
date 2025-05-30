import google.generativeai as genai
from rich.console import Console
from rich.markdown import Markdown
from twincli.config import load_config
from twincli.tools import TOOLS

console = Console()

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
    chat = model.start_chat()

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
