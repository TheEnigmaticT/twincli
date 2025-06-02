# twincli/tools/obsidian_structure.py
"""
Manages standardized TwinCLI folder structure in Obsidian.
Creates organized documentation for tools, projects, and work.
"""

import os
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional

from twincli.tools.obsidian import (
    _find_obsidian_vault, 
    create_obsidian_note, 
    read_obsidian_note,
    update_obsidian_note,
    search_obsidian
)

class TwinCLIStructure:
    def __init__(self):
        self.vault_path = _find_obsidian_vault()
        self.base_folder = "TwinCLI"
        self.folders = {
            "projects": "TwinCLI/Projects",
            "journal": "TwinCLI/Journal", 
            "tools": "TwinCLI/Tools",
            "config": "TwinCLI/Config",
            "templates": "TwinCLI/Templates"
        }
        
    def initialize_structure(self) -> str:
        """Create the complete TwinCLI folder structure in Obsidian."""
        if not self.vault_path:
            return "❌ No Obsidian vault found. Please configure vault path."
        
        try:
            # Create main index note
            self._create_main_index()
            
            # Create folder-specific index notes
            self._create_projects_index()
            self._create_journal_index()
            self._create_tools_index()
            self._create_config_index()
            
            # Create essential config files
            self._create_tags_config()
            self._create_templates()
            
            return f"""✅ **TwinCLI Obsidian Structure Initialized**

📁 **Folder Structure Created:**
• `{self.base_folder}/` - Main TwinCLI workspace
• `{self.folders['projects']}/` - Kanban boards and project notes
• `{self.folders['journal']}/` - Daily work logs and session tracking
• `{self.folders['tools']}/` - Tool documentation and guides
• `{self.folders['config']}/` - Configuration files and templates

📋 **Index Notes Created:**
• Main TwinCLI dashboard
• Project tracking overview
• Tool library catalog
• Configuration management

🏷️ **Tagging System:** Standardized tags configured
📝 **Templates:** Ready for consistent note creation

**Next Steps:**
• Use create_terminal_project() for new projects
• Tool documentation will auto-populate in Tools folder
• Daily journal entries will be organized automatically"""
            
        except Exception as e:
            return f"❌ Error initializing structure: {e}"
    
    def _create_main_index(self):
        """Create the main TwinCLI index note."""
        content = f"""# TwinCLI Workspace

Welcome to your TwinCLI-powered Obsidian workspace! This is your central hub for AI-assisted project management and documentation.

## 🎯 Quick Navigation

### [[{self.folders['projects']}/Projects Index|📋 Active Projects]]
Current kanban boards and project tracking

### [[{self.folders['journal']}/Journal Index|📅 Work Journal]]
Daily logs, session tracking, and progress notes

### [[{self.folders['tools']}/Tools Index|🔧 Tools Library]]
Documentation for all TwinCLI tools and capabilities

### [[{self.folders['config']}/Config Index|⚙️ Configuration]]
Settings, templates, and workspace configuration

---

## 📊 Dashboard

*This section will be auto-updated by TwinCLI*

**Last Active Session:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Active Projects:** 0
**Tools Documented:** 0
**Journal Entries:** 0

---

## 🏷️ Tag System

Use these standardized tags for consistent organization:

### Project Tags
- #project/active - Currently working on
- #project/planning - In planning phase
- #project/review - Under review
- #project/completed - Finished projects
- #project/archived - Archived projects

### Work Tags  
- #work/research - Information gathering
- #work/coding - Development work
- #work/writing - Content creation
- #work/automation - Tool/script creation
- #work/analysis - Data analysis or review

### Tool Tags
- #tool/new - Newly created tools
- #tool/tested - Verified and working
- #tool/documentation - Tool guides and docs
- #tool/integration - Integration with other tools

### Session Tags
- #session/planning - Planning sessions
- #session/execution - Work execution
- #session/review - Review and retrospective

---

## 🚀 Getting Started

1. **Initialize a Project:** Use `create_terminal_project()` in TwinCLI
2. **Daily Work:** TwinCLI will automatically create journal entries
3. **Tool Development:** New tools auto-document in the Tools folder
4. **Review Progress:** Check project boards and journal summaries

*This workspace grows smarter as you work with TwinCLI!*
"""
        
        create_obsidian_note("TwinCLI Index", content, folder=None)
    
    def _create_projects_index(self):
        """Create the projects index note."""
        content = """# Projects Index

Central hub for all TwinCLI-managed projects and kanban boards.

## 🎯 Active Projects

*Auto-populated by TwinCLI as projects are created*

## 📋 Project Templates

### Quick Project Template
```
create_terminal_project(
    "Project Name",
    "Clear goal statement",
    '[{
        "title": "Task name",
        "priority": "1",
        "due_date": "2025-06-15",
        "subtasks": ["Subtask 1", "Subtask 2"],
        "metadata": {"complexity": "Medium"}
    }]'
)
```

## 📊 Project Metrics

*TwinCLI will update this section with project statistics*

---

## 🏷️ Project Organization

Projects are organized with these patterns:
- **Kanban Boards:** `TwinCLI Project - [Name]`
- **Task Notes:** Individual task details with metadata
- **Project Folders:** Grouped by project type or client

## 🔗 Related

- [[TwinCLI Index]] - Main workspace
- [[Journal Index]] - Work tracking
- [[Tools Index]] - Available tools
"""
        
        create_obsidian_note("Projects Index", content, folder=self.folders['projects'])
    
    def _create_journal_index(self):
        """Create the journal index note.""" 
        content = """# Journal Index

Daily work logs and session tracking for TwinCLI activities.

## 📅 Recent Sessions

*Auto-populated by TwinCLI work sessions*

## 📈 Patterns & Insights

*TwinCLI will analyze work patterns and provide insights here*

---

## 🗓️ Journal Structure

### Daily Notes Format
- **Date:** YYYY-MM-DD format
- **Sessions:** Multiple sessions per day
- **Tool Usage:** Automatic logging of tool calls
- **Task Progress:** Linked to project kanban boards
- **Insights:** AI reasoning and decision tracking

### Weekly Reviews
- **Accomplishments:** What was completed
- **Blockers:** What slowed progress
- **Learning:** New insights and improvements
- **Planning:** Upcoming work and goals

---

## 🏷️ Journal Tags

- #journal/daily - Daily session logs
- #journal/weekly - Weekly summaries  
- #journal/insight - Key insights and learning
- #journal/retrospective - Review sessions
- #journal/planning - Planning and goal setting

## 🔗 Related

- [[TwinCLI Index]] - Main workspace
- [[Projects Index]] - Active projects
- [[Tools Index]] - Tool documentation
"""
        
        create_obsidian_note("Journal Index", content, folder=self.folders['journal'])
    
    def _create_tools_index(self):
        """Create the tools index note."""
        content = """# Tools Index

Comprehensive library of all TwinCLI tools, capabilities, and documentation.

## 🔧 Tool Categories

### Core Tools
*Built-in TwinCLI functionality*

### Project Management
- **create_terminal_project()** - Kanban project creation
- **get_simple_todo_list()** - Terminal task lists
- **move_task_to_status()** - Task status updates

### Research & Information
- **search_web()** - Real-time web search
- **search_obsidian()** - Vault knowledge search

### Content & Documentation
- **create_obsidian_note()** - Note creation
- **read_obsidian_note()** - Note reading
- **update_obsidian_note()** - Note modification

### Automation & Workflow
- **Browser tools** - Web automation
- **Shell tools** - System commands
- **Git tools** - Version control

---

## 📚 Tool Documentation

*This section auto-populates as new tools are created*

### Recently Added Tools

### Most Used Tools

### Tool Integration Patterns

---

## 🏷️ Tool Organization

Tools are documented with:
- **Purpose:** What the tool does
- **Usage:** How to call it with examples
- **Parameters:** Required and optional arguments
- **Returns:** What to expect as output
- **Integration:** How it works with other tools
- **Examples:** Real-world usage scenarios

## 🔗 Related

- [[TwinCLI Index]] - Main workspace
- [[Projects Index]] - Project management
- [[Config Index]] - Tool configuration
"""
        
        create_obsidian_note("Tools Index", content, folder=self.folders['tools'])
    
    def _create_config_index(self):
        """Create the configuration index note."""
        content = """# Configuration Index

TwinCLI configuration files, templates, and workspace settings.

## ⚙️ Configuration Files

### Tags Configuration
- **File:** `tags.yml`
- **Purpose:** Standardized tagging system
- **Auto-completion:** Consistent tag usage

### Templates
- **Project Template:** Standard project structure
- **Tool Template:** New tool documentation format
- **Journal Template:** Daily work log format

---

## 🎨 Workspace Customization

### Obsidian Settings
- **Kanban Plugin:** Board configurations
- **Tag Management:** Auto-completion setup
- **Template Usage:** Quick note creation

### TwinCLI Integration
- **Vault Path:** Connection to Obsidian
- **Auto-documentation:** Tool and project tracking
- **Session Management:** Work flow automation

---

## 📋 Template Library

### Project Template
```yaml
project:
  name: "{{ project_name }}"
  goal: "{{ project_goal }}"
  created: "{{ date }}"
  status: "active"
  tags: ["#project/active"]
```

### Tool Documentation Template
```yaml
tool:
  name: "{{ tool_name }}"
  category: "{{ category }}"
  created: "{{ date }}"
  status: "documented"
  tags: ["#tool/new"]
```

## 🔗 Related

- [[TwinCLI Index]] - Main workspace
- [[Tools Index]] - Tool library
- [[Projects Index]] - Project management
"""
        
        create_obsidian_note("Config Index", content, folder=self.folders['config'])
    
    def _create_tags_config(self):
        """Create standardized tags configuration file."""
        tags_config = {
            "tags": {
                "project": ["active", "planning", "review", "completed", "archived"],
                "work": ["research", "coding", "writing", "automation", "analysis"],
                "tool": ["new", "tested", "documentation", "integration"],
                "session": ["planning", "execution", "review"],
                "priority": ["critical", "high", "medium", "low"],
                "status": ["todo", "in-progress", "blocked", "done"]
            },
            "auto_complete": True,
            "suggest_on_type": True
        }
        
        content = f"""# TwinCLI Tags Configuration

Standardized tagging system for consistent organization.

```yaml
{json.dumps(tags_config, indent=2)}
```

## Tag Usage Guidelines

### Project Lifecycle
1. **#project/planning** - Initial project setup
2. **#project/active** - Currently working
3. **#project/review** - Under review
4. **#project/completed** - Finished successfully
5. **#project/archived** - Historical reference

### Work Types
- **#work/research** - Information gathering
- **#work/coding** - Development and programming
- **#work/writing** - Content creation and documentation
- **#work/automation** - Tool and workflow creation
- **#work/analysis** - Data analysis and review

### Tool Management
- **#tool/new** - Recently created tools
- **#tool/tested** - Verified functionality
- **#tool/documentation** - Documented and explained
- **#tool/integration** - Connected with other tools

Copy this configuration to your Obsidian tag settings for auto-completion.
"""
        
        create_obsidian_note("tags", content, folder=self.folders['config'])
    
    def _create_templates(self):
        """Create note templates for consistent formatting."""
        
        # Project template
        project_template = """# {{title}}

**Goal:** {{goal}}
**Created:** {{date}}
**Status:** #project/active

## Project Overview

Brief description of what this project aims to accomplish.

## Success Criteria

- [ ] Criteria 1
- [ ] Criteria 2
- [ ] Criteria 3

## Key Tasks

*Linked from kanban board: [[TwinCLI Project - {{title}}]]*

## Resources & References

## Notes & Updates

### {{date}}
Project initiated with TwinCLI assistance.
"""
        
        create_obsidian_note("Project Template", project_template, folder=f"{self.folders['templates']}")
        
        # Tool documentation template
        tool_template = """# {{tool_name}}

**Category:** {{category}}
**Created:** {{date}}
**Status:** #tool/new

## Purpose

Brief description of what this tool does and why it's useful.

## Usage

### Function Signature
```python
{{function_signature}}
```

### Parameters
- **param1** (type): Description
- **param2** (type, optional): Description

### Returns
- **type**: Description of return value

## Examples

### Basic Usage
```python
result = {{tool_name}}("example_input")
print(result)
```

### Advanced Usage
```python
# More complex example
result = {{tool_name}}(
    param1="value1",
    param2="value2"
)
```

## Integration

How this tool works with other TwinCLI tools:
- **Tool A**: Integration pattern
- **Tool B**: Usage combination

## Notes

Implementation details, limitations, or special considerations.

---

*Auto-generated by TwinCLI on {{date}}*
"""
        
        create_obsidian_note("Tool Template", tool_template, folder=f"{self.folders['templates']}")

def initialize_twincli_workspace() -> str:
    """Initialize the complete TwinCLI workspace structure in Obsidian."""
    structure = TwinCLIStructure()
    return structure.initialize_structure()

def document_new_tool(tool_name: str, function_signature: str, description: str, 
                     category: str = "utility", examples: List[str] = None) -> str:
    """Create comprehensive documentation for a new tool."""
    if not examples:
        examples = [f'{tool_name}("example_input")']
    
    structure = TwinCLIStructure()
    if not structure.vault_path:
        return "❌ No Obsidian vault configured"
    
    try:
        content = f"""# {tool_name}

**Category:** {category}
**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Status:** #tool/new #tool/documentation

## Purpose

{description}

## Usage

### Function Signature
```python
{function_signature}
```

## Examples

"""
        
        # Add examples
        for i, example in enumerate(examples, 1):
            content += f"""### Example {i}
```python
{example}
```

"""
        
        content += f"""## Integration Patterns

This tool can be combined with other TwinCLI tools for enhanced workflows:

- **Project Management**: Use with task planning tools
- **Documentation**: Combine with Obsidian note tools  
- **Automation**: Chain with browser and shell tools

## Technical Details

*Implementation notes and considerations*

## Related Tools

*Links to related functionality*

---

**Auto-documented by TwinCLI** | [[Tools Index|🔧 Back to Tools Library]]

#tool/{category.replace('_', '-')} #twincli #documentation
"""
        
        # Create the tool documentation
        create_obsidian_note(f"{tool_name}", content, folder=structure.folders['tools'])
        
        # Update the tools index
        _update_tools_index(tool_name, category, description)
        
        return f"""📚 **Tool Documentation Created**

**Tool:** {tool_name}
**Category:** {category}
**Location:** `{structure.folders['tools']}/{tool_name}.md`

✅ **Documentation includes:**
• Purpose and description
• Function signature and parameters
• Usage examples and patterns
• Integration with other tools
• Technical implementation notes

🔗 **Tool added to Tools Index for easy discovery**

**View in Obsidian:** Navigate to Tools folder or search for `{tool_name}`"""
        
    except Exception as e:
        return f"❌ Error creating tool documentation: {e}"

def _update_tools_index(tool_name: str, category: str, description: str):
    """Update the tools index with the new tool."""
    try:
        structure = TwinCLIStructure()
        index_note = read_obsidian_note(f"{structure.folders['tools']}/Tools Index")
        
        if "No note found" not in index_note:
            # Find the "Recently Added Tools" section and add the new tool
            new_tool_entry = f"\n- **[[{tool_name}]]** ({category}) - {description}"
            
            # This is a simplified update - a full implementation would parse and properly insert
            updated_content = index_note.replace(
                "### Recently Added Tools",
                f"### Recently Added Tools{new_tool_entry}"
            )
            
            update_obsidian_note(f"{structure.folders['tools']}/Tools Index", updated_content)
            
    except Exception:
        pass  # Don't fail if index update fails

def get_workspace_summary() -> str:
    """Get a summary of the TwinCLI workspace structure."""
    structure = TwinCLIStructure()
    if not structure.vault_path:
        return "❌ No Obsidian vault configured"
    
    try:
        # Count items in each folder
        project_count = len(search_obsidian("TwinCLI Project").split('\n')) if "Found" in search_obsidian("TwinCLI Project") else 0
        tool_count = len(search_obsidian("#tool/").split('\n')) if "Found" in search_obsidian("#tool/") else 0
        journal_count = len(search_obsidian("#journal/").split('\n')) if "Found" in search_obsidian("#journal/") else 0
        
        return f"""📊 **TwinCLI Workspace Summary**

**Vault Location:** {structure.vault_path}
**Base Folder:** {structure.base_folder}

📋 **Content Statistics:**
• **Projects:** {project_count} kanban boards
• **Tools:** {tool_count} documented tools
• **Journal Entries:** {journal_count} session logs

📁 **Folder Structure:**
• `{structure.folders['projects']}/` - Active project management
• `{structure.folders['journal']}/` - Work session tracking  
• `{structure.folders['tools']}/` - Tool documentation library
• `{structure.folders['config']}/` - Configuration and templates

🏷️ **Organization:**
• Standardized tagging system active
• Templates ready for consistent note creation
• Auto-documentation enabled for new tools

**Next Actions:**
• Create projects with `create_terminal_project()`
• New tools auto-document in Tools folder
• Daily work automatically tracked in Journal"""
        
    except Exception as e:
        return f"❌ Error getting workspace summary: {e}"

# Export structure management functions
structure_tools = [
    initialize_twincli_workspace,
    document_new_tool,
    get_workspace_summary
]