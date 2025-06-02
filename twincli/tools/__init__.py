from twincli.tools.enhanced_search import search_web
from twincli.tools.obsidian import (
    search_obsidian, 
    read_obsidian_note, 
    create_obsidian_note,
    update_obsidian_note,
    create_daily_note
)
from twincli.tools.filesystem import write_file, read_file, create_directory, list_directory
from twincli.tools.browser import browser_tools
from twincli.tools.task_planner import task_management_tools
from twincli.tools.memory_journal import memory_tools
from twincli.tools.tooltool import tooltool_tools
from twincli.tools.explain_git_action import explain_git_action
from twincli.tools.enhanced_git_command import enhanced_git_tools  # NEW: Enhanced Git tools
from twincli.tools.smart_path_finder import smart_path_tools        # NEW: Smart path resolution
from twincli.tools.enhanced_search import enhanced_search_tools     # NEW: Enhanced search
from twincli.tools.research_orchestrator import research_tools      # NEW: Research orchestrator
from twincli.tools.send_gmail import send_gmail
from twincli.tools.read_gmail_inbox import read_gmail_inbox
from twincli.tools.context_compression import initialize_session_with_kanban_state
from twincli.tools.analysis_output import save_analysis_report, save_data_summary

TOOLS = [
    search_web, 
    search_obsidian, 
    read_obsidian_note,
    create_obsidian_note,
    update_obsidian_note, 
    create_daily_note,
    write_file,
    read_file,
    create_directory,
    list_directory,
    save_analysis_report,
    *browser_tools,
    *task_management_tools,
    *memory_tools,
    *tooltool_tools,
    explain_git_action,
    *enhanced_git_tools,        # NEW: smart_git_command, quick_git_operations
    *smart_path_tools,          # NEW: smart_find_path, resolve_path_intelligently, smart_git_path_resolver
    *enhanced_search_tools,     # NEW: intelligent_search
    *research_tools,            # NEW: comprehensive_research
    send_gmail,
    read_gmail_inbox,
    initialize_session_with_kanban_state,
]