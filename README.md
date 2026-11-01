# Excel Agent

A local, tool-based AI assistant for XLSX, XLSM, CSV and TSV files.

## Features
- Upload, inspect, preview, edit and download spreadsheets
- Natural-language requests via Ollama (optional; app works without an LLM)
- Data analysis and summaries
- Formula insertion, cell formatting, conditional formatting and charts
- CSV/TSV import/export
- Keeps the original upload unchanged; edits are made to a working copy

## Requirements
Python 3.11+ recommended. For optional local LLM support, install Ollama and pull a model:
```bash
ollama pull qwen2.5:3b
```

## Run on Debian/Linux
```bash
cd excel-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Optional environment variables:
- `OLLAMA_URL` (default `http://localhost:11434`)
- `OLLAMA_MODEL` (default `qwen2.5:3b`)

## Example prompts
- "Summarize the data in the active sheet."
- "Show the five largest values in the Revenue column."
- "Add a total formula to cell D20."
- "Make row 1 bold with a blue fill."
- "Highlight negative values in red."
- "Create a bar chart using columns A and B."

## Safety and limitations
- The LLM can only request registered tools; it cannot execute arbitrary Python or shell commands.
- The app asks for confirmation before applying a tool plan.
- XLSX formulas are written, not calculated by openpyxl. Install LibreOffice for recalculation if desired.
- XLSM macros are preserved when possible, but complex workbook features may not survive every edit.
- CSV/TSV cannot store formatting, multiple sheets, formulas as Excel formulas, or embedded charts.
- Uploaded files are processed locally by the app. Do not expose the Streamlit port to an untrusted network.
# Question2
