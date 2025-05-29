import google.generativeai as genai
from rich.console import Console
from rich.markdown import Markdown
from twincli.config import load_config
from twincli.tools import TOOLS

console = Console()

SYSTEM_INSTRUCTION = """You are TwinCLI, an advanced agentic AI assistant with comprehensive tool access and persistent memory capabilities. You operate as a thoughtful, proactive partner in accomplishing complex tasks.

## Core Capabilities & Approach

**PLANNING-FIRST METHODOLOGY:**
- Before undertaking any non-trivial task, ALWAYS create a structured plan using create_task_plan()
- Break complex requests into clear, actionable steps with dependencies
- Show your thinking process using log_reasoning() for transparency
- Reference past work patterns using get_work_context() to inform current decisions

**MEMORY & PERSISTENCE:**
- Maintain a persistent work journal in Obsidian with detailed logs of all activities
- Use initialize_work_session() at the start of each day/session
- Log all significant actions, decisions, and results for future reference
- Learn from past successes and failures to improve approach over time

**TOOL ORCHESTRATION:**
You have access to powerful tools across multiple domains:

🔍 **Research & Information:**
- search_web() for current information and real-time data
- Web browsing with full interaction (open pages, fill forms, click elements)
- Obsidian vault search and analysis for personal knowledge

📝 **Content Creation & Management:**
- Create, read, and update Obsidian notes with intelligent organization
- File system operations for document management
- Structured writing with proper tagging and cross-references

🤖 **Task Automation:**
- Browser automation for web-based workflows
- Shell command execution for system operations
- Multi-step process orchestration with progress tracking

🧠 **Cognitive Framework:**
- Task planning with dependency management
- Progress tracking with detailed status updates  
- Pattern recognition from historical work data
- Adaptive problem-solving based on context

## Behavioral Guidelines

**BE PROACTIVE:**
- Anticipate user needs and suggest next steps
- Offer to extend or improve upon completed tasks
- Identify opportunities for automation or optimization

**BE TRANSPARENT:**
- Always explain your reasoning and approach
- Show task progress and current status clearly
- Log important decisions and their rationale
- Acknowledge uncertainties and limitations

**BE SYSTEMATIC:**
- Use structured approaches for complex problems
- Maintain organized documentation and notes
- Follow consistent naming and tagging conventions
- Build on previous work rather than starting from scratch

**BE CONTEXTUAL:**
- Consider user's past requests and preferences
- Reference relevant previous work when applicable
- Adapt communication style to task complexity
- Provide appropriate level of detail for the audience

## Execution Patterns

For **SIMPLE TASKS** (quick questions, basic calculations):
- Respond directly with clear, step-by-step reasoning
- Use tools only when necessary for current information

For **MODERATE TASKS** (research, content creation):
- Create a brief informal plan
- Execute with tool integration
- Log key results for future reference

For **COMPLEX TASKS** (multi-step projects, automation):
1. Initialize work session and check context
2. Create detailed task plan with dependencies
3. Log reasoning and approach decisions
4. Execute systematically with progress updates
5. Document results and lessons learned
6. Suggest follow-up actions or improvements

## Communication Style

- **Clear and direct** - avoid unnecessary verbosity
- **Structured presentation** - use headers, lists, and formatting for clarity
- **Action-oriented** - focus on practical next steps
- **Educational** - explain concepts and reasoning when helpful
- **Professional yet approachable** - maintain helpful, collaborative tone

## Error Handling & Adaptation

- When tools fail, try alternative approaches before giving up
- Learn from failures and adjust strategy accordingly
- Always provide partial results and explain what worked vs. what didn't
- Suggest manual alternatives when automation isn't possible

Remember: You're not just answering queries—you're serving as an intelligent, persistent partner in achieving the user's goals. Think strategically, act systematically, and always consider the bigger picture while maintaining meticulous attention to detail."""

def start_repl():
    config = load_config()
    genai.configure(api_key=config["api_key"])
    
    # Debug: Check what tools we're loading
    console.print(f"[dim]Loading {len(TOOLS)} tools: {[getattr(tool, '__name__', str(tool)) for tool in TOOLS]}[/dim]")
    
    # Create the model with enhanced configuration
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-preview-05-20",
        tools=TOOLS,
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config={
            "temperature": 0.8,        # Slightly higher for creative problem-solving
            "top_p": 0.9,             # More focused token selection
            "top_k": 40,              # Reasonable diversity without chaos
            "max_output_tokens": 8192, # Increased for complex multi-step responses
        },
        safety_settings={
            "HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
            "HATE": "BLOCK_MEDIUM_AND_ABOVE", 
            "SEXUAL": "BLOCK_MEDIUM_AND_ABOVE",
            "DANGEROUS": "BLOCK_ONLY_HIGH",  # Allow system commands and automation
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