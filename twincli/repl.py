import google.generativeai as genai
from rich.console import Console
from rich.markdown import Markdown
from twincli.config import load_config
from twincli.tools import TOOLS
from datetime import datetime
import time
import random

console = Console()

# Rate limiting configuration
class RateLimiter:
    def __init__(self):
        self.max_requests_per_minute = 60  # Gemini's actual limit
        self.max_tokens_per_minute = 1_000_000  # Gemini's actual limit
        self.request_times = []
        self.token_usage_history = []
        self.last_request_time = 0
        
    def _calculate_adaptive_interval(self, current_usage, max_limit, usage_type="requests"):
        """Calculate adaptive wait time based on current usage percentage."""
        usage_percentage = current_usage / max_limit
        
        if usage_percentage < 0.66:  # Below 66% - no throttling
            return 0.0
        elif usage_percentage < 0.80:  # 66-80% - light throttling
            # Linear scale from 0 to 0.5 seconds
            return (usage_percentage - 0.66) / (0.80 - 0.66) * 0.5
        elif usage_percentage < 0.90:  # 80-90% - moderate throttling
            # Linear scale from 0.5 to 2.0 seconds
            return 0.5 + (usage_percentage - 0.80) / (0.90 - 0.80) * 1.5
        else:  # 90%+ - aggressive throttling
            # Logarithmic scale from 2.0 seconds upward
            excess = usage_percentage - 0.90
            return 2.0 + (excess / 0.10) ** 2 * 8.0  # Up to 10 seconds at 100%
    
    def should_rate_limit(self, estimated_tokens=0):
        """Check if we should rate limit based on recent usage.""" 
        now = time.time()
        
        # Clean old entries (older than 1 minute)
        cutoff = now - 60
        self.request_times = [t for t in self.request_times if t > cutoff]
        self.token_usage_history = [(t, tokens) for t, tokens in self.token_usage_history if t > cutoff]
        
        current_requests = len(self.request_times)
        recent_tokens = sum(tokens for _, tokens in self.token_usage_history)
        projected_tokens = recent_tokens + estimated_tokens
        
        # Calculate required wait times based on usage
        request_wait = self._calculate_adaptive_interval(current_requests, self.max_requests_per_minute, "requests")
        token_wait = self._calculate_adaptive_interval(projected_tokens, self.max_tokens_per_minute, "tokens")
        
        # Use the longer of the two wait times
        required_wait = max(request_wait, token_wait)
        
        if required_wait > 0:
            time_since_last = now - self.last_request_time
            if time_since_last < required_wait:
                remaining_wait = required_wait - time_since_last
                
                # Determine reason for throttling
                if token_wait > request_wait:
                    reason = f"Token usage at {projected_tokens/self.max_tokens_per_minute*100:.1f}% ({projected_tokens:,}/{self.max_tokens_per_minute:,})"
                else:
                    reason = f"Request rate at {current_requests/self.max_requests_per_minute*100:.1f}% ({current_requests}/{self.max_requests_per_minute})"
                    
                return True, reason, remaining_wait
        
        return False, None, 0
    
    def record_request(self, token_count=0):
        """Record a successful request."""
        now = time.time()
        self.request_times.append(now)
        self.token_usage_history.append((now, token_count))
        self.last_request_time = now
    
    def wait_if_needed(self):
        """Wait if we need to respect rate limits."""
        should_limit, reason, wait_time = self.should_rate_limit()
        if should_limit:
            console.print(f"[yellow]Adaptive rate limiting: {reason}. Waiting {wait_time:.1f}s...[/yellow]")
            time.sleep(wait_time)

# Global rate limiter
rate_limiter = RateLimiter()

# Gemini 2.5 Flash pricing (as of January 2025)
PRICING = {
    "gemini-2.5-flash-preview-05-20": {
        "input_tokens_per_million": 0.075,
        "output_tokens_per_million": 0.30,
    }
}

class TokenTracker:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.session_start = time.time()
        self.conversation_count = 0
    
    def track_usage(self, response, model_name="gemini-2.5-flash-preview-05-20"):
        """Track token usage from a response."""
        if not response.usage_metadata:
            return None
        
        input_tokens = response.usage_metadata.prompt_token_count or 0
        output_tokens = response.usage_metadata.candidates_token_count or 0
        
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.conversation_count += 1
        
        # Calculate costs
        pricing = PRICING.get(model_name, PRICING["gemini-2.5-flash-preview-05-20"])
        input_cost = (input_tokens / 1_000_000) * pricing["input_tokens_per_million"]
        output_cost = (output_tokens / 1_000_000) * pricing["output_tokens_per_million"]
        total_cost = input_cost + output_cost
        
        self.total_cost += total_cost
        
        # Record with rate limiter
        rate_limiter.record_request(input_tokens + output_tokens)
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }
    
    def get_session_summary(self):
        """Get session summary with total usage and costs."""
        elapsed_time = time.time() - self.session_start
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": self.total_cost,
            "conversation_count": self.conversation_count,
            "elapsed_minutes": elapsed_time / 60,
            "cost_per_minute": self.total_cost / (elapsed_time / 60) if elapsed_time > 0 else 0
        }

# Global token tracker
token_tracker = TokenTracker()

def exponential_backoff(attempt, base_delay=1.0, max_delay=60.0):
    """Calculate exponential backoff delay."""
    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
    return delay

def safe_api_call(chat, content, max_retries=3):
    """Make an API call with exponential backoff and error handling."""
    for attempt in range(max_retries):
        try:
            # Check rate limiting before making request
            rate_limiter.wait_if_needed()
            
            # Make the API call
            response = chat.send_message(content)
            
            # Track token usage
            usage_info = token_tracker.track_usage(response)
            if usage_info:
                console.print(f"[blue]Tokens: {usage_info['total_tokens']:,} (${usage_info['total_cost']:.6f})[/blue]")
            
            return response, None
            
        except Exception as e:
            error_str = str(e)
            
            # Handle specific error types
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                # Rate limit error - extract retry delay if available
                retry_delay = 60  # Default fallback
                if "retry_delay" in error_str:
                    try:
                        # Try to extract the retry delay from the error
                        import re
                        delay_match = re.search(r'seconds: (\d+)', error_str)
                        if delay_match:
                            retry_delay = int(delay_match.group(1))
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    console.print(f"[red]Rate limit exceeded. Waiting {retry_delay}s before retry {attempt + 1}/{max_retries}...[/red]")
                    time.sleep(retry_delay)
                    continue
                else:
                    return None, f"Rate limit exceeded after {max_retries} attempts. Please wait before continuing."
            
            elif "503" in error_str or "502" in error_str or "server" in error_str.lower():
                # Server error - use exponential backoff
                if attempt < max_retries - 1:
                    delay = exponential_backoff(attempt)
                    console.print(f"[yellow]Server error. Retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries})[/yellow]")
                    time.sleep(delay)
                    continue
                else:
                    return None, f"Server error after {max_retries} attempts: {e}"
            
            else:
                # Other errors - don't retry
                return None, f"API error: {e}"
    
    return None, "Max retries exceeded"

ENHANCED_SYSTEM_INSTRUCTION = """You are TwinCLI, an advanced agentic AI assistant with comprehensive tool access and persistent memory capabilities. You operate as a thoughtful, proactive partner in accomplishing complex tasks.

**REQUIRED LOGGING PATTERNS:**

1. **ALWAYS start each session** with `initialize_work_session()`

2. **For Complex tasks or requests, ALWAYS:**
   - Call `log_reasoning()` to explain your approach and thinking
   - Call `log_tool_action()` after using any tool to summarize what you learned
   - Call `log_task_progress()` when starting, completing, or failing tasks

3. **For complex requests, ALWAYS:**
   - Create a detailed plan with `create_task_plan()`
   - Log your reasoning for the plan structure
   - Log progress after each major step
   - Log insights and discoveries as you work

4. **When using tools, ALWAYS log:**
   - Why you chose that specific tool
   - What you're trying to accomplish
   - What the results told you
   - How it influences your next steps

5. **Log your decision-making process:**
   - When you encounter problems or obstacles
   - When you change your approach
   - When you discover something unexpected
   - When you make connections between different pieces of information

## IMPORTANT: AVOID CONVERSATION LOOPS

- If a user provides a large block of text, treat it as complete input, not individual items to process one by one
- Don't ask for "the next word" or similar - process full content blocks as complete units
- If you're unsure about input format, ask once for clarification rather than creating a loop

## Examples of REQUIRED logging calls:

```
# At the start of any session
initialize_work_session()

# Before doing research
log_reasoning("I need to understand X before I can Y. My approach will be to...", "Starting research phase")

# After using a tool
log_tool_action("search_web", "Research competitors in the startup consulting space", "Found 5 potential competitors, with [Company] being the closest match")

# When completing tasks
log_task_progress("task_1", "Research target company", "complete", "Successfully analyzed their service offerings and target market")
```

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
- Initialize work session and log your reasoning
- Respond directly with clear, step-by-step reasoning
- Use tools only when necessary for current information
- Log any tools used and insights gained

For **MODERATE TASKS** (research, content creation):
- Initialize work session
- Create a brief informal plan and log your approach
- Execute with tool integration
- Log key results and insights for future reference

For **COMPLEX TASKS** (multi-step projects, automation):
1. Initialize work session and check context
2. Create detailed task plan with dependencies and log your reasoning
3. Log reasoning and approach decisions
4. Execute systematically with progress updates after each major step
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

def create_function_dispatcher():
    """Create a dynamic function dispatcher from loaded tools."""
    dispatcher = {}
    
    # Import all the tool modules and map function names to actual functions
    from twincli.tools.search import search_web
    from twincli.tools.obsidian import (
        search_obsidian, read_obsidian_note, create_obsidian_note,
        update_obsidian_note, create_daily_note, list_recent_notes
    )
    from twincli.tools.filesystem import write_file, read_file, create_directory
    from twincli.tools.browser import (
        open_browser_tab, get_page_info, find_elements_by_text,
        click_element_by_text, fill_form_field, take_screenshot,
        get_page_text, close_browser
    )
    from twincli.tools.task_planner import (
        create_task_plan, display_current_plan, get_next_task,
        start_task, complete_task, fail_task, get_plan_summary,
        clear_current_plan
    )
    from twincli.tools.memory_journal import (
        initialize_work_session, log_plan_to_journal, log_task_progress,
        log_reasoning, log_tool_action, get_work_context,
        analyze_my_work_patterns, get_todays_journal
    )
    
    # Map function names to actual functions
    function_map = {
        'search_web': search_web,
        'search_obsidian': search_obsidian,
        'read_obsidian_note': read_obsidian_note,
        'create_obsidian_note': create_obsidian_note,
        'update_obsidian_note': update_obsidian_note,
        'create_daily_note': create_daily_note,
        'list_recent_notes': list_recent_notes,
        'write_file': write_file,
        'read_file': read_file,
        'create_directory': create_directory,
        'open_browser_tab': open_browser_tab,
        'get_page_info': get_page_info,
        'find_elements_by_text': find_elements_by_text,
        'click_element_by_text': click_element_by_text,
        'fill_form_field': fill_form_field,
        'take_screenshot': take_screenshot,
        'get_page_text': get_page_text,
        'close_browser': close_browser,
        'create_task_plan': create_task_plan,
        'display_current_plan': display_current_plan,
        'get_next_task': get_next_task,
        'start_task': start_task,
        'complete_task': complete_task,
        'fail_task': fail_task,
        'get_plan_summary': get_plan_summary,
        'clear_current_plan': clear_current_plan,
        'initialize_work_session': initialize_work_session,
        'log_plan_to_journal': log_plan_to_journal,
        'log_task_progress': log_task_progress,
        'log_reasoning': log_reasoning,
        'log_tool_action': log_tool_action,
        'get_work_context': get_work_context,
        'analyze_my_work_patterns': analyze_my_work_patterns,
        'get_todays_journal': get_todays_journal,
    }
    
    return function_map

def auto_log_tool_usage(function_name, function_args, result, function_dispatcher):
    """Automatically log tool usage for better journal tracking."""
    # Don't log the logging functions themselves to avoid recursion
    if function_name.startswith('log_') or function_name in ['initialize_work_session', 'get_todays_journal']:
        return
    
    try:
        # Create a summary of what was accomplished
        if function_name == 'search_web':
            summary = f"Searched for: {function_args.get('query', 'unknown query')}"
        elif function_name == 'open_browser_tab':
            summary = f"Opened website: {function_args.get('url', 'unknown URL')}"
        elif function_name == 'get_page_text':
            summary = "Retrieved page content for analysis"
        elif function_name == 'create_obsidian_note':
            summary = f"Created note: {function_args.get('title', 'unnamed note')}"
        else:
            summary = f"Executed {function_name} with args: {function_args}"
        
        # Truncate very long results for readability
        result_summary = str(result)
        if len(result_summary) > 200:
            result_summary = result_summary[:200] + "... (truncated)"
        
        # Log the tool usage
        log_tool_action = function_dispatcher.get('log_tool_action')
        if log_tool_action:
            log_tool_action(function_name, summary, result_summary)
    except Exception as e:
        # Don't let logging errors break the main flow
        console.print(f"[dim]Auto-logging failed: {e}[/dim]")

def start_repl():
    global token_tracker, rate_limiter
    
    config = load_config()
    genai.configure(api_key=config["api_key"])
    
    # Create function dispatcher
    function_dispatcher = create_function_dispatcher()
    
    # Debug: Check what tools we're loading
    console.print(f"[dim]Loading {len(TOOLS)} tools: {[getattr(tool, '__name__', str(tool)) for tool in TOOLS]}[/dim]")
    console.print(f"[dim]Function dispatcher has {len(function_dispatcher)} functions[/dim]")
    
    # Create the model with enhanced configuration
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-preview-05-20",
        tools=TOOLS,
        system_instruction=ENHANCED_SYSTEM_INSTRUCTION,
        generation_config={
            "temperature": 0.8,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 8192,
        },
        safety_settings={
            "HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
            "HATE": "BLOCK_MEDIUM_AND_ABOVE", 
            "SEXUAL": "BLOCK_MEDIUM_AND_ABOVE",
            "DANGEROUS": "BLOCK_ONLY_HIGH",
        }
    )
    chat = model.start_chat()

    console.print("[bold blue]TwinCLI Chat Mode — Gemini 2.5 Flash[/bold blue]")
    console.print("[dim]Enhanced with adaptive rate limiting, auto-retry, and cost monitoring[/dim]\n")

    while True:
        try:
            # Handle multi-line input
            prompt_lines = []
            console.print("[bold cyan]You > [/bold cyan]", end="")
            
            while True:
                try:
                    if not prompt_lines:
                        line = input().strip()
                    else:
                        line = input("     > ").strip()
                    
                    if line.endswith("\\"):
                        prompt_lines.append(line[:-1])
                    else:
                        prompt_lines.append(line)
                        break
                except EOFError:
                    if prompt_lines:
                        break
                    else:
                        console.print("\n[bold yellow]Exiting TwinCLI.[/bold yellow]")
                        # Show session summary
                        summary = token_tracker.get_session_summary()
                        console.print(f"\n[dim]Session Summary:[/dim]")
                        console.print(f"[dim]Total tokens: {summary['total_tokens']:,} ({summary['total_input_tokens']:,} in, {summary['total_output_tokens']:,} out)[/dim]")
                        console.print(f"[dim]Total cost: ${summary['total_cost']:.4f}[/dim]")
                        console.print(f"[dim]Conversations: {summary['conversation_count']} over {summary['elapsed_minutes']:.1f} minutes[/dim]")
                        return
            
            prompt = "\n".join(prompt_lines).strip()
            
            if not prompt:
                continue
                
            if prompt.lower() in ("exit", "quit", ":q"):
                break
            
            # Usage commands
            if prompt.lower() in ("tokens", "cost", "usage"):
                summary = token_tracker.get_session_summary()
                console.print(f"\n[bold]Session Token Usage Summary:[/bold]")
                console.print(f"Input tokens: {summary['total_input_tokens']:,}")
                console.print(f"Output tokens: {summary['total_output_tokens']:,}")
                console.print(f"Total tokens: {summary['total_tokens']:,}")
                console.print(f"Total cost: ${summary['total_cost']:.6f}")
                console.print(f"Conversations: {summary['conversation_count']}")
                console.print(f"Average cost per minute: ${summary['cost_per_minute']:.6f}")
                continue
            
            # Make API call with rate limiting and retries
            response, error = safe_api_call(chat, prompt)
            if error:
                console.print(f"[red]Error: {error}[/red]")
                console.print("[yellow]Please wait a moment before trying again.[/yellow]")
                continue
            
            # Handle function calls with rate limiting
            while (response and response.candidates and 
                   response.candidates[0].content.parts and
                   any(hasattr(part, 'function_call') and part.function_call for part in response.candidates[0].content.parts)):
                
                function_responses = []
                
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_name = part.function_call.name
                        function_args = dict(part.function_call.args)
                        
                        console.print(f"[bright_green]Calling {function_name} with args: {function_args}[/bright_green]")
                        
                        try:
                            if function_name in function_dispatcher:
                                result = function_dispatcher[function_name](**function_args)
                                auto_log_tool_usage(function_name, function_args, result, function_dispatcher)
                                
                                function_response = genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=function_name,
                                        response={"result": result}
                                    )
                                )
                                function_responses.append(function_response)
                            else:
                                console.print(f"[red]Unknown function: {function_name}[/red]")
                        except Exception as e:
                            console.print(f"[red]Error executing {function_name}:[/red] {e}")
                            error_response = genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=function_name,
                                    response={"result": f"Error: {e}"}
                                )
                            )
                            function_responses.append(error_response)
                
                # Send function responses with rate limiting
                if function_responses:
                    response, error = safe_api_call(chat, function_responses)
                    if error:
                        console.print(f"[red]Error in function response: {error}[/red]")
                        break
                else:
                    break
            
            # Display text content
            if response and response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        console.print(Markdown(part.text))
            elif response and hasattr(response, 'text') and response.text:
                console.print(Markdown(response.text))
                
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Exiting TwinCLI.[/bold yellow]")
            break
        except Exception as e:
            console.print(f"[red]Unexpected error:[/red] {e}")
            import traceback
            traceback.print_exc()