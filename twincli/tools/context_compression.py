# twincli/tools/context_compression.py
"""
Context compression system for TwinCLI to maintain long-running conversations
without hitting context limits. Inspired by Claude Code's approach.
"""

import time
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import google.generativeai as genai


@dataclass
class ConversationState:
    """Represents the compressed state of a conversation."""
    session_id: str
    user_goal: str
    current_task_plan: Optional[Dict] = None
    completed_tasks: List[Dict] = None
    key_discoveries: List[str] = None
    active_context: List[str] = None
    tool_results_summary: Dict[str, str] = None
    current_step: str = ""
    next_actions: List[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.completed_tasks is None:
            self.completed_tasks = []
        if self.key_discoveries is None:
            self.key_discoveries = []
        if self.active_context is None:
            self.active_context = []
        if self.tool_results_summary is None:
            self.tool_results_summary = {}
        if self.next_actions is None:
            self.next_actions = []
        if self.timestamp is None:
            self.timestamp = time.time()


class ContextCompressor:
    """Manages conversation compression and state reconstruction."""
    
    def __init__(self, model, max_context_tokens=1000000, compression_threshold=400000):
        self.model = model
        self.max_context_tokens = max_context_tokens
        self.compression_threshold = compression_threshold  # Compress at 40% of limit
        self.conversation_history = []
        self.current_state = None
        self.compression_count = 0
        
    def estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count."""
        # More aggressive estimation: ~3 chars per token
        return len(text) // 3
    
    def should_compress(self, chat_history) -> bool:
        """Determine if compression is needed based on context size."""
        total_text = ""
        
        # Estimate current context size
        for message in chat_history:
            if hasattr(message, 'parts'):
                for part in message.parts:
                    if hasattr(part, 'text'):
                        total_text += part.text
        
        estimated_tokens = self.estimate_tokens(total_text)
        return estimated_tokens > self.compression_threshold
    
    def extract_conversation_state(self, chat_history, user_goal: str = None) -> ConversationState:
        """Extract key state information from conversation history."""
        
        # Use Gemini to analyze and compress the conversation
        compression_prompt = f"""
        Analyze this conversation history and extract the essential state information.
        Focus on:
        1. What the user is trying to accomplish (main goal)
        2. Current task plan and progress
        3. Key discoveries or important information found
        4. Current status and next steps
        5. Important tool results that need to be remembered
        
        Return a JSON object with this structure:
        {{
            "user_goal": "clear description of what user wants to accomplish",
            "current_task_plan": {{"goal": "...", "tasks": [...], "status": "..."}},
            "completed_tasks": [list of completed tasks with results],
            "key_discoveries": [important findings, facts, or insights],
            "active_context": [immediately relevant information for next steps],
            "tool_results_summary": {{"tool_name": "key results summary"}},
            "current_step": "what we're doing right now",
            "next_actions": [immediate next steps to take]
        }}
        
        Be concise but preserve all critical information needed to continue the work effectively.
        """
        
        try:
            # Create a temporary chat for compression analysis
            compression_chat = self.model.start_chat()
            response = compression_chat.send_message(compression_prompt)
            
            # Parse the JSON response
            state_data = json.loads(response.text)
            
            return ConversationState(
                session_id=f"session_{int(time.time())}",
                user_goal=state_data.get("user_goal", user_goal or "Unknown goal"),
                current_task_plan=state_data.get("current_task_plan"),
                completed_tasks=state_data.get("completed_tasks", []),
                key_discoveries=state_data.get("key_discoveries", []),
                active_context=state_data.get("active_context", []),
                tool_results_summary=state_data.get("tool_results_summary", {}),
                current_step=state_data.get("current_step", ""),
                next_actions=state_data.get("next_actions", [])
            )
            
        except Exception as e:
            print(f"Compression failed: {e}")
            # Fallback to basic state extraction
            return ConversationState(
                session_id=f"session_{int(time.time())}",
                user_goal=user_goal or "Continue previous work",
                current_step="Resuming after compression"
            )
    
    def create_compressed_prompt(self, state: ConversationState, kanban_state: str = None) -> str:
        """Create a compressed system prompt from conversation state and kanban board."""
        
        compressed_prompt = f"""You are TwinCLI, continuing a work session from compressed state.

**CURRENT SESSION STATE:**
Session ID: {state.session_id}
Goal: {state.user_goal}
Current Step: {state.current_step}

**ACTIVE KANBAN BOARD:**"""

        if kanban_state:
            compressed_prompt += f"""
{kanban_state}

**HISTORICAL CONTEXT:**"""
        else:
            compressed_prompt += """
No active task plan found. Ready to create new plan if needed.

**TASK PROGRESS:**"""

        if state.current_task_plan:
            compressed_prompt += f"""
Current Plan: {state.current_task_plan.get('goal', 'No goal specified')}
Plan Status: {state.current_task_plan.get('status', 'Unknown')}"""

        if state.completed_tasks:
            compressed_prompt += f"""

Completed Tasks:
{chr(10).join([f"- {task}" for task in state.completed_tasks[:5]])}"""

        if state.key_discoveries:
            compressed_prompt += f"""

Key Discoveries:
{chr(10).join([f"- {discovery}" for discovery in state.key_discoveries[:5]])}"""

        if state.tool_results_summary:
            compressed_prompt += f"""

Recent Tool Results:
{chr(10).join([f"- {tool}: {summary}" for tool, summary in state.tool_results_summary.items()])}"""

        if state.active_context:
            compressed_prompt += f"""

Active Context:
{chr(10).join([f"- {context}" for context in state.active_context[:3]])}"""

        if state.next_actions:
            compressed_prompt += f"""

Planned Next Actions:
{chr(10).join([f"- {action}" for action in state.next_actions[:3]])}"""

        compressed_prompt += f"""

**INSTRUCTIONS:**
- Continue working toward the goal: {state.user_goal}
- Use your full tool capabilities as needed
- Log important progress to maintain state
- If you need clarification about previous work, check the work journal
- Focus on immediate next steps while keeping the bigger picture in mind

**COMPRESSION INFO:**
This is compression #{self.compression_count + 1}. Previous conversation context has been compressed to preserve memory while maintaining essential state information.
"""

        return compressed_prompt
    
    def compress_and_restart(self, chat, user_goal: str = None, function_dispatcher=None) -> Tuple[Any, ConversationState]:
        """Compress current conversation and start fresh with compressed state."""
        
        # Get current kanban board state first
        kanban_state = None
        if function_dispatcher and 'display_current_plan' in function_dispatcher:
            try:
                kanban_state = function_dispatcher['display_current_plan']()
                print("[blue]Retrieved current kanban board state for compression[/blue]")
            except Exception as e:
                print(f"[yellow]Could not retrieve kanban state: {e}[/yellow]")
        
        # Extract state from current conversation
        try:
            # Get the current chat history (this is tricky with Gemini's API)
            # We'll need to track this ourselves in the REPL
            history = getattr(chat, '_history', [])
            state = self.extract_conversation_state(history, user_goal)
        except Exception as e:
            print(f"State extraction failed: {e}")
            # Create minimal state
            state = ConversationState(
                session_id=f"session_{int(time.time())}",
                user_goal=user_goal or "Continue previous work"
            )
        
        # Create new chat with compressed prompt including kanban state
        compressed_system_prompt = self.create_compressed_prompt(state, kanban_state)
        
        # Create new model instance with compressed system instruction
        new_model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-05-20",
            tools=chat.model._tools,  # Preserve tool access
            system_instruction=compressed_system_prompt,
            generation_config=chat.model._generation_config,
            safety_settings=chat.model._safety_settings
        )
        
        new_chat = new_model.start_chat()
        
        self.compression_count += 1
        self.current_state = state
        
        print(f"[Context compressed #{self.compression_count}] Session state preserved and conversation restarted.")
        
        return new_chat, state
    
    def get_compression_summary(self) -> str:
        """Get a summary of compression activity."""
        return f"""
Compression Summary:
- Compressions performed: {self.compression_count}
- Current session: {self.current_state.session_id if self.current_state else 'None'}
- Goal: {self.current_state.user_goal if self.current_state else 'None'}
"""


# Integration functions for the REPL

class ConversationTracker:
    """Tracks conversation for compression decisions."""
    
    def __init__(self):
        self.messages = []
        self.total_chars = 0
        self.actual_tokens_used = 0  # Track real token usage from API
        
    def add_message(self, role: str, content: str, function_calls: List[Dict] = None, token_count: int = 0):
        """Add a message to the conversation tracker."""
        message = {
            'role': role,
            'content': content,
            'function_calls': function_calls or [],
            'timestamp': time.time(),
            'char_count': len(content),
            'token_count': token_count
        }
        self.messages.append(message)
        self.total_chars += len(content)
        if token_count > 0:
            self.actual_tokens_used += token_count
    
    def get_context_estimate(self) -> int:
        """Get estimated token count for current context."""
        # Use actual token counts when available, fall back to estimation
        if self.actual_tokens_used > 0:
            return self.actual_tokens_used
        return self.total_chars // 3  # More aggressive estimation (3 chars per token)
    
    def should_compress(self, threshold: int = 400000) -> bool:
        """Check if compression is needed."""
        return self.get_context_estimate() > threshold


def initialize_session_with_kanban_state(function_dispatcher) -> str:
    """Initialize a new session by checking for existing kanban board state."""
    
    startup_context = []
    
    # 1. Initialize work session
    try:
        if 'initialize_work_session' in function_dispatcher:
            result = function_dispatcher['initialize_work_session']()
            startup_context.append(f"Work Session: {result}")
    except Exception as e:
        startup_context.append(f"Work Session Init Error: {e}")
    
    # 2. Check for active task plan/kanban board
    try:
        if 'display_current_plan' in function_dispatcher:
            kanban_state = function_dispatcher['display_current_plan']()
            startup_context.append(f"Active Kanban Board:\n{kanban_state}")
    except Exception as e:
        startup_context.append(f"Kanban Check: {e}")
    
    # 3. Get recent work context
    try:
        if 'get_work_context' in function_dispatcher:
            work_context = function_dispatcher['get_work_context'](days=1)
            startup_context.append(f"Recent Work Context:\n{work_context}")
    except Exception as e:
        startup_context.append(f"Work Context Error: {e}")
    
    # 4. Check if there's a next task ready to go
    try:
        if 'get_next_task' in function_dispatcher:
            next_task = function_dispatcher['get_next_task']()
            if "Next Task Ready" in next_task:
                startup_context.append(f"Ready Task:\n{next_task}")
    except Exception as e:
        startup_context.append(f"Next Task Check: {e}")
    
    return "\n\n".join(startup_context)


def enhanced_safe_api_call(chat, content, compressor: ContextCompressor, tracker: ConversationTracker, 
                          function_dispatcher=None, max_retries=3):
    """Enhanced API call with compression awareness and kanban integration."""
    
    # Check if compression is needed before making the call
    current_estimate = tracker.get_context_estimate()
    if tracker.should_compress():
        print(f"[yellow]Context at {current_estimate:,} tokens, approaching limits. Compressing conversation...[/yellow]")
        
        # Extract user goal from recent messages if possible
        user_goal = None
        for msg in reversed(tracker.messages[-10:]):
            if msg['role'] == 'user' and len(msg['content']) > 20:
                user_goal = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                break
        
        # Compress and restart (now includes kanban state)
        new_chat, state = compressor.compress_and_restart(chat, user_goal, function_dispatcher)
        
        # Reset tracker but preserve the compression info
        old_tokens = tracker.get_context_estimate()
        tracker.messages = []
        tracker.total_chars = 0
        tracker.actual_tokens_used = 0
        
        # Add compression info to tracker
        tracker.add_message("system", f"Conversation compressed. Previous context: {old_tokens:,} tokens")
        
        print(f"[green]✓ Compression complete. Context reset from {old_tokens:,} to ~0 tokens[/green]")
        
        return enhanced_safe_api_call(new_chat, content, compressor, tracker, function_dispatcher, max_retries)
    
    # Track the outgoing message
    tracker.add_message("user", str(content))
    
    # Make the regular API call with rate limiting
    for attempt in range(max_retries):
        try:
            # Import here to avoid circular import
            import time
            import random
            
            # Simple rate limiting check
            time.sleep(0.1)  # Basic throttling
            
            response = chat.send_message(content)
            
            # Extract token usage from response if available
            tokens_used = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                tokens_used = (response.usage_metadata.prompt_token_count or 0) + \
                             (response.usage_metadata.candidates_token_count or 0)
            
            # Track the response with actual token count
            if response and response.candidates and response.candidates[0].content.parts:
                response_text = ""
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
                tracker.add_message("assistant", response_text, token_count=tokens_used)
            
            return response, None, chat  # Return potentially new chat instance
            
        except Exception as e:
            # Handle retries as before
            if attempt < max_retries - 1:
                delay = min(1.0 * (2 ** attempt) + random.uniform(0, 1), 60.0)
                time.sleep(delay)
                continue
            return None, str(e), chat
    
    return None, "Max retries exceeded", chat