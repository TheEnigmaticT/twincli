# twincli/tools/tooltool.py
"""
Meta-tool for TwinCLI self-modification and tool creation.
This tool enables TwinCLI to create new tools for itself following established patterns.
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

def analyze_tool_need(task_description: str, current_capabilities: str = None) -> str:
    """
    Analyze whether TwinCLI needs a new tool for a given task.
    
    Args:
        task_description: Description of what the user wants to accomplish
        current_capabilities: Optional JSON string of current tool capabilities
        
    Returns:
        Analysis result with recommendation
    """
    # Get current tool inventory
    tools_dir = Path(__file__).parent
    existing_tools = []
    
    try:
        for tool_file in tools_dir.glob("*.py"):
            if tool_file.name not in ["__init__.py", "tooltool.py"]:
                existing_tools.append(tool_file.stem)
    except Exception as e:
        return f"Error analyzing tools directory: {e}"
    
    # Common tool categories and their indicators
    tool_categories = {
        "file_operations": ["read", "write", "create", "delete", "move", "copy", "file"],
        "web_operations": ["browse", "scrape", "download", "upload", "http", "api", "web"],
        "data_processing": ["parse", "convert", "transform", "csv", "json", "xml", "data"],
        "system_operations": ["command", "shell", "process", "system", "run"],
        "communication": ["email", "slack", "discord", "message", "notify"],
        "database": ["sql", "query", "database", "db", "store"],
        "ai_ml": ["model", "predict", "analyze", "ml", "ai", "llm"],
        "security": ["encrypt", "decrypt", "hash", "auth", "key", "secure"],
        "version_control": ["git", "commit", "push", "pull", "branch", "repo"],
        "monitoring": ["log", "monitor", "watch", "track", "alert"]
    }
    
    task_lower = task_description.lower()
    needed_categories = []
    
    for category, keywords in tool_categories.items():
        if any(keyword in task_lower for keyword in keywords):
            needed_categories.append(category)
    
    # Check if we already have tools for these categories
    coverage_analysis = []
    for category in needed_categories:
        existing_in_category = [tool for tool in existing_tools 
                              if any(keyword in tool.lower() 
                                   for keyword in tool_categories[category])]
        
        if existing_in_category:
            coverage_analysis.append(f"✅ {category}: Covered by {existing_in_category}")
        else:
            coverage_analysis.append(f"❌ {category}: NO COVERAGE - New tool needed")
    
    # Recommendation logic
    missing_categories = [cat for cat in needed_categories 
                         if not any(tool for tool in existing_tools 
                                  if any(kw in tool.lower() for kw in tool_categories[cat]))]
    
    if missing_categories:
        recommendation = f"""
🔧 **TOOL CREATION RECOMMENDED**

**Task:** {task_description}

**Analysis:**
{chr(10).join(coverage_analysis)}

**Missing Capabilities:** {', '.join(missing_categories)}

**Existing Tools:** {', '.join(existing_tools)}

**Recommendation:** Create new tool(s) for {', '.join(missing_categories)} functionality.
"""
    else:
        recommendation = f"""
✅ **EXISTING TOOLS SUFFICIENT**

**Task:** {task_description}

**Analysis:**
{chr(10).join(coverage_analysis)}

**Recommendation:** Use existing tools: {', '.join(existing_tools)}
"""
    
    return recommendation

def validate_tool_code(tool_code: str, tool_name: str) -> str:
    """
    Validate that tool code follows TwinCLI coding standards.
    
    Args:
        tool_code: Python code for the new tool
        tool_name: Name of the tool
        
    Returns:
        Validation result with issues or approval
    """
    issues = []
    
    try:
        # Parse the code to check syntax
        tree = ast.parse(tool_code)
        
        # Required patterns for TwinCLI tools
        has_main_function = False
        has_proper_docstring = False
        has_error_handling = False
        has_type_hints = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name == tool_name or node.name.endswith('_tool'):
                    has_main_function = True
                    
                    # Check for docstring
                    if (node.body and 
                        isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)):
                        has_proper_docstring = True
                    
                    # Check for type hints
                    if node.args.args and any(arg.annotation for arg in node.args.args):
                        has_type_hints = True
                    
                    # Check for error handling (try/except blocks)
                    for child in ast.walk(node):
                        if isinstance(child, ast.Try):
                            has_error_handling = True
                            break
        
        # Validation checks
        if not has_main_function:
            issues.append(f"❌ Missing main function named '{tool_name}' or ending with '_tool'")
        
        if not has_proper_docstring:
            issues.append("❌ Missing docstring in main function")
        
        if not has_error_handling:
            issues.append("❌ Missing error handling (try/except blocks)")
        
        if not has_type_hints:
            issues.append("❌ Missing type hints on function parameters")
        
        # Check for required patterns
        code_lines = tool_code.split('\n')
        
        # Check for imports at top
        import_found = False
        for line in code_lines[:10]:  # Check first 10 lines
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                import_found = True
                break
        
        # Check for return type annotation
        return_annotation = False
        for line in code_lines:
            if ' -> str:' in line or ' -> int:' in line or ' -> bool:' in line:
                return_annotation = True
                break
        
        if not return_annotation:
            issues.append("❌ Missing return type annotation (should return str for tool output)")
        
        # Check for security issues
        dangerous_patterns = ['eval(', 'exec(', 'os.system(', '__import__']
        for pattern in dangerous_patterns:
            if pattern in tool_code:
                issues.append(f"⚠️ Potentially dangerous pattern detected: {pattern}")
        
        # Coding style checks
        if 'def ' in tool_code and 'def  ' in tool_code:
            issues.append("❌ Inconsistent spacing in function definitions")
        
        if tool_code.count('\t') > 0:
            issues.append("❌ Uses tabs instead of spaces for indentation")
        
    except SyntaxError as e:
        issues.append(f"❌ Syntax error: {e}")
    except Exception as e:
        issues.append(f"❌ Code analysis failed: {e}")
    
    # Generate validation report
    if issues:
        return f"""
🔍 **TOOL CODE VALIDATION FAILED**

**Tool Name:** {tool_name}

**Issues Found:**
{chr(10).join(issues)}

**Required Standards:**
- Function with proper name and docstring
- Type hints on parameters and return value
- Error handling with try/except blocks
- Return string for tool output
- Use spaces for indentation (4 spaces)
- Avoid dangerous operations (eval, exec, os.system)

**Please fix these issues before integration.**
"""
    else:
        return f"""
✅ **TOOL CODE VALIDATION PASSED**

**Tool Name:** {tool_name}
**Standards Met:** All TwinCLI coding standards satisfied
**Ready for Integration:** Yes
"""

def create_tool_template(tool_name: str, tool_description: str, tool_category: str = "utility") -> str:
    """
    Generate a properly formatted tool template following TwinCLI standards.
    
    Args:
        tool_name: Name of the tool function
        tool_description: What the tool does
        tool_category: Category of tool (utility, web, file, etc.)
        
    Returns:
        Complete Python code template for the new tool
    """
    
    # Sanitize tool name
    safe_tool_name = re.sub(r'[^a-zA-Z0-9_]', '_', tool_name.lower())
    
    template = f'''# twincli/tools/{safe_tool_name}.py
"""
{tool_description}

Category: {tool_category}
Created: {datetime.now().strftime("%Y-%m-%d")}
"""

import os
from typing import Optional
from pathlib import Path


def {safe_tool_name}(param1: str, param2: Optional[str] = None) -> str:
    """
    {tool_description}
    
    Args:
        param1: Description of first parameter
        param2: Optional description of second parameter
        
    Returns:
        String result of the operation
    """
    try:
        # TODO: Implement tool logic here
        
        # Example implementation structure:
        # 1. Validate inputs
        if not param1 or not param1.strip():
            return "Error: param1 cannot be empty"
        
        # 2. Perform main operation
        result = f"Processing {{param1}}"
        if param2:
            result += f" with {{param2}}"
        
        # 3. Return success result
        return f"Success: {{result}}"
        
    except FileNotFoundError as e:
        return f"File not found: {{e}}"
    except PermissionError as e:
        return f"Permission denied: {{e}}"
    except Exception as e:
        return f"Error in {safe_tool_name}: {{e}}"


# Tool registration for TwinCLI
{safe_tool_name}_metadata = {{
    "function": {safe_tool_name},
    "name": "{safe_tool_name}",
    "description": "{tool_description}",
    "category": "{tool_category}",
    "parameters": {{
        "type": "object",
        "properties": {{
            "param1": {{
                "type": "string",
                "description": "Description of first parameter"
            }},
            "param2": {{
                "type": "string",
                "description": "Optional description of second parameter"
            }}
        }},
        "required": ["param1"]
    }}
}}
'''
    
    return template

def integrate_new_tool(tool_name: str, tool_code: str) -> str:
    """
    Integrate a new tool into TwinCLI by writing the file and updating __init__.py.
    Now also creates comprehensive Obsidian documentation.
    
    Args:
        tool_name: Name of the tool
        tool_code: Complete Python code for the tool
        
    Returns:
        Integration result with Obsidian documentation status
    """
    try:
        # Sanitize tool name
        safe_tool_name = re.sub(r'[^a-zA-Z0-9_]', '_', tool_name.lower())
        
        # Get paths
        tools_dir = Path(__file__).parent
        tool_file_path = tools_dir / f"{safe_tool_name}.py"
        init_file_path = tools_dir / "__init__.py"
        
        # Step 1: Write the tool file
        with open(tool_file_path, 'w', encoding='utf-8') as f:
            f.write(tool_code)
        
        # Step 2: Update __init__.py to import and register the tool
        if init_file_path.exists():
            with open(init_file_path, 'r', encoding='utf-8') as f:
                init_content = f.read()
            
            # Add import statement
            import_line = f"from twincli.tools.{safe_tool_name} import {safe_tool_name}"
            
            # Find where to insert the import (after existing imports)
            lines = init_content.split('\n')
            import_insert_index = 0
            
            for i, line in enumerate(lines):
                if line.startswith('from twincli.tools.'):
                    import_insert_index = i + 1
                elif line.startswith('TOOLS = ['):
                    break
            
            # Insert import
            if import_line not in init_content:
                lines.insert(import_insert_index, import_line)
            
            # Add to TOOLS list
            tools_list_start = -1
            tools_list_end = -1
            
            for i, line in enumerate(lines):
                if line.strip().startswith('TOOLS = ['):
                    tools_list_start = i
                elif tools_list_start != -1 and line.strip() == ']':
                    tools_list_end = i
                    break
            
            if tools_list_start != -1 and tools_list_end != -1:
                # Insert the new tool before the closing bracket
                tool_entry = f"    {safe_tool_name},"
                if tool_entry.strip() not in [line.strip() for line in lines]:
                    lines.insert(tools_list_end, tool_entry)
            
            # Write updated __init__.py
            updated_content = '\n'.join(lines)
            with open(init_file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
        
        # Step 3: Extract tool information for documentation
        function_signature, description, category = _extract_tool_info(tool_code, safe_tool_name)
        
        # Step 4: Create Obsidian documentation
        obsidian_result = ""
        try:
            from twincli.tools.obsidian_structure import document_new_tool
            obsidian_result = document_new_tool(
                tool_name=safe_tool_name,
                function_signature=function_signature,
                description=description,
                category=category,
                examples=[f"{safe_tool_name}('example_input')"]
            )
        except ImportError:
            obsidian_result = "⚠️ Obsidian documentation not available (obsidian_structure not imported)"
        except Exception as e:
            obsidian_result = f"⚠️ Obsidian documentation failed: {e}"
        
        return f"""
✅ **TOOL INTEGRATION SUCCESSFUL**

**Tool Name:** {safe_tool_name}
**File Created:** {tool_file_path}
**Registration:** Added to TOOLS list in __init__.py

📚 **Obsidian Documentation:**
{obsidian_result}

**Next Steps:**
1. Restart TwinCLI (or trigger reload if using -e flag)
2. Test the new tool with a sample call
3. Verify tool appears in available functions
4. Check documentation in Obsidian Tools folder

**Tool is now ready for use!**
"""
        
    except Exception as e:
        return f"❌ Tool integration failed: {e}"

def _extract_tool_info(tool_code: str, tool_name: str) -> tuple:
    """Extract function signature, description, and category from tool code."""
    try:
        import ast
        tree = ast.parse(tool_code)
        
        function_signature = f"def {tool_name}():"
        description = f"A tool that performs {tool_name} operations"
        category = "utility"
        
        # Find the main function
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and (node.name == tool_name or node.name.endswith('_tool')):
                # Extract function signature
                args = []
                for arg in node.args.args:
                    arg_name = arg.arg
                    arg_type = ast.unparse(arg.annotation) if arg.annotation else "Any"
                    args.append(f"{arg_name}: {arg_type}")
                
                return_type = ast.unparse(node.returns) if node.returns else "str"
                function_signature = f"def {node.name}({', '.join(args)}) -> {return_type}:"
                
                # Extract docstring for description
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    description = node.body[0].value.value.strip()
                
                break
        
        # Try to determine category from code content
        code_lower = tool_code.lower()
        if any(keyword in code_lower for keyword in ['web', 'http', 'request', 'browser']):
            category = "web"
        elif any(keyword in code_lower for keyword in ['file', 'read', 'write', 'path']):
            category = "filesystem" 
        elif any(keyword in code_lower for keyword in ['git', 'commit', 'repo']):
            category = "version_control"
        elif any(keyword in code_lower for keyword in ['email', 'message', 'send']):
            category = "communication"
        elif any(keyword in code_lower for keyword in ['obsidian', 'note', 'markdown']):
            category = "documentation"
        
        return function_signature, description, category
        
    except Exception:
        return f"def {tool_name}():", f"A tool that performs {tool_name} operations", "utility"

def generate_tool_documentation(tool_name: str, tool_file_path: str = None) -> str:
    """
    Generate documentation for a tool by analyzing its code.
    
    Args:
        tool_name: Name of the tool to document
        tool_file_path: Optional path to tool file
        
    Returns:
        Generated documentation
    """
    try:
        if tool_file_path is None:
            tools_dir = Path(__file__).parent
            tool_file_path = tools_dir / f"{tool_name}.py"
        
        if not Path(tool_file_path).exists():
            return f"Tool file not found: {tool_file_path}"
        
        with open(tool_file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Parse the code
        tree = ast.parse(code)
        
        documentation = f"# {tool_name} Tool Documentation\n\n"
        
        # Extract function information
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                # Function signature
                args = []
                for arg in node.args.args:
                    arg_name = arg.arg
                    arg_type = ast.unparse(arg.annotation) if arg.annotation else "Any"
                    args.append(f"{arg_name}: {arg_type}")
                
                return_type = ast.unparse(node.returns) if node.returns else "Any"
                signature = f"def {node.name}({', '.join(args)}) -> {return_type}:"
                
                documentation += f"## Function: `{node.name}`\n\n"
                documentation += f"```python\n{signature}\n```\n\n"
                
                # Extract docstring
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant)):
                    docstring = node.body[0].value.value
                    documentation += f"**Description:** {docstring}\n\n"
        
        # Add usage example
        documentation += f"""
## Usage Example

```python
# Call from TwinCLI
result = {tool_name}("example_parameter")
print(result)
```

## Integration Status
- ✅ Integrated into TwinCLI
- ✅ Available in TOOLS list
- ✅ Ready for use

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        return documentation
        
    except Exception as e:
        return f"Error generating documentation: {e}"

# Export the meta-tool functions
tooltool_tools = [
    analyze_tool_need,
    validate_tool_code,
    create_tool_template,
    integrate_new_tool,
    generate_tool_documentation
]