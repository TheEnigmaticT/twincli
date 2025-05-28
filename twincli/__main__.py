import click
import google.generativeai as genai
from rich.console import Console
from rich.markdown import Markdown

from twincli.config import load_config, save_config
from twincli.tools import TOOLS
from twincli.repl import start_repl  # Break REPL into its own file for clarity since I'm switching to Click anyway

VERSION = "0.1.3"
console = Console()

@click.group()
def cli():
    """TwinCLI — A terminal assistant powered by Gemini 2.5."""
    pass

@cli.command()
def config():
    """Set up your Gemini and Serper API keys."""
    console.print("[bold yellow]Enter your Gemini API key:[/bold yellow]")
    gemini_key = input("> ").strip()

    console.print("[bold yellow]Enter your Serper.dev API key (for search):[/bold yellow]")
    serper_key = input("> ").strip()

    save_config(gemini_key, serper_key)
    console.print("[green]Keys saved.[/green]")

@cli.command()
def version():
    """Print the current TwinCLI version."""
    click.echo(f"TwinCLI v{VERSION}")

@cli.command()
def repl():
    """Start a REPL chat session with Gemini."""
    start_repl()

if __name__ == "__main__":
    cli()
