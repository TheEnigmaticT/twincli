import click
import google.generativeai as genai
from rich.console import Console
from rich.markdown import Markdown

from twincli.config import load_config, save_config, validate_obsidian_path
from twincli.tools import TOOLS
from twincli.repl import start_repl

VERSION = "0.2.0"
console = Console()

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """TwinCLI — A terminal assistant powered by Gemini 2.5.
    
    By default, starts a REPL chat session. Use subcommands for other actions.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand provided, start REPL by default
        start_repl()

@cli.command()
def config():
    """Set up your Gemini, Serper, and Obsidian vault configuration."""
    console.print("[bold yellow]TwinCLI Configuration Setup[/bold yellow]\n")
    
    # Load existing config to show current values
    existing_config = load_config()
    
    # Gemini API Key
    current_gemini = "***configured***" if existing_config.get("api_key") else "not set"
    console.print(f"[dim]Current Gemini API key: {current_gemini}[/dim]")
    console.print("[bold yellow]Enter your Gemini API key (press Enter to keep current):[/bold yellow]")
    gemini_key = input("> ").strip()
    
    # Serper API Key
    current_serper = "***configured***" if existing_config.get("serper_api_key") else "not set"
    console.print(f"[dim]Current Serper API key: {current_serper}[/dim]")
    console.print("[bold yellow]Enter your Serper.dev API key for search (press Enter to keep current):[/bold yellow]")
    serper_key = input("> ").strip()
    
    # Obsidian Vault Path
    current_obsidian = existing_config.get("obsidian_vault_path", "not set")
    console.print(f"[dim]Current Obsidian vault path: {current_obsidian}[/dim]")
    console.print("[bold yellow]Enter the full path to your Obsidian vault (press Enter to keep current):[/bold yellow]")
    console.print("[dim]Example: /home/username/Documents/My Obsidian Vault[/dim]")
    obsidian_path = input("> ").strip()
    
    # Validate Obsidian path if provided
    if obsidian_path:
        is_valid, message = validate_obsidian_path(obsidian_path)
        if is_valid:
            console.print(f"[green]✓ {message}[/green]")
        else:
            console.print(f"[red]✗ {message}[/red]")
            console.print("[yellow]Warning: Invalid Obsidian path. You can fix this later by running 'twincli config' again.[/yellow]")
    
    # Save configuration
    save_config(gemini_key, serper_key, obsidian_path)
    console.print("\n[green]Configuration saved successfully![/green]")
    
    # Show summary
    final_config = load_config()
    console.print("\n[bold]Current Configuration:[/bold]")
    console.print(f"• Gemini API: {'✓ configured' if final_config.get('api_key') else '✗ not set'}")
    console.print(f"• Serper API: {'✓ configured' if final_config.get('serper_api_key') else '✗ not set'}")
    console.print(f"• Obsidian Vault: {'✓ ' + final_config.get('obsidian_vault_path', '') if final_config.get('obsidian_vault_path') else '✗ not set'}")

@cli.command()
def version():
    """Print the current TwinCLI version."""
    click.echo(f"TwinCLI v{VERSION}")

@cli.command()
def repl():
    """Start a REPL chat session with Gemini (same as default behavior)."""
    start_repl()

@cli.command()
def check():
    """Check current configuration and diagnose issues."""
    console.print("[bold blue]TwinCLI Configuration Check[/bold blue]\n")
    
    config = load_config()
    
    # Check Gemini API
    if config.get("api_key"):
        console.print("[green]✓ Gemini API key configured[/green]")
    else:
        console.print("[red]✗ Gemini API key not configured[/red]")
        console.print("  Run 'twincli config' to set up your Gemini API key")
    
    # Check Serper API
    if config.get("serper_api_key"):
        console.print("[green]✓ Serper API key configured[/green]")
    else:
        console.print("[yellow]⚠ Serper API key not configured[/yellow]")
        console.print("  Web search functionality will be limited")
    
    # Check Obsidian vault
    obsidian_path = config.get("obsidian_vault_path")
    if obsidian_path:
        is_valid, message = validate_obsidian_path(obsidian_path)
        if is_valid:
            console.print(f"[green]✓ Obsidian vault configured: {obsidian_path}[/green]")
            console.print(f"  {message}")
        else:
            console.print(f"[red]✗ Obsidian vault path invalid: {obsidian_path}[/red]")
            console.print(f"  {message}")
    else:
        console.print("[yellow]⚠ Obsidian vault not configured[/yellow]")
        console.print("  Note reading/writing functionality will be limited")
    
    # Check tools
    console.print(f"\n[bold]Available Tools:[/bold] {len(TOOLS)} loaded")

if __name__ == "__main__":
    cli()