from twincli.tools import TOOLS

model = genai.GenerativeModel(
    model_name="models/gemini-2.5-pro-preview-05-06",
    tools=TOOLS,
    ...
)
