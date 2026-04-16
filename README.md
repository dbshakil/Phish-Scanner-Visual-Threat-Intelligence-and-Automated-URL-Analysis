# Phish Scanner

A simple Flask web application to scan and analyze phishing URLs. Upload a text file of URLs or enter a single URL to get brand, description, and screenshot results.

## Features
- Scan a single URL or upload a .txt file of URLs
- Get brand, description, and screenshot for each URL
- Export results as CSV

## Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   source .venv/bin/activate
   python phish_scanner.py
   ```
3. Open your browser at [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Project Structure
- `phish_scanner.py` - Main Flask app
- `static/` - CSS styles
- `templates/` - HTML templates
- `screenshots/` - Saved screenshots

## Notes
- Requires a running screenshot service at `http://localhost:3000/screenshot`
- Requires a running LLM service at `http://localhost:11434/v1/chat/completions`

---

## Dependencies

| Component | Purpose | Default address |
|-----------|---------|-----------------|
| Python 3.10+ | Runtime | — |
| Flask | Web framework | — |
| requests | HTTP client | — |
| [Browserless](https://github.com/browserless/browserless) | Headless Chromium screenshot API | `http://localhost:3000` |
| [Ollama](https://ollama.com/) with `qwen3-vl:4b` model | Vision-language model for brand/description extraction | `http://localhost:11434` |

Install Python packages:

```bash
pip install -r requirements.txt
```

---

## Running the Web App

```bash
# Activate the virtual environment first
source .venv/bin/activate

python phish_scanner.py
# App runs at http://127.0.0.1:5000
```

### Usage

1. **Single URL** — paste the URL into the text field and click **Get Details**.
2. **Bulk** — upload a plain `.txt` file with one URL per line (use `bulk.txt` as a template).
3. Results appear in a table with four columns:
   - **Brand Name** — the organisation impersonated on the page.
   - **Description** — one-line summary of the page's purpose.
   - **URL** — defanged and shortened (`http://` → `hxxp://`) to prevent accidental clicks.
   - **Screenshot** — a **Shot** pill button that opens the captured screenshot in a new tab.
4. Click **Export CSV** to download the full result set as `results.csv`.

---

## Running the CLI Batch Script

`batch_processor.py` fetches URLs directly from the OpenPhish public feed instead of taking manual input.

```bash
python batch_processor.py
```

- Screenshots are saved to `screenshots/`.
- Results are written incrementally to `brands.md` as a Markdown table.
- By default the script processes the first 15 URLs (edit the `[:15]` slice in `main()` to change this).

---

## Security Controls

### URL Safety Check
Before any URL is sent to Browserless, `process_url()` blocks requests to files with dangerous extensions:

`.exe` `.bat` `.msi` `.cmd` `.scr` `.pif` `.com` `.cpl` `.js` `.vbs` `.wsf` `.jse` `.lnk` `.ps1`

Blocked URLs are returned immediately with `Brand: Blocked` and never reach the browser.

### Defanged URL Display
All URLs shown in the UI are defanged:
- `http://` → `hxxp://`
- `https://` → `hxxps://`

URLs longer than 40 characters are truncated in the middle (`first18...last18`) to reduce visual footprint.

### No Direct Hyperlinks
URLs in the results table are **plain text only** — they are not rendered as clickable links.

---

## How the Extraction Works

1. **Screenshot** — the URL is POSTed to Browserless (`/screenshot`). Browserless navigates to the page with a real Chromium instance and returns a PNG image.

2. **Brand & Description** — the PNG is base64-encoded and sent to Ollama's OpenAI-compatible chat endpoint with the `qwen3-vl:4b` model. The prompt instructs the model to return a single pipe-delimited line:
   ```
   Brand Name | One-line description | URL
   ```

3. **Parsing** — the response is split on `|`. The first segment becomes the brand, the second the description, and the actual URL replaces the placeholder third segment.

---

## Filtering bulk.txt (utility)

To keep only UAE-related domains (`.ae`, `uae`, `-uae`) from a large list:

```bash
grep -iE '\.ae(/|$|\.)|-uae\b|uae' bulk.txt | sort -u > bulk_filtered.txt
```

---

## Configuration

All key constants are defined near the top of each file and can be changed without touching logic:

| Constant | File | Default |
|----------|------|---------|
| `SCREENSHOT_ENDPOINT` | `phish_scanner.py`, `batch_processor.py` | `http://localhost:3000/screenshot` |
| `LLM_ENDPOINT` | `phish_scanner.py`, `batch_processor.py` | `http://localhost:11434/v1/chat/completions` |
| `LLM_MODEL` | `phish_scanner.py`, `batch_processor.py` | `qwen3-vl:4b` |
| `FEED_URL` | `batch_processor.py` | OpenPhish public feed |
| `SCREENSHOT_DIR` | `phish_scanner.py` | OS temp dir / `webapp_screenshots` |
| `BRAND_MD` | `batch_processor.py` | `brands.md` |

---

## Notes

- Screenshots are cached on disk. If a screenshot already exists for a URL, it is reused and the page is not fetched again. Delete the `screenshots/` folder to force a refresh.
- The LLM has a 60-second timeout per request. Slow models or large pages may time out; the result will show "No details extracted" for those entries.
- This tool is intended for **threat intelligence research** in a controlled, offline environment. Do not use it to interact with live malicious pages without appropriate sandboxing.

## File Naming

- **phish_scanner.py** — Primary web application for interactive scanning of URLs.
- **batch_processor.py** — Command-line utility for batch processing of URL feeds.
- **bulk.txt** — Input file for bulk uploads via the web interface.
- **brands.md** — Output from batch processor runs.
