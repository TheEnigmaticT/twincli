import google.generativeai as genai
from rich.console import Console
from rich.markdown import Markdown
from twincli.config import load_config
from twincli.tools import TOOLS

console = Console()

def start_repl():
    config = load_config()
    genai.configure(api_key=config["api_key"])
    
    # Debug: Check what tools we're loading
    console.print(f"[dim]Loading {len(TOOLS)} tools: {[getattr(tool, '__name__', str(tool)) for tool in TOOLS]}[/dim]")
    
    # Create the model - let Google AI handle the tool conversion automatically
    model = genai.GenerativeModel(
        model_name="gemini-2.5-pro-preview-05-06",
        tools=TOOLS,
        system_instruction="You are a helpful assistant. When asked to perform calculations or solve problems, think through them step by step and show your reasoning. You can perform basic mathematical calculations including date arithmetic like ISO week calculations.",
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

    console.print("[bold blue]TwinCLI Chat Mode — Gemini 2.5 Flash[/bold blue]\n")

    while True:
        try:
            # Handle multi-line input
            prompt_lines = []
            console.print("[bold cyan]You > [/bold cyan]", end="")
            
            while True:
                try:
                    if not prompt_lines:
                        # First line
                        line = input().strip()
                    else:
                        # Continuation lines
                        line = input("     > ").strip()
                    
                    if line.endswith("\\"):
                        # Continue on next line (remove the backslash)
                        prompt_lines.append(line[:-1])
                    else:
                        prompt_lines.append(line)
                        break
                except EOFError:
                    # Handle Ctrl+D gracefully
                    if prompt_lines:
                        break
                    else:
                        console.print("\n[bold yellow]Exiting TwinCLI.[/bold yellow]")
                        return
            
            prompt = "\n".join(prompt_lines).strip()
            
            # Handle empty input
            if not prompt:
                continue
                
            # Handle exit commands
            if prompt.lower() in ("exit", "quit", ":q"):
                break
            
            response = chat.send_message(prompt)
            
            # Handle function calls properly
            if (response.candidates and 
                response.candidates[0].finish_reason.name != "MALFORMED_FUNCTION_CALL" and
                response.candidates[0].content.parts):
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        # Gemini wants to call a function
                        function_name = part.function_call.name
                        function_args = dict(part.function_call.args)
                        
                        console.print(f"[dim]Calling {function_name} with args: {function_args}[/dim]")
                        
                        # Execute the function (same pattern as search_web)
                        try:
                            if function_name == "search_web":
                                from twincli.tools.search import search_web
                                result = search_web(**function_args)
                            elif function_name == "search_obsidian":
                                from twincli.tools.obsidian import search_obsidian
                                result = search_obsidian(**function_args)
                            elif function_name == "read_obsidian_note":
                                from twincli.tools.obsidian import read_obsidian_note
                                result = read_obsidian_note(**function_args)
                            elif function_name == "list_recent_notes":
                                from twincli.tools.obsidian import list_recent_notes
                                result = list_recent_notes(**function_args)
                            else:
                                console.print(f"[red]Unknown function: {function_name}[/red]")
                                continue
                            
                            # Send the result back to continue the conversation
                            function_response = genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=function_name,
                                    response={"result": result}
                                )
                            )
                            response = chat.send_message([function_response])
                            console.print(Markdown(response.text))
                        except Exception as e:
                            console.print(f"[red]Error executing {function_name}:[/red] {e}")
                    elif hasattr(part, 'text') and part.text:
                        console.print(Markdown(part.text))
            else:
                console.print(Markdown(response.text))
                
        except genai.types.StopCandidateException as e:
            console.print(f"[red]Model stopped generation:[/red] {e}")
            console.print("[yellow]This might be due to a malformed function call. Try rephrasing your question.[/yellow]")
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Exiting TwinCLI.[/bold yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            import traceback
            traceback.print_exc()