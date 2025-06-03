# twincli/repl.py
"""
TwinCLI REPL - main conversation loop with enhanced UX.
Focuses purely on API interaction and conversation management.
"""

import google.generativeai as genai
from rich.console import Console
from rich.markdown import Markdown
from pathlib import Path
import time
import random
import json

from twincli.config import load_config
from twincli.tools import TOOLS
from twincli.display import (
    TwinCLIDisplay, 
    get_enhanced_multiline_input, 
    format_function_args_preview,
    get_current_session_info,
    get_tool_purpose_context,
    extract_project_data_from_current_project
)
from twincli.function_registry import create_function_dispatcher
from twincli.tools.context_compression import (
    ContextCompressor, ConversationTracker, enhanced_safe_api_call,
    initialize_session_with_kanban_state
)

console = Console()
display = TwinCLIDisplay(console)

# Rate limiting configuration
class RateLimiter:
    def __init__(self):
        self.max_requests_per_minute = 60
        self.max_tokens_per_minute = 1_000_000
        self.request_times = []
        self.token_usage_history = []
        self.last_request_time = 0
        
    def _calculate_adaptive_interval(self, current_usage, max_limit, usage_type="requests"):
        """Calculate adaptive wait time based on current usage percentage."""
        usage_percentage = current_usage / max_limit
        
        if usage_percentage < 0.66:
            return 0.0
        elif usage_percentage < 0.80:
            return (usage_percentage - 0.66) / (0.80 - 0.66) * 0.5
        elif usage_percentage < 0.90:
            return 0.5 + (usage_percentage - 0.80) / (0.90 - 0.80) * 1.5
        else:
            excess = usage_percentage - 0.90
            return 2.0 + (excess / 0.10) ** 2 * 8.0
    
    def should_rate_limit(self, estimated_tokens=0):
        """Check if we should rate limit based on recent usage.""" 
        now = time.time()
        cutoff = now - 60
        self.request_times = [t for t in self.request_times if t > cutoff]
        self.token_usage_history = [(t, tokens) for t, tokens in self.token_usage_history if t > cutoff]
        
        current_requests = len(self.request_times)
        recent_tokens = sum(tokens for _, tokens in self.token_usage_history)
        projected_tokens = recent_tokens + estimated_tokens
        
        request_wait = self._calculate_adaptive_interval(current_requests, self.max_requests_per_minute, "requests")
        token_wait = self._calculate_adaptive_interval(projected_tokens, self.max_tokens_per_minute, "tokens")
        
        required_wait = max(request_wait, token_wait)
        
        if required_wait > 0:
            time_since_last = now - self.last_request_time
            if time_since_last < required_wait:
                remaining_wait = required_wait - time_since_last
                
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
            display.status_update(f"Rate limiting: {reason}. Waiting {wait_time:.1f}s...", "warning")
            time.sleep(wait_time)


# Token tracking and pricing
PRICING = {
    "gemini-2.5-flash-preview-05-20": {
        "input_tokens_per_million": 0.15,
        "output_tokens_per_million": 0.60,
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
        
        pricing = PRICING.get(model_name, PRICING["gemini-2.5-flash-preview-05-20"])
        input_cost = (input_tokens / 1_000_000) * pricing["input_tokens_per_million"]
        output_cost = (output_tokens / 1_000_000) * pricing["output_tokens_per_million"]
        total_cost = input_cost + output_cost
        
        self.total_cost += total_cost
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


# Global instances
rate_limiter = RateLimiter()
token_tracker = TokenTracker()


def exponential_backoff(attempt, base_delay=1.0, max_delay=60.0):
    """Calculate exponential backoff delay."""
    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
    return delay


def safe_api_call(chat, content, max_retries=3):
    """Enhanced API call with better error display."""
    for attempt in range(max_retries):
        try:
            rate_limiter.wait_if_needed()
            response = chat.send_message(content)
            
            usage_info = token_tracker.track_usage(response)
            if usage_info:
                console.print(f"[dim]Tokens: {usage_info['total_tokens']:,} (${usage_info['total_cost']:.6f})[/dim]")
            
            return response, None
            
        except Exception as e:
            error_str = str(e)
            
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                retry_delay = 60
                if "retry_delay" in error_str:
                    try:
                        import re
                        delay_match = re.search(r'seconds: (\d+)', error_str)
                        if delay_match:
                            retry_delay = int(delay_match.group(1))
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    display.status_update(f"Rate limit exceeded. Waiting {retry_delay}s before retry {attempt + 1}/{max_retries}...", "warning")
                    time.sleep(retry_delay)
                    continue
                else:
                    return None, f"Rate limit exceeded after {max_retries} attempts. Please wait before continuing."
            
            elif "503" in error_str or "502" in error_str or "server" in error_str.lower():
                if attempt < max_retries - 1:
                    delay = exponential_backoff(attempt)
                    display.status_update(f"Server error. Retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries})", "warning")
                    time.sleep(delay)
                    continue
                else:
                    return None, f"Server error after {max_retries} attempts: {e}"
            else:
                return None, f"API error: {e}"
    
    return None, "Max retries exceeded"


def load_system_instruction() -> str:
    """Load system instruction from markdown file."""
    instruction_path = Path(__file__).parent / "system_instruction.md"
    
    try:
        return instruction_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        display.status_update(f"System instruction file not found: {instruction_path}", "warning")
        # Fallback to basic instruction
        return """You are TwinCLI, an advanced AI assistant. You have access to many tools and should use them to help users accomplish their goals."""
    except Exception as e:
        display.status_update(f"Error loading system instruction: {e}", "error")
        return """You are TwinCLI, an advanced AI assistant."""


def auto_log_tool_usage(function_name, function_args, result, function_dispatcher):
    """Automatically log tool usage for better journal tracking."""
    # TEMPORARILY DISABLED - recursion issues
    return


def start_repl():
    """Start the enhanced TwinCLI REPL with visual feedback and tool integration."""
    global token_tracker, rate_limiter
    
    # Load configuration
    config = load_config()
    genai.configure(api_key=config["api_key"])
    
    # Create function dispatcher
    function_dispatcher = create_function_dispatcher()
    
    # Initialize compression system
    compressor = ContextCompressor(None)
    tracker = ConversationTracker()
    
    # Load system instruction from file
    system_instruction = load_system_instruction()
    
    # Create the model with enhanced configuration
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-preview-05-20",
        tools=TOOLS,
        system_instruction=system_instruction,
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

    # Enhanced startup display
    display.startup_banner(len(TOOLS), len(function_dispatcher))
    
    # Show session info
    session_info = get_current_session_info()
    display.session_header(session_info)

    # Main conversation loop
    while True:
        try:
            # Get enhanced multi-line input
            prompt = get_enhanced_multiline_input(console)
            
            if not prompt:
                continue
                
            if prompt.lower() in ("exit", "quit", ":q"):
                break
            
            # Handle special commands
            if prompt.lower() in ("tokens", "cost", "usage"):
                summary = token_tracker.get_session_summary()
                display.usage_summary_table(summary)
                continue
            
            if prompt.lower() in ("session", "status"):
                session_info = get_current_session_info()
                display.session_header(session_info)
                continue
            
            # Make API call with enhanced error handling
            response, error = safe_api_call(chat, prompt)
            if error:
                display.status_update(f"Error: {error}", "error")
                display.status_update("Please wait a moment before trying again.", "warning")
                continue
            
            # Handle function calls with enhanced display
            while (response and response.candidates and 
                   response.candidates[0].content.parts and
                   any(hasattr(part, 'function_call') and part.function_call for part in response.candidates[0].content.parts)):
                
                function_responses = []
                
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_name = part.function_call.name
                        function_args = dict(part.function_call.args)
                        
                        # Enhanced tool call display
                        args_preview = format_function_args_preview(function_args)
                        purpose = get_tool_purpose_context(function_name, function_args)
                        
                        display.tool_action(function_name, purpose, args_preview)
                        
                        try:
                            if function_name in function_dispatcher:
                                result = function_dispatcher[function_name](**function_args)
                                auto_log_tool_usage(function_name, function_args, result, function_dispatcher)
                                
                                # Enhanced result display
                                display.tool_result(result, success=True)
                                
                                function_response = genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=function_name,
                                        response={"result": result}
                                    )
                                )
                                function_responses.append(function_response)
                            else:
                                error_msg = f"Unknown function: {function_name}"
                                display.tool_result(error_msg, success=False)
                        except Exception as e:
                            error_msg = f"Error executing {function_name}: {e}"
                            display.tool_result(error_msg, success=False)
                            error_response = genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=function_name,
                                    response={"result": error_msg}
                                )
                            )
                            function_responses.append(error_response)
                
                # Send function responses with rate limiting
                if function_responses:
                    response, error = safe_api_call(chat, function_responses)
                    if error:
                        display.status_update(f"Error in function response: {error}", "error")
                        break
                else:
                    break
            
            # Display AI response with enhanced formatting
            if response and response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        # Check if it's project-related content that should show progress
                        if any(keyword in part.text.lower() for keyword in ['project:', 'task', 'kanban', 'progress']):
                            project_data = extract_project_data_from_current_project()
                            if project_data:
                                display.project_progress_table(project_data)
                        
                        # Display the main response
                        console.print(Markdown(part.text))
            elif response and hasattr(response, 'text') and response.text:
                console.print(Markdown(response.text))
                
        except KeyboardInterrupt:
            display.status_update("Exiting TwinCLI.", "info")
            break
        except Exception as e:
            display.status_update(f"Unexpected error: {e}", "error")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    # Show final session summary
    summary = token_tracker.get_session_summary()
    display.final_session_summary(summary)