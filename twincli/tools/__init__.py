from twincli.tools.search import search_web
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
    *browser_tools,
    *task_management_tools,
    *memory_tools,
    *tooltool_tools
]