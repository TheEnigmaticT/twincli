def read_notion_transcripts(page_id: str) -> str:
    # In the real version, you'd call the Notion API and extract text
    return f"(Stub) Fetched and summarized tasks from Notion page: {page_id}"

notion_tool = {
    "function": read_notion_transcripts,
    "name": "notion_reader",
    "description": "Read Notion transcript pages and extract tasks or notes.",
    "parameters": {
        "type": "object",
        "properties": {
            "page_id": {
                "type": "string",
                "description": "The Notion page ID to read"
            }
        },
        "required": ["page_id"]
    }
}
