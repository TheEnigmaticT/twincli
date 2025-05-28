# twincli/tools/__init__.py

from twincli.tools.shell import shell_tool
from twincli.tools.notion_reader import notion_tool
from twincli.tools.search import search_tool

TOOLS = [
    shell_tool,
    notion_tool,
    search_tool
]

