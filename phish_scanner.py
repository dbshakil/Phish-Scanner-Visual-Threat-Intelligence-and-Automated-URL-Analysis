
from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import requests
import csv
import base64
import re
from werkzeug.utils import secure_filename
from flask import send_from_directory
import threading
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()






# Serve screenshots statically
@app.route('/screenshots/<path:filename>')
def serve_screenshot(filename):
    return send_from_directory(SCREENSHOT_DIR, filename)


# Screenshot and LLM endpoints
SCREENSHOT_ENDPOINT = 'http://localhost:3000/screenshot'
LLM_ENDPOINT = 'http://localhost:11434/v1/chat/completions'
LLM_MODEL = 'qwen3-vl:4b'
SCREENSHOT_DIR = os.path.join(tempfile.gettempdir(), 'webapp_screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def sanitize_filename(url):
    name = re.sub(r'^https?://', '', url)
    name = re.sub(r'[^a-zA-Z0-9._-]', '_', name)
    return name[:100]

def save_screenshot(url, out_path):
    payload = {"url": url}
    try:
        resp = requests.post(SCREENSHOT_ENDPOINT, json=payload, timeout=30)
        if resp.status_code == 200:
            with open(out_path, 'wb') as f:
                f.write(resp.content)
            return True
        else:
            return False
    except Exception:
        return False

def extract_brief_info_from_image(image_path):
    with open(image_path, 'rb') as img_file:
        img_bytes = img_file.read()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    prompt = (
        "Analyze the provided screenshot of a web page. "
        "Extract the following in a single line, separated by | (pipe):\n"
        "1. The main brand name or organization (if visible, otherwise 'Unknown').\n"
        "2. A one-line description of the page's purpose or main message.\n"
        "3. The literal string 'URL' (the script will append the actual URL).\n"
        "Format: Brand Name | One-line Description | URL\n"
        "Return only the single line, nothing else."
    )
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                    {"type": "text", "text": prompt}
                ]
            }
        ]
    }
    try:
        resp = requests.post(LLM_ENDPOINT, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            line = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
            return line
        else:
            return None
    except Exception:
        return None

def process_url(url):
    # Block URLs ending with dangerous file extensions
    blocked_exts = ['.exe', '.bat', '.msi', '.cmd', '.scr', '.pif', '.com', '.cpl', '.js', '.vbs', '.wsf', '.jse', '.lnk', '.ps1']
    url_lower = url.lower()
    if any(url_lower.endswith(ext) for ext in blocked_exts):
        return {
            'brand': 'Blocked',
            'description': 'Blocked: executable or script file',
            'url': url,
            'screenshot_name': None,
        }

    fname = sanitize_filename(url) + ".png"
    out_path = os.path.join(SCREENSHOT_DIR, fname)
    if not os.path.exists(out_path):
        ok = save_screenshot(url, out_path)
        if not ok:
            return {
                'brand': 'Unknown',
                'description': 'Screenshot failed',
                'url': url,
                'screenshot_name': None,
            }
    line = extract_brief_info_from_image(out_path)
    if line and '|' in line:
        parts = line.split('|')
        if len(parts) == 3:
            return {
                'brand': parts[0].strip(),
                'description': parts[1].strip(),
                'url': url,
                'screenshot_name': fname,
            }
        else:
            return {
                'brand': 'Unknown',
                'description': line.strip(),
                'url': url,
                'screenshot_name': fname,
            }
    else:
        return {
            'brand': 'Unknown',
            'description': 'No details extracted',
            'url': url,
            'screenshot_name': fname,
        }

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    # openphish_rows is now always empty; all data comes from openphish_status.json
    openphish_rows = []
    if request.method == 'POST':
        url = request.form.get('url')
        file = request.files.get('file')
        urls = []
        if url:
            urls.append(url.strip())
        if file and file.filename.endswith('.txt'):
            content = file.read().decode('utf-8')
            urls += [line.strip() for line in content.splitlines() if line.strip()]
        for u in urls:
            results.append(process_url(u))
    return render_template('index.html', results=results, openphish_rows=openphish_rows)

@app.route('/export', methods=['POST'])
def export():
    data = request.json.get('results', [])
    fd, path = tempfile.mkstemp(suffix='.csv')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Brand Name', 'Description', 'URL'])
        for row in data:
            writer.writerow([row['brand'], row['description'], row['url']])
    return send_file(path, as_attachment=True, download_name='results.csv')

if __name__ == '__main__':
    app.run(debug=True)
