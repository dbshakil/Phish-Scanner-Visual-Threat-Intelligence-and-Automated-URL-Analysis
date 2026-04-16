# Phish Scanner - Visual Threat Intelligence and Automated URL Analysis

A simple Flask web application to scan and analyze phishing URLs. Enter a single URL or upload a .txt file of URLs to get brand, description, and screenshot results.

## Features
- Scan a single URL or upload a .txt file of URLs
- Get brand, description, and screenshot for each URL
- Export results as CSV

## Requirements
- Python 3.10+
- Flask
- requests
- [Browserless](https://github.com/browserless/browserless) (screenshot API, running at `http://localhost:3000/screenshot`)
- [Ollama](https://ollama.com/) with `qwen3-vl:4b` model (LLM API, running at `http://localhost:11434/v1/chat/completions`)

Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage
1. Activate your virtual environment (if using one):
   ```bash
   source .venv/bin/activate
   ```
2. Start the Flask app:
   ```bash
   python phish_scanner.py
   ```
3. Open your browser at [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Project Structure
- `phish_scanner.py` — Main Flask app
- `static/` — CSS styles
- `templates/` — HTML templates
- `screenshots/` — Saved screenshots

## How it Works
1. **Screenshot** — The URL is sent to Browserless, which returns a PNG screenshot.
2. **Brand & Description** — The screenshot is sent to the LLM (Ollama/qwen3-vl:4b) for brand and page summary extraction.
3. **Results** — Displayed in a table with brand, description, defanged URL, and screenshot. Results can be exported as CSV.

## Security Controls
- **URL Safety Check:** URLs with dangerous file extensions (e.g., `.exe`, `.js`, `.bat`, etc.) are blocked and not processed.
- **Defanged URLs:** URLs are displayed as `hxxp://` or `hxxps://` to prevent accidental clicks. Long URLs are truncated in the middle.
- **No Direct Hyperlinks:** URLs are shown as plain text, not clickable links.

## Notes
- Screenshots are cached on disk. Delete the `screenshots/` folder to force a refresh.
- The LLM has a 60-second timeout per request. Slow models or large pages may time out and show "No details extracted."
- This tool is intended for threat intelligence research in a controlled environment. Do not use it to interact with live malicious pages without proper sandboxing.
