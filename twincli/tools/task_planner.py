# twincli/tools/task_planner.py
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class TaskStatus(Enum):
    PENDING = "⏳"
    IN_PROGRESS = "🔄"
    COMPLETED = "✅"
    FAILED = "❌"
    SKIPPED = "⏭️"

@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = None
    completed_at: Optional[float] = None
    tools_needed: List[str] = None
    dependencies: List[str] = None  # Task IDs this depends on
    result: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.tools_needed is None:
            self.tools_needed = []
        if self.dependencies is None:
            self.dependencies = []

class TaskPlan:
    def __init__(self, goal: str, plan_id: str = None):
        self.goal = goal
        self.plan_id = plan_id or f"plan_{int(time.time())}"
        self.tasks: List[Task] = []
        self.created_at = time.time()
        self.current_task_index = 0
        
    def add_task(self, title: str, description: str, tools_needed: List[str] = None, dependencies: List[str] = None) -> str:
        """Add a new task to the plan."""
        task_id = f"task_{len(self.tasks) + 1}"
        task = Task(
            id=task_id,
            title=title,
            description=description,
            tools_needed=tools_needed or [],
            dependencies=dependencies or []
        )
        self.tasks.append(task)
        return task_id
    
    def get_next_available_task(self) -> Optional[Task]:
        """Get the next task that can be executed (dependencies met)."""
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                if all(self.get_task_by_id(dep_id).status == TaskStatus.COMPLETED 
                       for dep_id in task.dependencies if self.get_task_by_id(dep_id)):
                    return task
        return None
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return next((task for task in self.tasks if task.id == task_id), None)
    
    def update_task_status(self, task_id: str, status: TaskStatus, result: str = None):
        """Update task status and result."""
        task = self.get_task_by_id(task_id)
        if task:
            task.status = status
            if result:
                task.result = result
            if status == TaskStatus.COMPLETED:
                task.completed_at = time.time()
    
    def get_progress_summary(self) -> Dict:
        """Get current progress summary."""
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        failed = sum(1 for task in self.tasks if task.status == TaskStatus.FAILED)
        in_progress = sum(1 for task in self.tasks if task.status == TaskStatus.IN_PROGRESS)
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": total - completed - failed - in_progress,
            "completion_rate": completed / total if total > 0 else 0
        }

# Global task plan storage
_current_plan: Optional[TaskPlan] = None
_plan_history: List[TaskPlan] = []

def create_task_plan(goal: str, tasks_json: str) -> str:
    """Create a new task plan with a goal and list of tasks.
    
    Args:
        goal: The overall goal or objective
        tasks_json: JSON string containing list of tasks with structure:
                   [{"title": str, "description": str, "tools_needed": [str], "dependencies": [str]}]
    
    Returns:
        String confirmation with plan summary
    """
    global _current_plan, _plan_history
    
    try:
        tasks_data = json.loads(tasks_json)
        
        # Save previous plan to history
        if _current_plan:
            _plan_history.append(_current_plan)
        
        # Create new plan
        _current_plan = TaskPlan(goal)
        
        # Add tasks
        for task_data in tasks_data:
            _current_plan.add_task(
                title=task_data.get("title", ""),
                description=task_data.get("description", ""),
                tools_needed=task_data.get("tools_needed", []),
                dependencies=task_data.get("dependencies", [])
            )        
           
        # For synthesis tasks, add a reminder about deliverables
        for task_data in tasks_data:
            if "synthesize" in task_data.get("title", "").lower():
                if "deliverable" not in task_data.get("description", ""):
                    task_data["description"] += "\n\nIMPORTANT: This task must produce a deliverable file using save_analysis_report()."

        # Log to Obsidian journal
        try:
            from twincli.tools.memory_journal import log_plan_to_journal
            log_plan_to_journal(goal, tasks_json, _current_plan.plan_id)
        except ImportError:
            pass  # Memory journal not available
        
        return f"""📋 **New Task Plan Created**
**Goal:** {goal}
**Plan ID:** {_current_plan.plan_id}
**Total Tasks:** {len(_current_plan.tasks)}

{display_current_plan()}"""
        
    except json.JSONDecodeError as e:
        return f"Error parsing tasks JSON: {e}"
    except Exception as e:
        return f"Error creating task plan: {e}"

def display_current_plan() -> str:
    """Display the current task plan with progress."""
    global _current_plan
    
    if not _current_plan:
        return "No active task plan. Use create_task_plan() to start planning."
    
    progress = _current_plan.get_progress_summary()
    
    # Header
    result = [
        f"🎯 **Current Plan: {_current_plan.goal}**",
        f"📊 Progress: {progress['completed']}/{progress['total']} tasks completed ({progress['completion_rate']:.1%})",
        ""
    ]
    
    # Task list
    result.append("**Tasks:**")
    for i, task in enumerate(_current_plan.tasks, 1):
        status_icon = task.status.value
        
        # Add dependency info
        dep_info = ""
        if task.dependencies:
            dep_status = []
            for dep_id in task.dependencies:
                dep_task = _current_plan.get_task_by_id(dep_id)
                if dep_task:
                    dep_status.append(f"{dep_task.title} {dep_task.status.value}")
            if dep_status:
                dep_info = f" (depends on: {', '.join(dep_status)})"
        
        # Add tools info
        tools_info = ""
        if task.tools_needed:
            tools_info = f" [tools: {', '.join(task.tools_needed)}]"
        
        result.append(f"{i}. {status_icon} **{task.title}**{dep_info}{tools_info}")
        result.append(f"   {task.description}")
        
        if task.result:
            result.append(f"   📝 Result: {task.result[:100]}{'...' if len(task.result) > 100 else ''}")
        
        result.append("")
    
    return "\n".join(result)

def get_next_task() -> str:
    """Get the next available task to work on."""
    global _current_plan
    
    if not _current_plan:
        return "No active task plan. Create a plan first."
    
    next_task = _current_plan.get_next_available_task()
    if not next_task:
        progress = _current_plan.get_progress_summary()
        if progress['completed'] == progress['total']:
            return "🎉 All tasks completed! Plan finished successfully."
        else:
            return "No available tasks. Check if there are dependency issues or all tasks are completed."
    
    return f"""🔄 **Next Task Ready**
**Task:** {next_task.title}
**ID:** {next_task.id}
**Description:** {next_task.description}
**Tools Needed:** {', '.join(next_task.tools_needed) if next_task.tools_needed else 'None specified'}
**Status:** {next_task.status.value}"""

def start_task(task_id: str) -> str:
    """Mark a task as started/in progress."""
    global _current_plan
    
    if not _current_plan:
        return "No active task plan."
    
    task = _current_plan.get_task_by_id(task_id)
    if not task:
        return f"Task {task_id} not found."
    
    # Check dependencies
    for dep_id in task.dependencies:
        dep_task = _current_plan.get_task_by_id(dep_id)
        if dep_task and dep_task.status != TaskStatus.COMPLETED:
            return f"Cannot start {task_id}. Dependency {dep_id} ({dep_task.title}) is not completed."
    
    _current_plan.update_task_status(task_id, TaskStatus.IN_PROGRESS)
    
    # Log to journal
    try:
        from twincli.tools.memory_journal import log_task_progress
        log_task_progress(task_id, task.title, "start", task.description)
    except ImportError:
        pass
    
    return f"🔄 Started task: {task.title}"

def complete_task(task_id: str, result: str = None) -> str:
    """Mark a task as completed with optional result."""
    global _current_plan
    
    if not _current_plan:
        return "No active task plan."
    
    task = _current_plan.get_task_by_id(task_id)
    if not task:
        return f"Task {task_id} not found."
    
    _current_plan.update_task_status(task_id, TaskStatus.COMPLETED, result)
    
    # Log to journal
    try:
        from twincli.tools.memory_journal import log_task_progress
        log_task_progress(task_id, task.title, "complete", result or "Task completed successfully")
    except ImportError:
        pass
    
    progress = _current_plan.get_progress_summary()
    return f"""✅ **Task Completed:** {task.title}
{f'📝 **Result:** {result}' if result else ''}
📊 **Progress:** {progress['completed']}/{progress['total']} tasks completed"""

def fail_task(task_id: str, reason: str = None) -> str:
    """Mark a task as failed with optional reason."""
    global _current_plan
    
    if not _current_plan:
        return "No active task plan."
    
    task = _current_plan.get_task_by_id(task_id)
    if not task:
        return f"Task {task_id} not found."
    
    _current_plan.update_task_status(task_id, TaskStatus.FAILED, reason)
    return f"❌ **Task Failed:** {task.title}\n{f'📝 **Reason:** {reason}' if reason else ''}"

def get_plan_summary() -> str:
    """Get a summary of the current plan's progress."""
    global _current_plan
    
    if not _current_plan:
        return "No active task plan."
    
    progress = _current_plan.get_progress_summary()
    
    # Time elapsed
    elapsed_time = time.time() - _current_plan.created_at
    elapsed_minutes = elapsed_time / 60
    
    # Estimate completion
    if progress['completed'] > 0:
        avg_time_per_task = elapsed_time / progress['completed']
        remaining_tasks = progress['total'] - progress['completed']
        estimated_remaining = (remaining_tasks * avg_time_per_task) / 60
        eta_text = f"🕒 **ETA:** ~{estimated_remaining:.1f} minutes remaining"
    else:
        eta_text = "🕒 **ETA:** Cannot estimate (no completed tasks yet)"
    
    return f"""📊 **Plan Summary**
**Goal:** {_current_plan.goal}
**Total Tasks:** {progress['total']}
**Completed:** {progress['completed']} ✅
**In Progress:** {progress['in_progress']} 🔄  
**Failed:** {progress['failed']} ❌
**Pending:** {progress['pending']} ⏳
**Completion Rate:** {progress['completion_rate']:.1%}
**Time Elapsed:** {elapsed_minutes:.1f} minutes
{eta_text}"""

def clear_current_plan() -> str:
    """Clear the current plan and move it to history."""
    global _current_plan, _plan_history
    
    if not _current_plan:
        return "No active plan to clear."
    
    plan_goal = _current_plan.goal
    _plan_history.append(_current_plan)
    _current_plan = None
    
    return f"📝 Plan '{plan_goal}' moved to history. Ready for new plan."

# Export all the task management functions
task_management_tools = [
    create_task_plan,
    display_current_plan,
    get_next_task,
    start_task,
    complete_task,
    fail_task,
    get_plan_summary,
    clear_current_plan
]