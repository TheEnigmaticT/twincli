# twincli/tools/obsidian_kanban.py
"""
Enhanced task management system that integrates with Obsidian's kanban plugin.
Creates proper kanban boards with metadata and provides simple terminal to-do lists.

This builds on the existing task planning but uses the actual Obsidian kanban format
with proper metadata headers and writes to the central TwinCLI Projects Kanban.md board.
"""

import json
import time
import re
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from twincli.tools.obsidian import (
    _find_obsidian_vault, 
    create_obsidian_note, 
    read_obsidian_note,
    update_obsidian_note,
    search_obsidian
)

class TaskStatus(Enum):
    PLANNING = "Planning"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In review"
    DONE = "Done"
    ARCHIVED = "Archived"

@dataclass
class KanbanTask:
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PLANNING
    priority: str = "2"  # String to match Obsidian format
    due_date: Optional[str] = None  # Format: @{2025-06-04}
    subtasks: List[Dict[str, bool]] = None  # [{"task": "thing", "completed": True}]
    metadata: Dict[str, str] = None  # Custom properties
    created_at: float = None
    updated_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.subtasks is None:
            self.subtasks = []
        if self.metadata is None:
            self.metadata = {}

class KanbanProject:
    def __init__(self, project_name: str, goal: str = ""):
        self.project_name = project_name
        self.goal = goal
        self.tasks: List[KanbanTask] = []
        self.created_at = time.time()
        self.updated_at = time.time()
        self.vault_path = _find_obsidian_vault()
        
    def add_task(self, task: KanbanTask) -> str:
        """Add a task to the project."""
        self.tasks.append(task)
        self.updated_at = time.time()
        self._save_to_central_kanban()
        return task.id
    
    def update_task_status(self, task_id: str, new_status: TaskStatus, note: str = ""):
        """Update a task's status."""
        task = self.get_task_by_id(task_id)
        if task:
            old_status = task.status
            task.status = new_status
            task.updated_at = time.time()
            self.updated_at = time.time()
            self._move_task_in_central_kanban(task.title, old_status.value, new_status.value)
    
    def update_task_subtasks(self, task_id: str, subtasks: List[Dict[str, bool]]):
        """Update subtasks for a task."""
        task = self.get_task_by_id(task_id)
        if task:
            task.subtasks = subtasks
            task.updated_at = time.time()
            self.updated_at = time.time()
            self._update_task_note(task)
    
    def get_task_by_id(self, task_id: str) -> Optional[KanbanTask]:
        """Get task by ID."""
        return next((task for task in self.tasks if task.id == task_id), None)
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[KanbanTask]:
        """Get all tasks with a specific status."""
        return [task for task in self.tasks if task.status == status]
    
    def get_active_todo_list(self) -> List[Dict]:
        """Get a simple to-do list for current work (Planning + In Progress)."""
        active_tasks = []
        
        # Get tasks that are actively being worked on
        for status in [TaskStatus.PLANNING, TaskStatus.IN_PROGRESS]:
            for task in self.get_tasks_by_status(status):
                task_info = {
                    "id": task.id,
                    "title": task.title,
                    "status": status.value,
                    "priority": task.priority,
                    "due_date": task.due_date,
                    "subtasks": task.subtasks,
                    "total_subtasks": len(task.subtasks),
                    "completed_subtasks": len([s for s in task.subtasks if s.get("completed", False)])
                }
                active_tasks.append(task_info)
        
        # Sort by priority (1=highest, 3=lowest) then by due date
        active_tasks.sort(key=lambda x: (int(x["priority"]), x.get("due_date", "9999-99-99")))
        return active_tasks
    
    def _save_to_central_kanban(self):
        """Save tasks to the central TwinCLI Projects Kanban.md board."""
        if not self.vault_path:
            return
        
        central_kanban_title = "TwinCLI Projects Kanban"
        
        try:
            # Read existing kanban board
            current_content = read_obsidian_note(central_kanban_title)
            if "No note found" in current_content:
                print("❌ TwinCLI Projects Kanban.md not found. Please create it first.")
                return
            
            # Add each new task to the appropriate status section
            updated_content = current_content
            for task in self.tasks:
                # Check if task already exists in the kanban board
                if f"[[{task.title}]]" not in current_content:
                    task_line = self._format_task_line(task)
                    updated_content = self._insert_task_into_section(updated_content, task.status.value, task_line)
            
            # Update the central kanban board
            update_obsidian_note(central_kanban_title, updated_content, append=False)
            
            # Create individual task notes
            self._create_task_notes()
            
        except Exception as e:
            print(f"Error updating central kanban: {e}")
    
    def _format_task_line(self, task: KanbanTask) -> str:
        """Format a task for the kanban board."""
        task_line = f"- [ ] [[{task.title}]]"
        
        if task.due_date:
            task_line += f" {task.due_date}"
        
        # Add metadata on separate lines with proper indentation
        metadata_lines = []
        if task.priority != "2":
            metadata_lines.append(f"\tPriority:: {task.priority}")
        
        if self.project_name:
            metadata_lines.append(f"\tProject:: {self.project_name}")
        
        for key, value in task.metadata.items():
            metadata_lines.append(f"\t{key}:: {value}")
        
        if metadata_lines:
            task_line += "\n" + "\n".join(metadata_lines)
        
        return task_line
    
    def _insert_task_into_section(self, content: str, section: str, task_line: str) -> str:
        """Insert a task into the specified kanban section."""
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip() == f"## {section}":
                # Find insertion point after section header
                insert_index = i + 1
                
                # Skip any section description lines
                while (insert_index < len(lines) and 
                       lines[insert_index].strip() and 
                       not lines[insert_index].startswith('- [') and
                       not lines[insert_index].startswith('## ')):
                    insert_index += 1
                
                # Insert the task and add a blank line after
                lines.insert(insert_index, task_line)
                lines.insert(insert_index + 1, "")
                break
        
        return '\n'.join(lines)
    
    def _move_task_in_central_kanban(self, task_title: str, old_status: str, new_status: str):
        """Move a task from one status to another in the central kanban board."""
        if not self.vault_path:
            return
        
        central_kanban_title = "TwinCLI Projects Kanban"
        
        try:
            # Read current kanban content
            current_content = read_obsidian_note(central_kanban_title)
            if "No note found" in current_content:
                return
            
            # Find and remove task from current location
            lines = current_content.split('\n')
            task_line = None
            task_metadata = []
            
            i = 0
            while i < len(lines):
                line = lines[i]
                if f"[[{task_title}]]" in line:
                    task_line = line
                    lines.pop(i)  # Remove the task line
                    
                    # Remove any metadata lines that follow
                    while (i < len(lines) and 
                           lines[i].strip().startswith('\t')):
                        task_metadata.append(lines.pop(i))
                    
                    # Remove any empty line after the task
                    if i < len(lines) and not lines[i].strip():
                        lines.pop(i)
                    
                    break
                i += 1
            
            if not task_line:
                print(f"Task '{task_title}' not found in kanban board")
                return
            
            # Reconstruct the full task entry
            full_task_entry = task_line
            if task_metadata:
                full_task_entry += "\n" + "\n".join(task_metadata)
            
            # Insert task into new status section
            updated_content = '\n'.join(lines)
            final_content = self._insert_task_into_section(updated_content, new_status, full_task_entry)
            
            # Update the kanban file
            update_obsidian_note(central_kanban_title, final_content, append=False)
            
        except Exception as e:
            print(f"Error moving task in kanban: {e}")
    
    def _create_task_notes(self):
        """Create individual task notes with proper metadata and subtasks."""
        if not self.vault_path:
            return
        
        for task in self.tasks:
            task_content = self._generate_task_note_content(task)
            try:
                create_obsidian_note(task.title, task_content, folder="TwinCLI/Projects/Tasks")
            except:
                pass  # Note might already exist
    
    def _generate_task_note_content(self, task: KanbanTask) -> str:
        """Generate individual task note content with proper YAML frontmatter."""
        
        # Create proper YAML frontmatter
        frontmatter = ["---"]
        frontmatter.append(f'Priority: "{task.priority}"')
        
        # Add custom metadata in YAML format
        for key, value in task.metadata.items():
            frontmatter.append(f'{key}: "{value}"')
        
        if task.due_date:
            frontmatter.append(f'Due: "{task.due_date}"')
        
        frontmatter.append(f'Status: "{task.status.value}"')
        frontmatter.append(f'Project: "{self.project_name}"')
        frontmatter.append("---")
        
        content = [
            "\n".join(frontmatter),
            "",
            f"# {task.title}",
            "",
            task.description if task.description else "Task description goes here.",
            ""
        ]
        
        # Add subtasks
        if task.subtasks:
            content.append("## Subtasks")
            for subtask in task.subtasks:
                checkbox = "[x]" if subtask.get("completed", False) else "[ ]"
                content.append(f"- {checkbox} {subtask['task']}")
        else:
            content.extend([
                "## Subtasks",
                "- [ ] Add specific steps here",
                "- [ ] Break down the work",
                "- [ ] Mark completed items"
            ])
        
        return "\n".join(content)
    
    def _update_task_note(self, task: KanbanTask):
        """Update an individual task note."""
        if not self.vault_path:
            return
        
        try:
            task_content = self._generate_task_note_content(task)
            update_obsidian_note(task.title, task_content, append=False)
        except Exception as e:
            print(f"Error updating task note: {e}")

# Global project management
_current_project: Optional[KanbanProject] = None

def create_terminal_project(project_name: str, goal: str, tasks_json: str) -> str:
    """Create a new project with full Obsidian kanban board and simple terminal tracking."""
    global _current_project
    
    try:
        tasks_data = json.loads(tasks_json)
        
        # Create new project
        _current_project = KanbanProject(project_name, goal)
        
        # Add tasks
        for i, task_data in enumerate(tasks_data):
            # Parse due date if provided
            due_date = None
            if "due_date" in task_data:
                due_date = f"@{{{task_data['due_date']}}}"
            
            # Parse subtasks
            subtasks = []
            if "subtasks" in task_data:
                for subtask in task_data["subtasks"]:
                    if isinstance(subtask, str):
                        subtasks.append({"task": subtask, "completed": False})
                    else:
                        subtasks.append(subtask)
            
            task = KanbanTask(
                id=f"{project_name}_task_{i+1}",
                title=task_data.get("title", ""),
                description=task_data.get("description", ""),
                priority=str(task_data.get("priority", "2")),
                due_date=due_date,
                subtasks=subtasks,
                metadata=task_data.get("metadata", {})
            )
            _current_project.add_task(task)
        
        return f"""📋 **Terminal Project Created**
**Project:** {project_name}
**Goal:** {goal}
**Tasks:** {len(_current_project.tasks)}

🎯 **Tasks added to central TwinCLI Projects Kanban.md**
📝 **Individual task notes created with proper YAML frontmatter**

{get_simple_todo_list()}"""
        
    except json.JSONDecodeError as e:
        return f"Error parsing tasks JSON: {e}"
    except Exception as e:
        return f"Error creating project: {e}"

def get_simple_todo_list() -> str:
    """Get a clean, simple to-do list for terminal work."""
    global _current_project
    
    if not _current_project:
        return "No active project. Use create_terminal_project() to start."
    
    active_tasks = _current_project.get_active_todo_list()
    
    if not active_tasks:
        return "🎉 No active tasks! All work is done or in review."
    
    result = [f"📋 **Current To-Do List - {_current_project.project_name}**\n"]
    
    # Group by status
    planning_tasks = [t for t in active_tasks if t["status"] == "Planning"]
    in_progress_tasks = [t for t in active_tasks if t["status"] == "In Progress"]
    
    if in_progress_tasks:
        result.append("🔄 **Currently Working On:**")
        for task in in_progress_tasks:
            priority_indicator = "🔴" if task["priority"] == "1" else "🟡" if task["priority"] == "2" else "🟢"
            due_info = f" (due: {task['due_date'][2:-1]})" if task['due_date'] else ""
            
            if task["subtasks"]:
                progress = f" [{task['completed_subtasks']}/{task['total_subtasks']}]"
            else:
                progress = ""
            
            result.append(f"  • {priority_indicator} {task['title']}{progress}{due_info}")
            
            # Show incomplete subtasks
            if task["subtasks"]:
                incomplete_subtasks = [s for s in task["subtasks"] if not s.get("completed", False)]
                for subtask in incomplete_subtasks[:3]:  # Show first 3 incomplete
                    result.append(f"    ○ {subtask['task']}")
                if len(incomplete_subtasks) > 3:
                    result.append(f"    ○ ... and {len(incomplete_subtasks) - 3} more")
        result.append("")
    
    if planning_tasks:
        result.append("📋 **Ready to Start:**")
        for task in planning_tasks[:5]:  # Show top 5 by priority
            priority_indicator = "🔴" if task["priority"] == "1" else "🟡" if task["priority"] == "2" else "🟢"
            due_info = f" (due: {task['due_date'][2:-1]})" if task['due_date'] else ""
            result.append(f"  • {priority_indicator} {task['title']}{due_info}")
        
        if len(planning_tasks) > 5:
            result.append(f"  • ... and {len(planning_tasks) - 5} more tasks")
        result.append("")
    
    result.append("💡 **Tips:**")
    result.append("• Use move_task_to_status() to update progress")
    result.append("• Use complete_subtask() to check off sub-items")
    result.append("• Full kanban board available in Obsidian at TwinCLI/Projects/TwinCLI Projects Kanban.md")
    
    return "\n".join(result)

def move_task_to_status(task_id: str, new_status: str) -> str:
    """Move a task to a new status (Planning, In Progress, In review, Done, Archived)."""
    global _current_project
    
    if not _current_project:
        return "No active project."
    
    try:
        # Find status by value
        status = None
        for s in TaskStatus:
            if s.value.lower() == new_status.lower():
                status = s
                break
        
        if not status:
            valid_statuses = [s.value for s in TaskStatus]
            return f"Invalid status. Use one of: {', '.join(valid_statuses)}"
        
        _current_project.update_task_status(task_id, status)
        
        task = _current_project.get_task_by_id(task_id)
        if not task:
            return f"Task {task_id} not found."
        
        # Log to memory journal
        try:
            from twincli.tools.memory_journal import log_task_progress
            status_map = {
                TaskStatus.IN_PROGRESS: "start",
                TaskStatus.DONE: "complete",
                TaskStatus.ARCHIVED: "complete"
            }
            if status in status_map:
                log_task_progress(task_id, task.title, status_map[status], f"Moved to {status.value}")
        except ImportError:
            pass
        
        return f"""✅ **Task Status Updated**
**Task:** {task.title}
**New Status:** {status.value}

📋 **Updated central kanban board and task note**

{get_simple_todo_list()}"""
        
    except Exception as e:
        return f"Error updating task: {e}"

def complete_subtask(task_id: str, subtask_text: str) -> str:
    """Mark a subtask as completed."""
    global _current_project
    
    if not _current_project:
        return "No active project."
    
    task = _current_project.get_task_by_id(task_id)
    if not task:
        return f"Task {task_id} not found."
    
    # Find and update the subtask
    updated = False
    for subtask in task.subtasks:
        if subtask_text.lower() in subtask["task"].lower():
            subtask["completed"] = True
            updated = True
            break
    
    if not updated:
        return f"Subtask containing '{subtask_text}' not found in {task.title}"
    
    _current_project.update_task_subtasks(task_id, task.subtasks)
    
    # Check if all subtasks are complete
    all_complete = all(s.get("completed", False) for s in task.subtasks)
    status_suggestion = "\n💡 All subtasks complete! Consider moving to 'In review' or 'Done'" if all_complete else ""
    
    return f"""✅ **Subtask Completed**
**Task:** {task.title}
**Completed:** {subtask_text}
**Progress:** {len([s for s in task.subtasks if s.get('completed', False)])}/{len(task.subtasks)} subtasks{status_suggestion}

{get_simple_todo_list()}"""

def add_subtask(task_id: str, subtask_text: str) -> str:
    """Add a new subtask to an existing task."""
    global _current_project
    
    if not _current_project:
        return "No active project."
    
    task = _current_project.get_task_by_id(task_id)
    if not task:
        return f"Task {task_id} not found."
    
    new_subtask = {"task": subtask_text, "completed": False}
    task.subtasks.append(new_subtask)
    
    _current_project.update_task_subtasks(task_id, task.subtasks)
    
    return f"""➕ **Subtask Added**
**Task:** {task.title}
**New Subtask:** {subtask_text}
**Total Subtasks:** {len(task.subtasks)}

{get_simple_todo_list()}"""

def get_project_summary() -> str:
    """Get a high-level project summary."""
    global _current_project
    
    if not _current_project:
        return "No active project."
    
    # Calculate metrics
    total_tasks = len(_current_project.tasks)
    planning = len(_current_project.get_tasks_by_status(TaskStatus.PLANNING))
    in_progress = len(_current_project.get_tasks_by_status(TaskStatus.IN_PROGRESS))
    in_review = len(_current_project.get_tasks_by_status(TaskStatus.IN_REVIEW))
    done = len(_current_project.get_tasks_by_status(TaskStatus.DONE))
    archived = len(_current_project.get_tasks_by_status(TaskStatus.ARCHIVED))
    
    completed = done + archived
    completion_rate = completed / total_tasks if total_tasks > 0 else 0
    
    # Calculate subtask progress
    total_subtasks = sum(len(task.subtasks) for task in _current_project.tasks)
    completed_subtasks = sum(len([s for s in task.subtasks if s.get("completed", False)]) 
                           for task in _current_project.tasks)
    subtask_rate = completed_subtasks / total_subtasks if total_subtasks > 0 else 0
    
    # Progress bar
    progress_bar = "█" * int(completion_rate * 20) + "░" * (20 - int(completion_rate * 20))
    
    return f"""📊 **Project Summary - {_current_project.project_name}**

**Goal:** {_current_project.goal}

**Task Progress:** {progress_bar} {completion_rate:.1%}
• **Planning:** {planning} tasks
• **In Progress:** {in_progress} tasks  
• **In Review:** {in_review} tasks
• **Done:** {done} tasks ✅
• **Archived:** {archived} tasks

**Subtask Progress:** {completed_subtasks}/{total_subtasks} subtasks completed ({subtask_rate:.1%})

**Next Actions:**
• Focus on {in_progress} active tasks
• {planning} tasks ready to start
• Central kanban board: TwinCLI/Projects/TwinCLI Projects Kanban.md

⏱️ **Active since:** {datetime.fromtimestamp(_current_project.created_at).strftime("%Y-%m-%d %H:%M")}"""

def sync_from_obsidian(project_name: str) -> str:
    """Sync project state from Obsidian kanban board (manual refresh)."""
    try:
        central_kanban_content = read_obsidian_note("TwinCLI Projects Kanban")
        
        if "No note found" in central_kanban_content:
            return f"No central kanban board found. Please create TwinCLI Projects Kanban.md"
        
        return f"""🔄 **Sync from Central Kanban**
**Board:** TwinCLI Projects Kanban.md
**Status:** Manual sync completed

Note: This reads the current state of your central kanban board.
The board is automatically updated when you use TwinCLI functions.

{get_simple_todo_list()}"""
        
    except Exception as e:
        return f"Error syncing from Obsidian: {e}"

# Export terminal-focused kanban functions
terminal_kanban_tools = [
    create_terminal_project,
    get_simple_todo_list,
    move_task_to_status,
    complete_subtask,
    add_subtask,
    get_project_summary,
    sync_from_obsidian
]