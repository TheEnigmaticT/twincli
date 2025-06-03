# twincli/display.py
"""
Enhanced display manager for TwinCLI with clear visual separation of thinking vs. actions.
Handles all terminal output formatting, user input, and visual feedback.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.columns import Columns
from rich.text import Text
from rich.prompt import Confirm


class TwinCLIDisplay:
    """Enhanced display manager for TwinCLI with clear thinking vs. action separation."""
    
    def __init__(self, console: Console):
        self.console = console
        self.current_workflow_stage = None
        
    def thinking(self, message: str):
        """Display AI thinking/reasoning - clearly separated from actions."""
        self.console.print(f"[dim italic]🤔 {message}[/dim italic]")
    
    def planning_step(self, step: str):
        """Display planning phase activities."""
        self.current_workflow_stage = "planning"
        self.console.print(f"[blue]📋 PLANNING[/blue] [bold]{step}[/bold]")
    
    def execution_step(self, step: str):
        """Display execution phase activities."""
        self.current_workflow_stage = "execution"
        self.console.print(f"[green]⚡ EXECUTING[/green] [bold]{step}[/bold]")
    
    def review_step(self, step: str):
        """Display review phase activities."""
        self.current_workflow_stage = "review"
        self.console.print(f"[yellow]👀 REVIEWING[/yellow] [bold]{step}[/bold]")
    
    def tool_action(self, tool_name: str, purpose: str, args_preview: str = ""):
        """Display tool usage with clear purpose."""
        args_text = f" [dim]({args_preview})[/dim]" if args_preview else ""
        self.console.print(f"[bright_green]🔧 {tool_name}[/bright_green]{args_text}")
        self.console.print(f"[dim]   └─ {purpose}[/dim]")
    
    def tool_result(self, result: str, success: bool = True):
        """Display tool results with auto-collapse for large content."""
        status = "✓" if success else "✗"
        color = "green" if success else "red"
        
        # Filter out debug statements from tool results
        filtered_result = self._filter_debug_statements(result)
        
        if len(filtered_result) > 800:  # Auto-collapse large results
            preview = filtered_result[:300] + "..."
            self.console.print(f"[{color}]{status}[/{color}] [dim]Result ({len(filtered_result)} chars):[/dim]")
            self.console.print(Panel(preview, title="Preview", border_style="dim", padding=(0, 1)))
            
            if Confirm.ask("[dim]Show full result?[/dim]", default=False):
                self.console.print(Panel(filtered_result, title="Full Result", border_style=color, padding=(0, 1)))
        else:
            self.console.print(f"[{color}]{status}[/{color}] [bold]Result:[/bold]")
            self.console.print(Panel(filtered_result, border_style=color, padding=(0, 1)))
    
    def _filter_debug_statements(self, text: str) -> str:
        """Filter out debug statements from tool output."""
        if not text:
            return text
        
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Skip debug lines
            if (line.strip().startswith('[DEBUG]') or 
                line.strip().startswith('DEBUG:') or
                line.strip().startswith('print(f"[DEBUG]')):
                continue
            # Skip empty lines that result from debug filtering
            if not line.strip() and len(filtered_lines) > 0 and not filtered_lines[-1].strip():
                continue
            filtered_lines.append(line)
        
        # Clean up any trailing empty lines
        while filtered_lines and not filtered_lines[-1].strip():
            filtered_lines.pop()
        
        return '\n'.join(filtered_lines)
    
    def large_content(self, title: str, content: str, threshold: int = 1000):
        """Handle large content blocks with auto-collapse."""
        if len(content) > threshold:
            preview = content[:400] + "\n... (content truncated)"
            self.console.print(f"[bold]{title}[/bold] [dim]({len(content)} chars)[/dim]")
            self.console.print(Panel(preview, border_style="dim", padding=(0, 1)))
            
            if len(content) > 2000:
                self.console.print("[dim italic]Large content auto-collapsed for readability[/dim italic]")
        else:
            self.console.print(f"[bold]{title}:[/bold]")
            self.console.print(content)
    
    def status_update(self, message: str, status_type: str = "info"):
        """Display status updates with appropriate styling."""
        colors = {
            "info": "blue",
            "success": "green", 
            "warning": "yellow",
            "error": "red"
        }
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️", 
            "error": "❌"
        }
        
        color = colors.get(status_type, "blue")
        icon = icons.get(status_type, "ℹ️")
        
        self.console.print(f"[{color}]{icon} {message}[/{color}]")
    
    def project_progress_table(self, project_data: dict):
        """Display project progress as a formatted table."""
        if not project_data:
            return
            
        table = Table(title=f"📋 Project: {project_data.get('name', 'Unknown')}")
        table.add_column("Task", style="white", width=30)
        table.add_column("Status", style="cyan", width=15)
        table.add_column("Progress", style="green", width=10)
        table.add_column("Priority", style="yellow", width=8)
        
        tasks = project_data.get('tasks', [])
        for task in tasks:
            status_emoji = {
                "Planning": "📋",
                "In Progress": "🔄", 
                "In review": "👀",
                "Done": "✅",
                "Archived": "📦"
            }.get(task.get('status', ''), "❓")
            
            priority_color = {
                "1": "[red]🔴[/red]",
                "2": "[yellow]🟡[/yellow]", 
                "3": "[green]🟢[/green]"
            }.get(str(task.get('priority', '2')), "⚪")
            
            progress = ""
            if 'subtasks' in task:
                completed = task.get('completed_subtasks', 0)
                total = task.get('total_subtasks', 0)
                if total > 0:
                    progress = f"{completed}/{total}"
            
            table.add_row(
                task.get('title', 'Untitled'),
                f"{status_emoji} {task.get('status', 'Unknown')}",
                progress,
                priority_color
            )
        
        self.console.print(table)
    
    def workflow_checklist(self, items: list, title: str = "Workflow Progress"):
        """Display a workflow checklist with clear progress indicators."""
        tree = Tree(f"[bold]{title}[/bold]")
        
        for item in items:
            status = item.get('status', 'pending')
            name = item.get('name', 'Unknown step')
            
            if status == 'completed':
                tree.add(f"[green]✅ {name}[/green]")
            elif status == 'in_progress':
                tree.add(f"[yellow]🔄 {name}[/yellow]")
            elif status == 'failed':
                tree.add(f"[red]❌ {name}[/red]")
            else:
                tree.add(f"[dim]⏳ {name}[/dim]")
        
        self.console.print(tree)
    
    def session_header(self, session_info: dict):
        """Display session information header."""
        columns = []
        
        # Session info
        session_text = Text()
        session_text.append("Session: ", style="dim")
        session_text.append(session_info.get('id', 'Unknown'), style="bold cyan")
        columns.append(Panel(session_text, title="Current Session", border_style="cyan", width=25))
        
        # Active project
        project_text = Text()
        project_text.append("Project: ", style="dim")
        project_name = session_info.get('active_project', 'None')
        project_text.append(project_name, style="bold green" if project_name != 'None' else "dim")
        columns.append(Panel(project_text, title="Active Project", border_style="green", width=25))
        
        # Workflow stage
        stage_text = Text()
        stage_text.append("Stage: ", style="dim")
        stage = self.current_workflow_stage or "Ready"
        stage_text.append(stage.title(), style="bold yellow")
        columns.append(Panel(stage_text, title="Workflow Stage", border_style="yellow", width=25))
        
        self.console.print(Columns(columns, equal=True))
        self.console.print()
    
    def usage_summary_table(self, summary: dict):
        """Display token usage summary as a formatted table."""
        table = Table(title="💰 Session Usage Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Input tokens", f"{summary['total_input_tokens']:,}")
        table.add_row("Output tokens", f"{summary['total_output_tokens']:,}")
        table.add_row("Total tokens", f"{summary['total_tokens']:,}")
        table.add_row("Total cost", f"${summary['total_cost']:.6f}")
        table.add_row("Conversations", f"{summary['conversation_count']}")
        table.add_row("Avg cost/min", f"${summary['cost_per_minute']:.6f}")
        
        self.console.print(table)
    
    def startup_banner(self, tools_count: int, functions_count: int):
        """Display the startup banner with system information."""
        self.console.print(Panel.fit(
            "[bold blue]TwinCLI[/bold blue] [dim]—[/dim] [italic]Enhanced Gemini 2.5 Flash Interface[/italic]\n"
            "[dim]Enhanced with visual feedback, auto-collapse, and structured workflows[/dim]",
            border_style="blue"
        ))
        
        self.console.print(f"[dim]🔧 {functions_count} tools loaded | {tools_count} functions available[/dim]\n")
    
    def final_session_summary(self, summary: dict):
        """Display final session summary on exit."""
        self.console.print(f"\n[dim]Session Summary:[/dim]")
        self.console.print(f"[dim]Total tokens: {summary['total_tokens']:,} ({summary['total_input_tokens']:,} in, {summary['total_output_tokens']:,} out)[/dim]")
        self.console.print(f"[dim]Total cost: ${summary['total_cost']:.4f}[/dim]")
        self.console.print(f"[dim]Conversations: {summary['conversation_count']} over {summary['elapsed_minutes']:.1f} minutes[/dim]")


def get_enhanced_multiline_input(console: Console) -> str:
    """Enhanced multi-line input with better visual indicators."""
    lines = []
    
    console.print("[bold cyan]You >[/bold cyan] ", end="")
    
    while True:
        try:
            if not lines:
                line = input().strip()
            else:
                # Better continuation indicator
                line = input("     │ ").strip()
            
            if line.endswith("\\"):
                lines.append(line[:-1])
                continue
            else:
                lines.append(line)
                break
                
        except EOFError:
            if lines:
                break
            else:
                console.print("\n[yellow]Exiting TwinCLI.[/yellow]")
                return "exit"
        except KeyboardInterrupt:
            console.print("\n[yellow]Input cancelled.[/yellow]")
            return ""
    
    full_input = "\n".join(lines).strip()
    
    # Show preview for very long inputs
    if len(full_input) > 500:
        preview = full_input[:200] + "..."
        console.print(f"[dim]Input received ({len(full_input)} chars): {preview}[/dim]")
        console.print("[dim italic]↳ Full input captured, showing preview[/dim italic]")
    
    return full_input


def format_function_args_preview(args: dict) -> str:
    """Create a concise preview of function arguments for display."""
    if not args:
        return ""
    
    preview_parts = []
    for key, value in args.items():
        if isinstance(value, str) and len(value) > 50:
            preview_parts.append(f"{key}='{value[:30]}...'")
        else:
            preview_parts.append(f"{key}={repr(value)}")
    
    preview = ", ".join(preview_parts)
    return preview[:100] + "..." if len(preview) > 100 else preview


def get_current_session_info() -> dict:
    """Get current session information for display."""
    session_info = {
        'id': f"session_{int(time.time())}",
        'active_project': 'None',
        'start_time': datetime.now().strftime("%H:%M")
    }
    
    # Try to get active project info
    try:
        from twincli.tools.obsidian_kanban import _current_project
        if _current_project:
            session_info['active_project'] = _current_project.project_name
    except ImportError:
        # obsidian_kanban not available
        pass
    except Exception:
        # Other errors getting project info
        pass
    
    return session_info


def get_tool_purpose_context(function_name: str, function_args: dict) -> str:
    """Determine the purpose/context for better tool display."""
    purpose = "Executing function"
    
    if function_name in ['search_web', 'intelligent_search']:
        query = function_args.get('query', 'unknown')
        purpose = f"Searching for: {query}"
    elif function_name in ['create_obsidian_note', 'update_obsidian_note']:
        title = function_args.get('title', 'unknown')
        purpose = f"Managing note: {title}"
    elif function_name in ['create_task_plan', 'start_task']:
        goal_or_id = function_args.get('goal', function_args.get('task_id', 'unknown'))
        purpose = f"Task management: {goal_or_id}"
    elif function_name in ['smart_git_command']:
        command = function_args.get('command', 'unknown')
        purpose = f"Git operation: {command}"
    elif function_name in ['write_file', 'read_file']:
        file_path = function_args.get('file_path', function_args.get('path', 'unknown'))
        action = "Writing to" if function_name == 'write_file' else "Reading from"
        purpose = f"{action}: {Path(file_path).name if file_path != 'unknown' else 'unknown'}"
    elif function_name in ['open_browser_tab']:
        url = function_args.get('url', 'unknown')
        purpose = f"Opening browser: {url}"
    elif function_name.startswith('log_'):
        purpose = f"Logging: {function_name.replace('log_', '').replace('_', ' ')}"
    
    return purpose


def extract_project_data_from_current_project():
    """Extract project data for display from current kanban project."""
    try:
        from twincli.tools.obsidian_kanban import _current_project
        if not _current_project:
            return None
            
        project_data = {
            'name': _current_project.project_name,
            'tasks': []
        }
        
        for task in _current_project.tasks:
            project_data['tasks'].append({
                'title': task.title,
                'status': task.status.value,
                'priority': task.priority,
                'subtasks': task.subtasks,
                'completed_subtasks': len([s for s in task.subtasks if s.get('completed', False)]),
                'total_subtasks': len(task.subtasks)
            })
        
        return project_data
        
    except ImportError:
        return None
    except Exception:
        return None