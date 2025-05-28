# twincli/tools/__init__.py

from twincli.tools.search import search_web
from twincli.tools.obsidian import search_obsidian, read_obsidian_note

TOOLS = [search_web, search_obsidian, read_obsidian_note]