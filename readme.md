# TwinCLI 🧠💻

I didn't see a great tool to run Gemini in my commandline, so I made one. Mostly becasuse I wanted it to have some tooling that I didn't see others have. Maybe I'm wrong! :P 

**TwinCLI** is a modular, terminal-based interface for [Gemini 2.5](https://ai.google.dev/), designed to be fast, memory-efficient, and extensible. Use powerful AI models right from your shell — without the RAM-heavy browser.

> “Twin” = CLI twin to Gemini — fast, thoughtful, always nearby.

---

## 🚀 Features

- 💬 **REPL-based chat** — Hold full conversations with memory
- 🔌 **Tool support** — Gemini can call real Python functions (e.g. search, shell, Notion)
- 🧠 **Powered by Gemini 2.5 Pro Preview** — Use the latest model with huge context (1M+ tokens)
- 🌐 **Custom web search** — Built-in support via [Serper.dev](https://serper.dev)
- 🗂 **Modular design** — Add your own tools in `tools/` and auto-wire them into Gemini

---

## 🔧 Installation

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/twincli.git
cd twincli
```

### 2. Install with pipx (recommended)

```bash
pipx install .
```

> Don’t have `pipx`?  
> Install it with: `sudo apt install pipx && pipx ensurepath`

---

## 🔐 Configuration

### Run once to set up your API keys:

```bash
twincli --config
```

You'll be prompted to enter:

- Your **Gemini API key** (get one from [Google AI Studio](https://makersuite.google.com/app/apikey))
- Your **Serper.dev API key** (for web search)

This creates a config file at:

```
~/.twincli/config.json
```

Example:

```json
{
  "api_key": "AIzaSy...yourGeminiKey",
  "serper_api_key": "serper-api-key-xxxx"
}
```

---

## 🧪 Usage

```bash
twincli
```

Then chat away:

```
You > What’s the latest news on the EU AI Act?
```

TwinCLI will:
- Use Gemini 2.5
- Call `search_web()` if needed
- Return grounded, contextual answers

---

## 🧰 Built-in Tools

- `search_web(query)` — Searches the live web via Serper.dev
- [planned] `notion_reader(page_id)` — Parses Notion transcripts for tasks
- [planned] `run_shell(cmd)` — Run limited terminal commands with output

Want to add your own tools? See below 👇

---

## 🧩 Adding Your Own Tools

Create a Python file in `twincli/tools/`, for example:

```python
def joke_tool(topic: str) -> str:
    return f"Why did {topic} cross the road? To train an LLM!"

joke = {
  "function": joke_tool,
  "name": "joke_tool",
  "description": "Tells a bad joke",
  "parameters": {
    "type": "object",
    "properties": {
      "topic": {"type": "string"}
    },
    "required": ["topic"]
  }
}
```

Then import and register it in `tools/__init__.py`:

```python
from .joke import joke
TOOLS = [joke, ...]
```

---

## 🧱 Project Structure

```
twincli/
├── twincli/
│   ├── __main__.py        # CLI entrypoint and REPL
│   ├── config.py          # Config handling
│   ├── tools/             # Modular tool folder
│   │   ├── __init__.py    # Auto-load tools
│   │   └── search.py      # Serper.dev tool
├── pyproject.toml         # Pipx + packaging config
└── README.md
```

---

## 👥 Contributing

Pull requests welcome! Please:

- Keep tools modular and clearly documented
- Add yourself to the CONTRIBUTORS section if submitting a major tool

Want help building a tool? [Open an issue](https://github.com/yourusername/twincli/issues)

---

## 📜 License

MIT – do what you like. Attribution appreciated.

---

## ✨ Inspiration

TwinCLI was built to help developers like me (and you) use AI more naturally: directly in the workflow, without fluff. It’s fast, hackable, and respectful of your RAM.

Hope ya like it!
