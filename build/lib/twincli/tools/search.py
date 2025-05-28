import requests
import os
import json
from twincli.config import load_config

def search_web(query: str) -> str:
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
    summary = "\n".join([f"{r['title']}\n{r['link']}" for r in results[:5]])
    return f"Top search results for '{query}':\n\n{summary}"

search_tool = {
    "function": search_web,
    "name": "search_web",
    "description": "Search the web for real-time information using Serper.dev",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query to run"}
        },
        "required": ["query"]
    }
}
