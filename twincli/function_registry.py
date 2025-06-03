# twincli/function_registry.py
"""
Function registry for TwinCLI - auto-generates dispatcher from TOOLS list.
Single source of truth: if it's in tools/__init__.py TOOLS, it's available in the dispatcher.
"""

def create_function_dispatcher():
    """Create function dispatcher by introspecting the TOOLS list."""
    from twincli.tools import TOOLS
    
    function_map = {}
    
    def add_tool(tool):
        """Add a single tool to the function map."""
        if callable(tool):
            # Standard callable function
            function_map[tool.__name__] = tool
        elif hasattr(tool, '__call__'):
            # Handle any callable objects
            tool_name = getattr(tool, '__name__', str(tool))
            function_map[tool_name] = tool
        elif hasattr(tool, 'function') and callable(tool.function):
            # Handle tool metadata objects (if any exist)
            tool_name = getattr(tool, 'name', tool.function.__name__)
            function_map[tool_name] = tool.function
    
    # Process TOOLS list, handling both individual tools and grouped tool lists
    for tool in TOOLS:
        if isinstance(tool, (list, tuple)):
            # Handle grouped tools like browser_tools, memory_tools, enhanced_git_tools
            for subtool in tool:
                add_tool(subtool)
        else:
            # Handle individual tools
            add_tool(tool)
    
    return function_map


def debug_function_dispatcher():
    """Debug version that logs everything it finds."""
    print("=== DEBUGGING FUNCTION DISPATCHER ===")
    
    # Get the current dispatcher
    current_functions = create_function_dispatcher()
    
    print(f"Total functions found: {len(current_functions)}")
    print("\nAll functions:")
    
    for i, func_name in enumerate(sorted(current_functions.keys()), 1):
        print(f"{i:2d}. {func_name}")
    
    # Also try to scan the tools directory manually for comparison
    print("\n=== TOOLS DIRECTORY SCAN ===")
    import os
    import importlib
    
    tools_dir = os.path.join(os.path.dirname(__file__), 'tools')
    print(f"Scanning: {tools_dir}")
    
    if os.path.exists(tools_dir):
        py_files = [f for f in os.listdir(tools_dir) if f.endswith('.py') and not f.startswith('__')]
        print(f"Python files found: {sorted(py_files)}")
        
        for py_file in sorted(py_files):
            module_name = py_file[:-3]
            print(f"\nChecking {module_name}:")
            
            try:
                module = importlib.import_module(f'twincli.tools.{module_name}')
                
                # Find all callable functions
                functions_in_module = []
                for attr_name in dir(module):
                    if not attr_name.startswith('_'):
                        attr = getattr(module, attr_name)
                        if callable(attr):
                            functions_in_module.append(attr_name)
                
                print(f"  Callable functions: {functions_in_module}")
                
                # Check which ones have docstrings
                with_docs = []
                for func_name in functions_in_module:
                    func = getattr(module, func_name)
                    if hasattr(func, '__doc__') and func.__doc__:
                        with_docs.append(func_name)
                
                print(f"  With docstrings: {with_docs}")
                
            except Exception as e:
                print(f"  ERROR importing: {e}")
    
    return current_functions


def get_function_info(function_name: str) -> dict:
    """Get detailed information about a specific function."""
    dispatcher = create_function_dispatcher()
    
    if function_name not in dispatcher:
        return {"error": f"Function '{function_name}' not found"}
    
    func = dispatcher[function_name]
    
    info = {
        "name": function_name,
        "module": getattr(func, '__module__', 'unknown'),
        "doc": getattr(func, '__doc__', 'No documentation'),
        "annotations": getattr(func, '__annotations__', {}),
        "callable": callable(func)
    }
    
    # Try to get signature information
    try:
        import inspect
        sig = inspect.signature(func)
        info["signature"] = str(sig)
        info["parameters"] = list(sig.parameters.keys())
    except Exception as e:
        info["signature_error"] = str(e)
    
    return info


def list_functions_by_category() -> dict:
    """Categorize functions by their module or purpose."""
    dispatcher = create_function_dispatcher()
    categories = {}
    
    for func_name, func in dispatcher.items():
        module = getattr(func, '__module__', 'unknown')
        
        # Extract category from module name
        if 'tools.' in module:
            category = module.split('tools.')[-1]
        else:
            category = 'core'
        
        if category not in categories:
            categories[category] = []
        
        categories[category].append(func_name)
    
    # Sort functions within each category
    for category in categories:
        categories[category].sort()
    
    return categories