# twincli/tools/__init__.py
from twincli.tools.enhanced_search import search_web
from twincli.tools.obsidian import (
    search_obsidian, 
    read_obsidian_note, 
    create_obsidian_note,
    update_obsidian_note,
    create_daily_note,
    list_recent_notes
)
from twincli.tools.obsidian_kanban import terminal_kanban_tools  # NEW: Add kanban tools
from twincli.tools.obsidian_structure import structure_tools    # NEW: Add structure tools
from twincli.tools.filesystem import write_file, read_file, create_directory, list_directory
from twincli.tools.browser import browser_tools
from twincli.tools.task_planner import task_management_tools
from twincli.tools.memory_journal import memory_tools
from twincli.tools.tooltool import tooltool_tools
from twincli.tools.explain_git_action import explain_git_action
from twincli.tools.enhanced_git_command import enhanced_git_tools
from twincli.tools.smart_path_finder import smart_path_tools
from twincli.tools.enhanced_search import enhanced_search_tools
from twincli.tools.research_orchestrator import research_tools
from twincli.tools.send_gmail import send_gmail
from twincli.tools.read_gmail_inbox import read_gmail_inbox
from twincli.tools.context_compression import initialize_session_with_kanban_state
from twincli.tools.analysis_output import save_analysis_report, save_data_summary
from twincli.tools.research_person_for_podcast import research_person_for_podcast

TOOLS = [
    search_web, 
    search_obsidian, 
    read_obsidian_note,
    create_obsidian_note,
    update_obsidian_note, 
    create_daily_note,
    list_recent_notes,
    *terminal_kanban_tools,     # NEW: Add all kanban project management tools
    *structure_tools,           # NEW: Add workspace structure management tools
    write_file,
    read_file,
    create_directory,
    list_directory,
    save_analysis_report,
    save_data_summary,          # NEW: Also added this missing tool
    *browser_tools,
    *task_management_tools,
    *memory_tools,
    *tooltool_tools,
    explain_git_action,
    *enhanced_git_tools,
    *smart_path_tools,
    *enhanced_search_tools,
    *research_tools,
    send_gmail,
    read_gmail_inbox,
    initialize_session_with_kanban_state,
    research_person_for_podcast,
]