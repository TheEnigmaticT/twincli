import requests
import os
import json
from twincli.config import load_config

def search_web(query: str) -> str:
    """Search the web for current and real-time information using Serper.dev.
    
    This function can search for:
    - Current dates, times, and calendar information (ISO weeks, current date, etc.)
    - Real-time news and events
    - Latest information on any topic
    - Current weather, stock prices, etc.
    
    Args:
        query: The search query to run
        
    Returns:
        String containing the top search results
    """
    config = load_config()
    api_key = config.get("serper_api_key")
    if not api_key:
        return "No Serper API key found in config."

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    data = {"q": query}

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        return f"Search failed with status {response.status_code}"

    results = response.json().get("organic", [])
    
    # Include snippets for more useful information
    summary_parts = []
    for r in results[:5]:
        title = r.get('title', 'No title')
        link = r.get('link', 'No link')
        snippet = r.get('snippet', 'No description')
        summary_parts.append(f"**{title}**\n{snippet}\n{link}")
    
    summary = "\n\n".join(summary_parts)
    return f"Top search results for '{query}':\n\n{summary}"

# Just export the function - tool declaration is handled in __init__.py