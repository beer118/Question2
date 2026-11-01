"""Optional Ollama-based planning. The model returns JSON tool calls only."""
import json
import os
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

TOOL_DESCRIPTIONS = [
    {"name": "summarize", "description": "Summarize the active sheet: row/column count, columns, missing values and numeric summaries.", "args": {}},
    {"name": "top_values", "description": "Find the largest rows by a numeric column.", "args": {"column": "column name", "n": "integer"}},
    {"name": "write_cell", "description": "Write a value or Excel formula to one cell.", "args": {"cell": "cell address such as D2", "value": "value or formula string"}},
    {"name": "format_header", "description": "Format the first row with bold text and a colored fill.", "args": {}},
    {"name": "highlight_negative", "description": "Add conditional formatting to highlight negative numeric cells.", "args": {"cell_range": "optional Excel range"}},
    {"name": "create_chart", "description": "Create a chart from the first two columns or named columns.", "args": {"kind": "bar, line or pie", "x_column": "optional column name", "y_column": "optional column name"}},
]

SYSTEM = """You are an Excel assistant. Convert the user's request into a short JSON array of tool calls.
Only use the available tools. Never invent column names; use workbook context. If a request is ambiguous, return
{"clarification":"your question"}. Output JSON only, no markdown. Format:
{"calls":[{"tool":"summarize","args":{}}],"explanation":"brief plan"}
Tools:
""" + json.dumps(TOOL_DESCRIPTIONS)

def plan_request(user_request: str, workbook_context: str) -> dict:
    """Ask local Ollama for a tool plan. Raises a readable error if unavailable."""
    prompt = f"Workbook context:\n{workbook_context[:12000]}\n\nUser request:\n{user_request}"
    response = requests.post(
        f"{OLLAMA_URL.rstrip('/')}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "format": "json",
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        },
        timeout=90,
    )
    response.raise_for_status()
    result = response.json()["message"]["content"]
    parsed = json.loads(result)
    if not isinstance(parsed, dict):
        raise ValueError("The model did not return a JSON object.")
    if not isinstance(parsed.get("calls", []), list):
        raise ValueError("The model returned an invalid tool plan.")
    return parsed
