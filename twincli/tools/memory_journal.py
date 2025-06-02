# twincli/tools/memory_journal.py
import json
import time
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Set
import re

from twincli.tools.obsidian import (
    _find_obsidian_vault, 
    create_obsidian_note, 
    read_obsidian_note,
    search_obsidian
)

class WorkJournal:
    def __init__(self):
        self.vault_path = _find_obsidian_vault()
        self.journal_folder = "TwinCLI/Journal"
        self.today = date.today()
        self.today_str = self.today.strftime("%Y-%m-%d")
        self.current_session_id = f"session_{int(time.time())}"
        
    def get_todays_journal_path(self) -> str:
        """Get the path for today's journal note."""
        return f"{self.journal_folder}/{self.today_str}-TwinCLI-Work"
        
    def initialize_daily_journal(self) -> str:
        """Create or update today's journal note."""
        journal_title = f"{self.today_str}-TwinCLI-Work"
        
        # Check if today's journal already exists
        existing_content = ""
        try:
            existing_result = read_obsidian_note(journal_title)
            if "No note found" not in existing_result:
                # Extract existing content after the header
                lines = existing_result.split('\n')
                content_start = 0
                
                # Find where the actual session content starts
                for i, line in enumerate(lines):
                    if line.strip().startswith('## Session'):
                        content_start = i
                        break
                    # Also look for other entry patterns that might exist
                    elif line.strip().startswith('### ') or line.strip().startswith('#### '):
                        content_start = i
                        break
                
                if content_start > 0:
                    # Get the existing content and clean up any leading empty lines
                    session_lines = lines[content_start:]
                    # Remove leading empty lines
                    while session_lines and not session_lines[0].strip():
                        session_lines.pop(0)
                    # Remove trailing empty lines  
                    while session_lines and not session_lines[-1].strip():
                        session_lines.pop()
                    
                    if session_lines:  # Only add if there's actual content
                        existing_content = '\n'.join(session_lines)
        except Exception:
            pass
        
        # Create new journal template - no leading newlines in the template
        template_lines = [
            f"# TwinCLI Work Journal - {self.today_str}",
            "",
            "#twincli #work-journal #ai-assistant",
            "",
            f"**Date:** {self.today_str}",
            f"**Vault:** [[{Path(self.vault_path).name if self.vault_path else 'Unknown'}]]",
            "",
            "---",
            "",
            "## Quick Reference",
            "- Use `#task-planning` for planning sessions",
            "- Use `#completed` for finished tasks",
            "- Use `#research` for information gathering", 
            "- Use `#writing` for content creation",
            "- Use `#automation` for browser/system tasks",
            "- Use `#failed` for unsuccessful attempts",
            "",
            "---",
            ""
        ]
        
        # Add existing content or default session start
        if existing_content:
            template_lines.append(existing_content)
        else:
            template_lines.extend([
                f"## Session {self.current_session_id}",
                f"**Started:** {datetime.now().strftime('%H:%M')}"
            ])
        
        # Join without any leading empty lines
        template = '\n'.join(template_lines)
        
        result = create_obsidian_note(
            title=journal_title,
            content=template,
            folder=self.journal_folder
        )
        
        return f"📓 Daily journal initialized: {journal_title}\n{result}"
    
    def log_plan_creation(self, goal: str, tasks: List[Dict], plan_id: str) -> str:
        """Log a new task plan to today's journal."""
        timestamp = datetime.now().strftime("%H:%M")
        
        # Create task list for journal
        task_list = []
        for i, task in enumerate(tasks, 1):
            tools = f" `{', '.join(task.get('tools_needed', []))}`" if task.get('tools_needed') else ""
            task_list.append(f"   {i}. ⏳ {task['title']}{tools}")
        
        log_entry = f"""

### 🎯 New Plan Created - {timestamp}
**Goal:** {goal}  
**Plan ID:** `{plan_id}`  
**Tags:** #task-planning #new-plan

**Tasks:**
{chr(10).join(task_list)}

**Status:** Planning phase complete, ready to execute
"""
        
        return self._append_to_journal(log_entry)
    
    def log_task_start(self, task_id: str, task_title: str, description: str) -> str:
        """Log when a task starts."""
        timestamp = datetime.now().strftime("%H:%M")
        
        log_entry = f"""
#### 🔄 Started: {task_title} - {timestamp}
**Task ID:** `{task_id}`  
**Description:** {description}  
**Status:** In Progress
"""
        return self._append_to_journal(log_entry)
    
    def log_task_completion(self, task_id: str, task_title: str, result: str, success: bool = True) -> str:
        """Log task completion with results."""
        timestamp = datetime.now().strftime("%H:%M")
        status_emoji = "✅" if success else "❌"
        status_tag = "#completed" if success else "#failed"
        
        # Truncate very long results for readability
        display_result = result
        if len(result) > 300:
            display_result = result[:300] + f"\n... (truncated, full result: {len(result)} chars)"
        
        log_entry = f"""
#### {status_emoji} {'Completed' if success else 'Failed'}: {task_title} - {timestamp}
**Task ID:** `{task_id}`  
**Tags:** {status_tag}

**Result:**
{display_result}
"""
        return self._append_to_journal(log_entry)
    
    def log_thinking(self, context: str, thoughts: str) -> str:
        """Log AI reasoning and decision-making process."""
        timestamp = datetime.now().strftime("%H:%M")
        
        log_entry = f"""
#### 🧠 Thinking Process - {timestamp}
**Context:** {context}  
**Tags:** #reasoning #decision-making

**Analysis:**
{thoughts}
"""
        return self._append_to_journal(log_entry)
    
    def log_tool_usage(self, tool_name: str, purpose: str, result_summary: str) -> str:
        """Log when tools are used and their outcomes."""
        timestamp = datetime.now().strftime("%H:%M")
        
        log_entry = f"""
#### 🔧 Tool Used: {tool_name} - {timestamp}
**Purpose:** {purpose}  
**Result:** {result_summary}  
**Tags:** #tool-usage #{tool_name.replace('_', '-')}
"""
        return self._append_to_journal(log_entry)
    
    def _append_to_journal(self, content: str) -> str:
        """Append content to today's journal."""
        journal_title = f"{self.today_str}-TwinCLI-Work"
        
        try:
            # Read current content
            current_result = read_obsidian_note(journal_title)
            if "No note found" in current_result:
                # Initialize if doesn't exist
                self.initialize_daily_journal()
                current_result = read_obsidian_note(journal_title)
            
            # Extract just the content part (after "Path:" line)
            lines = current_result.split('\n')
            content_start = 0
            for i, line in enumerate(lines):
                if line.startswith('Path:'):
                    content_start = i + 2  # Skip path line and empty line
                    break
            
            if content_start > 0:
                current_content = '\n'.join(lines[content_start:])
            else:
                current_content = current_result
            
            # Append new content
            updated_content = current_content + content
            
            # Write back
            create_obsidian_note(
                title=journal_title,
                content=updated_content,
                folder=self.journal_folder
            )
            
            return f"📝 Logged to journal: {journal_title}"
            
        except Exception as e:
            return f"❌ Failed to log to journal: {e}"
    
    def get_recent_work_context(self, days: int = 3, max_entries: int = 10) -> str:
        """Get context from recent work to inform current decisions."""
        try:
            # Search for recent journal entries
            search_terms = [
                "TwinCLI-Work",
                "#completed",
                "#task-planning",
                "#research"
            ]
            
            context_parts = []
            for term in search_terms:
                results = search_obsidian(term)
                if "Found" in results and "notes containing" in results:
                    context_parts.append(f"**{term} Results:**\n{results[:500]}...\n")
            
            if not context_parts:
                return "No recent work context found in Obsidian."
            
            return f"""📚 **Recent Work Context (Last {days} days):**

{chr(10).join(context_parts)}

**Analysis:** Based on recent entries, I can see patterns in task types, successful approaches, and areas where I've struggled. This will inform my planning and execution."""
            
        except Exception as e:
            return f"❌ Could not retrieve work context: {e}"
    
    def analyze_work_patterns(self) -> str:
        """Analyze work patterns and provide insights."""
        try:
            # Search for different types of work
            patterns = {
                "completed_tasks": search_obsidian("#completed"),
                "failed_tasks": search_obsidian("#failed"), 
                "research_work": search_obsidian("#research"),
                "automation_work": search_obsidian("#automation"),
                "writing_work": search_obsidian("#writing")
            }
            
            analysis = ["🔍 **Work Pattern Analysis:**\n"]
            
            for pattern_type, results in patterns.items():
                if "Found" in results:
                    # Extract number of results
                    match = re.search(r'Found (\d+) notes', results)
                    count = match.group(1) if match else "unknown"
                    analysis.append(f"- **{pattern_type.replace('_', ' ').title()}:** {count} instances")
            
            analysis.append("\n**Insights:** This data helps me understand what types of tasks I handle well and where I might need to adjust my approach.")
            
            return "\n".join(analysis)
            
        except Exception as e:
            return f"❌ Could not analyze work patterns: {e}"

# Global work journal instance
_work_journal = WorkJournal()

def initialize_work_session() -> str:
    """Initialize today's work session and journal."""
    global _work_journal
    _work_journal = WorkJournal()  # Refresh with current date
    return _work_journal.initialize_daily_journal()

def log_plan_to_journal(goal: str, tasks_json: str, plan_id: str) -> str:
    """Log a new task plan to the work journal."""
    try:
        tasks = json.loads(tasks_json)
        return _work_journal.log_plan_creation(goal, tasks, plan_id)
    except Exception as e:
        return f"❌ Failed to log plan: {e}"

def log_task_progress(task_id: str, task_title: str, status: str, details: str = "") -> str:
    """Log task progress (start, complete, fail)."""
    if status == "start":
        return _work_journal.log_task_start(task_id, task_title, details)
    elif status == "complete":
        return _work_journal.log_task_completion(task_id, task_title, details, True)
    elif status == "fail":
        return _work_journal.log_task_completion(task_id, task_title, details, False)
    else:
        return f"❌ Unknown status: {status}"

def log_reasoning(context: str, thoughts: str) -> str:
    """Log AI thinking and decision-making process."""
    return _work_journal.log_thinking(context, thoughts)  # Was log_reasoning

def log_tool_action(tool_name: str, purpose: str, result_summary: str) -> str:
    """Log tool usage and outcomes."""
    return _work_journal.log_tool_usage(tool_name, purpose, result_summary)  # This looks correct

def get_work_context(days: int = 3) -> str:
    """Get recent work context to inform current decisions."""
    return _work_journal.get_recent_work_context(days)

def analyze_my_work_patterns() -> str:
    """Analyze work patterns from journal entries."""
    return _work_journal.analyze_work_patterns()

def get_todays_journal() -> str:
    """Get today's complete work journal."""
    journal_title = f"{_work_journal.today_str}-TwinCLI-Work"
    return read_obsidian_note(journal_title)

# Export the memory/journal functions
memory_tools = [
    initialize_work_session,
    log_plan_to_journal,
    log_task_progress,
    log_reasoning,
    log_tool_action,
    get_work_context,
    analyze_my_work_patterns,
    get_todays_journal
]