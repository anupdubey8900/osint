import asyncio
import time
import sqlite3
import re
import os
from flask import Flask, render_template_string, request, jsonify
from telethon.sync import TelegramClient

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
API_ID = 34179263
API_HASH = "6a54e9a94340b6a6983df4b7acfccd00"
SESSION_NAME = 'termux_osint_session'  
TARGET_BOT = 'utkarsh_hackerr_bot'  
DB_NAME = 'anurag_data.db'

# ==========================================
# 🧹 SMART TEXT CLEANER & PREMIUM BOX FORMATTER
# ==========================================
def clean_bot_data(raw_text):
    # Faltu words, ads, aur stats ko list mein daala hai taaki hide ho jayein
    junk_phrases = [
        "hiteckgroop", "bot is deleted", "free version", "1.8 billion", 
        "subscription is over", "mirror (", "request:", "subjects made:", 
        "number of results:", "the number of leaks:", "search time:", 
        "in october 2023", "at the beginning of 2025", "database size:"
    ]

    lines = raw_text.split('\n')
    boxes = []
    current_box = []
    
    for line in lines:
        line_str = line.strip()
        
        # Agar blank line aayi, toh naya box shuru karo (Isse har person alag box me aayega)
        if not line_str:
            if current_box:
                boxes.append(current_box)
                current_box = []
            continue
            
        # Junk words filter
        if any(j in line_str.lower() for j in junk_phrases):
            continue
            
        # Lambi paragraphs filter (jo faltu ki details aati hain)
        if len(line_str) > 90 and ':' not in line_str[:20]:
            continue
            
        # Agar SOURCE ka naam aaya, toh naya box banao
        if "SOURCE:" in line_str.upper() or "SOURCE :" in line_str.upper():
            if current_box:
                boxes.append(current_box)
                current_box = []
                
        current_box.append(line_str)
        
    if current_box:
        boxes.append(current_box)
        
    final_html = ""
    
    # PREMIUM CSS FOR BOXES
    box_style = (
        "position: relative; padding: 22px 25px; margin-bottom: 25px; "
        "background: linear-gradient(145deg, rgba(5, 15, 10, 0.8) 0%, rgba(0, 0, 0, 0.9) 100%); "
        "box-shadow: 0 10px 30px -10px rgba(0, 255, 170, 0.15), inset 0 0 0 1px rgba(0, 255, 170, 0.2); "
        "border-radius: 12px; display: block; word-break: break-word; font-family: 'Fira Code', monospace; "
        "overflow: hidden; transition: transform 0.3s ease;"
    )
    
    for box_lines in boxes:
        box_html = ""
        for line_str in box_lines:
            # Emoji hatane aur text saaf karne ka logic
            clean_line = re.sub(r'^[^\w\s\[\]]+', '', line_str).strip()
            
            if ':' in clean_line:
                parts = clean_line.split(':', 1)
                key = parts[0].strip()
                val = parts[1].strip()
                
                if "SOURCE" in key.upper():
                    box_html += f"<div style='color: #ffcc00; font-weight: 800; font-size: 16px; margin-bottom: 15px; display: flex; align-items: center; gap: 10px;'><span style='background: #ffcc00; color: #000; padding: 3px 8px; border-radius: 4px; font-size: 11px; letter-spacing: 1px;'>SOURCE</span> {val}</div><hr style='border: 0; border-top: 1px dashed rgba(255,255,255,0.1); margin: 15px 0;'>"
                else:
                    box_html += f"<div style='margin-bottom: 10px; font-size: 15px; line-height: 1.5;'><span style='color: #00ffaa; font-weight: 600;'>{key}:</span> <span style='color: #e2e8f0;'>{val}</span></div>"
            else:
                if clean_line:
                    box_html += f"<div style='color: #cbd5e1; font-size: 14px; margin-bottom: 8px; line-height: 1.5;'>{clean_line}</div>"
                    
        if box_html:
            # Neon Green Accent Line (Left Side)
            accent = "<div style='position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: #00ffaa; box-shadow: 0 0 15px #00ffaa;'></div>"
            final_html += f"<div style='{box_style}' onmouseover=\"this.style.transform='translateY(-2px)'\" onmouseout=\"this.style.transform='translateY(0)'\">{accent}{box_html}</div>"
            
    return final_html

# ==========================================
# 🗄️ DATABASE SETUP & SEARCH
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  command TEXT,
                  response TEXT,
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_log(cmd, response):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO logs (command, response) VALUES (?, ?)", (cmd, response))
        conn.commit()
        conn.close()
    except: pass

def search_log(query):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT response FROM logs WHERE command LIKE ? ORDER BY id DESC", (f'%{query}%',))
        all_rows = c.fetchall()
        conn.close()
        
        if not all_rows: return None
        
        valid_records = []
        seen = set()

        for row in all_rows:
            text = row[0]
            if not text: continue
            text_hash = hash(text)
            if text_hash in seen: continue
            seen.add(text_hash)
            valid_records.append(text)
        
        if not valid_records: return None
        return "".join(valid_records)
    except: return None

# ==========================================
# 🎨 UI CODE
# ==========================================
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>UTKARSH | CYBER OSINT</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Fira+Code:wght@400;500;600&display=swap');
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: 'Outfit', sans-serif;
            background-color: #030712;
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(0, 255, 170, 0.05), transparent 30%),
                radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.08), transparent 30%);
            color: #e2e8f0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            position: relative;
        }

        .grid-bg {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background-size: 40px 40px;
            background-image: linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
                              linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
            z-index: -1; pointer-events: none;
        }

        .dashboard {
            background: rgba(10, 15, 20, 0.75); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            width: 100%; max-width: 1300px; height: 92vh; border-radius: 28px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.1);
            display: flex; overflow: hidden; z-index: 1; margin: 20px; position: relative;
        }

        .sidebar {
            width: 290px; background: rgba(0, 5, 10, 0.5);
            border-right: 1px solid rgba(255, 255, 255, 0.05); padding: 40px 30px;
            display: flex; flex-direction: column;
        }
        .brand {
            display: flex; align-items: center; gap: 15px; font-size: 24px; font-weight: 800; color: #fff;
            letter-spacing: 1px; margin-bottom: 50px;
        }
        .brand-icon {
            background: linear-gradient(135deg, #0ea5e9, #6366f1); color: white; width: 45px; height: 45px;
            border-radius: 14px; display: flex; align-items: center; justify-content: center;
            font-size: 22px; box-shadow: 0 0 20px rgba(14, 165, 233, 0.4); flex-shrink: 0;
        }

        .nav-label { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 2.5px; margin-bottom: 15px; padding-left: 5px; }
        .nav-group { display: flex; flex-direction: column; gap: 12px; }
        
        .nav-btn {
            width: 100%; background: transparent; border: 1px solid transparent; padding: 15px 20px; border-radius: 14px; font-size: 15px; font-weight: 600;
            color: #94a3b8; text-align: left; cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; gap: 12px;
        }
        .nav-btn:hover { background: rgba(255, 255, 255, 0.03); color: #e2e8f0; }
        .nav-btn.active {
            background: rgba(0, 255, 170, 0.1); border: 1px solid rgba(0, 255, 170, 0.3);
            color: #00ffaa; box-shadow: inset 0 0 20px rgba(0, 255, 170, 0.05);
        }

        .buy-tools-btn {
            margin-top: auto; background: linear-gradient(135deg, #00b09b, #96c93d); color: #000; border: none; padding: 18px; border-radius: 16px;
            font-size: 15px; font-weight: 800; cursor: pointer; text-align: center; display: flex; align-items: center; justify-content: center; gap: 10px;
            box-shadow: 0 10px 25px rgba(0, 255, 170, 0.2); transition: 0.3s;
        }
        .buy-tools-btn:hover { transform: translateY(-3px); box-shadow: 0 15px 30px rgba(0, 255, 170, 0.4); }

        .main { flex: 1; display: flex; flex-direction: column; padding: 40px 50px; overflow: hidden; position: relative; }

        .page-header { margin-bottom: 30px; }
        .page-title { font-size: 36px; font-weight: 800; color: #fff; letter-spacing: -0.5px; margin-bottom: 8px;}
        .page-desc { color: #94a3b8; font-size: 15px; font-weight: 400; }

        .search-wrapper {
            background: rgba(0, 0, 0, 0.4); padding: 12px; border-radius: 22px; border: 1px solid rgba(255, 255, 255, 0.08);
            display: flex; gap: 12px; margin-bottom: 30px; box-shadow: inset 0 2px 5px rgba(0,0,0,0.5); transition: all 0.3s ease;
        }
        .search-wrapper:focus-within { border-color: rgba(0, 255, 170, 0.5); box-shadow: 0 0 25px rgba(0, 255, 170, 0.15), inset 0 2px 5px rgba(0,0,0,0.5); }
        .search-input { flex: 1; border: none; background: transparent; padding: 15px 20px; font-size: 18px; font-weight: 600; color: #00ffaa; outline: none; font-family: 'Fira Code', monospace; letter-spacing: 1.5px; width: 100%;}
        .search-input::placeholder { color: #475569; font-family: 'Outfit', sans-serif; letter-spacing: 0; font-weight: 400;}
        
        .search-btn {
            background: #fff; color: #0f172a; border: none; padding: 0 50px; border-radius: 16px; font-size: 16px; font-weight: 800;
            cursor: pointer; transition: 0.3s; text-transform: uppercase; letter-spacing: 1px; flex-shrink: 0;
        }
        .search-btn:hover { background: #00ffaa; transform: scale(1.03); box-shadow: 0 0 20px rgba(0, 255, 170, 0.4); }

        .results-container {
            flex: 1; background: rgba(2, 6, 15, 0.5); border-radius: 24px; border: 1px solid rgba(255, 255, 255, 0.05);
            display: flex; flex-direction: column; overflow: hidden; position: relative;
        }

        .result-header {
            padding: 20px 30px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); display: flex; justify-content: space-between; align-items: center; background: rgba(0, 0, 0, 0.2);
        }
        .result-title { font-size: 14px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 1.5px; }
        
        .copy-btn {
            background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); color: #e2e8f0;
            padding: 10px 18px; border-radius: 10px; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.3s; display: flex; align-items: center; gap: 8px;
        }
        .copy-btn:hover { background: rgba(255, 255, 255, 0.15); color: #fff; }
        .copy-btn.copied { background: rgba(0, 255, 170, 0.2); color: #00ffaa; border-color: rgba(0, 255, 170, 0.4); }

        .result-body { padding: 30px 30px 80px 30px; overflow-y: auto; flex: 1; scrollbar-width: thin; scrollbar-color: #475569 transparent; }
        .result-body::-webkit-scrollbar { width: 6px; }
        .result-body::-webkit-scrollbar-thumb { background: #475569; border-radius: 10px; }
        
        .empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #475569; text-align: center;}
        .error-text { color: #ff3366 !important; text-shadow: 0 0 15px rgba(255, 51, 102, 0.3) !important; font-weight: 500; font-family: 'Outfit', sans-serif; text-align: center; margin-top: 20px;}

        .loader-wrapper { display: none; text-align: center; padding: 40px 0; height: 100%; flex-direction: column; justify-content: center; align-items: center; }
        .spinner { width: 60px; height: 60px; border: 4px solid rgba(255, 255, 255, 0.05); border-top: 4px solid #00ffaa; border-right: 4px solid #0ea5e9; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 20px auto; }
        .scan-text { font-family: 'Fira Code', monospace; color: #00ffaa; font-size: 15px; letter-spacing: 2px; animation: pulse 1.5s infinite; font-weight: 600;}
        
        /* FIX FOR WATERMARK POSITION */
        .watermark {
            position: absolute; bottom: 20px; right: 35px; color: rgba(255, 255, 255, 0.15);
            font-size: 14px; font-weight: 800; letter-spacing: 4px; text-transform: uppercase;
            z-index: 100; pointer-events: none;
        }

        @keyframes spin { 100% { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

        /* ANDROID / MOBILE RESPONSIVENESS FIX */
        @media (max-width: 768px) {
            body { align-items: flex-start; display: block; overflow-x: hidden; }
            .dashboard { flex-direction: column; height: auto; min-height: 100vh; border-radius: 0; border: none; margin: 0; box-shadow: none; }
            .sidebar { width: 100%; padding: 20px 25px; border-right: none; border-bottom: 1px solid rgba(255, 255, 255, 0.05); flex-direction: row; align-items: center; justify-content: space-between; flex-wrap: wrap; background: rgba(2, 6, 23, 0.95); }
            .brand { margin-bottom: 0; font-size: 20px; }
            .brand-icon { width: 38px; height: 38px; font-size: 18px; }
            .nav-label { display: none; }
            .nav-group { flex-direction: row; width: 100%; margin-top: 15px; }
            .nav-btn { flex: 1; padding: 12px; justify-content: center; font-size: 14px; margin-bottom: 0; }
            .buy-tools-btn { display: none; } 
            .main { padding: 25px 20px; overflow: visible; display: flex; flex-direction: column; flex: 1; }
            .page-header { margin-bottom: 20px; }
            .page-title { font-size: 28px; }
            .page-desc { font-size: 14px; }
            .search-wrapper { flex-direction: column; background: transparent; border: none; box-shadow: none; padding: 0; gap: 12px; }
            .search-input { background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 18px 20px; font-size: 16px; }
            .search-btn { padding: 18px; border-radius: 16px; font-size: 16px; width: 100%; }
            .results-container { min-height: 65vh; height: auto; flex: none; border-radius: 20px;}
            .result-header { flex-direction: column; gap: 12px; align-items: flex-start; padding: 20px; }
            .copy-btn { width: 100%; justify-content: center; padding: 14px; }
            .result-body { padding: 20px 20px 60px 20px; }
            .watermark { position: relative; text-align: center; bottom: 0; right: 0; margin-top: 30px; padding-bottom: 20px; font-size: 12px; } 
        }
    </style>
</head>
<body>
    <div class="grid-bg"></div>

    <div class="dashboard">
        <div class="sidebar">
            <div class="brand">
                <div class="brand-icon">⚡</div> UTKARSH
            </div>

            <div class="nav-label">Extraction Protocol</div>
            <div class="nav-group">
                <button class="nav-btn active" id="btn-live" onclick="setMode('live')"><span style="font-size: 18px;">📡</span> Live Scan</button>
                <button class="nav-btn" id="btn-db" onclick="setMode('db')"><span style="font-size: 18px;">🗄️</span> DB Vault</button>
            </div>

            <button class="buy-tools-btn" onclick="buyTools()">🛒 Premium Tools</button>
        </div>

        <div class="main">
            <div class="page-header">
                <h1 class="page-title" id="pageTitle">Live Data Nodes</h1>
                <p class="page-desc" id="pageDesc">Execute real-time targeted queries to external central servers.</p>
            </div>

            <div class="search-wrapper">
                <input type="number" id="cmdInput" class="search-input" placeholder="Enter Target Number..." autocomplete="off">
                <button class="search-btn" onclick="executeSearch()">EXECUTE</button>
            </div>

            <div class="results-container">
                <div class="result-header">
                    <span class="result-title" id="resHeaderTitle">SYSTEM STANDBY</span>
                    <button class="copy-btn" id="copyBtn" onclick="copyData()" style="display:none;">📋 Copy Payload</button>
                </div>
                
                <div class="result-body" id="resultBody">
                    <div class="empty-state" id="initialState">
                        <svg width="55" height="55" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom:15px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                        <p style="font-size: 15px;">Awaiting command parameters...</p>
                    </div>
                    
                    <div class="loader-wrapper" id="loaderState">
                        <div class="spinner"></div>
                        <div class="scan-text" id="scanText">FETCHING ALL PAGES... PLEASE WAIT...</div>
                    </div>

                    <div id="finalData" style="display:none; animation: slideUp 0.3s ease-out;"></div>
                </div>
            </div>
            <div class="watermark">MADE BY UTKARSH</div>
        </div>
    </div>

    <script>
        let mode = 'live';

        function setMode(m) {
            mode = m;
            document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById('btn-' + m).classList.add('active');
            
            document.getElementById('pageTitle').innerText = m === 'live' ? 'Live Data Nodes' : 'Encrypted Vault';
            document.getElementById('pageDesc').innerText = m === 'live' ? 'Execute real-time targeted queries to external central servers.' : 'Access previously decrypted local records.';
            document.getElementById('cmdInput').value = '';
            resetView();
        }

        function resetView() {
            document.getElementById('initialState').style.display = 'flex';
            document.getElementById('loaderState').style.display = 'none';
            document.getElementById('finalData').style.display = 'none';
            document.getElementById('copyBtn').style.display = 'none';
            document.getElementById('resHeaderTitle').innerText = 'SYSTEM STANDBY';
            document.getElementById('resHeaderTitle').style.color = '#94a3b8';
        }

        function executeSearch() {
            let val = document.getElementById('cmdInput').value.trim();
            if(!val) return;

            document.getElementById('initialState').style.display = 'none';
            document.getElementById('finalData').style.display = 'none';
            document.getElementById('copyBtn').style.display = 'none';
            document.getElementById('loaderState').style.display = 'flex';
            document.getElementById('resHeaderTitle').innerText = `TARGET ACQUIRED: ${val}`;
            document.getElementById('resHeaderTitle').style.color = '#fff';
            document.getElementById('scanText').innerText = mode === 'live' ? 'FETCHING ALL PAGES... PLEASE WAIT...' : 'SCANNING DB...';

            fetch(mode === 'live' ? '/run_live' : '/search_db', {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({cmd: val})
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('loaderState').style.display = 'none';
                let dataBox = document.getElementById('finalData');
                dataBox.style.display = 'block';
                
                if(data.found) {
                    document.getElementById('resHeaderTitle').innerText = `✅ DECRYPTION SUCCESSFUL`;
                    document.getElementById('resHeaderTitle').style.color = '#00ffaa';
                    document.getElementById('copyBtn').style.display = 'flex';
                    dataBox.classList.remove('error-text');
                    dataBox.innerHTML = data.reply;
                } else {
                    document.getElementById('resHeaderTitle').innerText = `❌ DATA NOT FOUND`;
                    document.getElementById('resHeaderTitle').style.color = '#ff3366';
                    dataBox.classList.add('error-text');
                    dataBox.innerHTML = "DATA NOT FOUND!<br><br><span style='color:#94a3b8; font-size:14px;'>Target record does not exist or bot did not reply.</span>";
                }
            })
            .catch(err => {
                document.getElementById('loaderState').style.display = 'none';
                let dataBox = document.getElementById('finalData');
                dataBox.style.display = 'block';
                dataBox.classList.add('error-text');
                dataBox.innerHTML = "FATAL ERROR: Connection failed. Server/Network issue.";
            });
        }

        function copyData() {
            let dataText = document.getElementById('finalData').innerText;
            navigator.clipboard.writeText(dataText).then(() => {
                let btn = document.getElementById('copyBtn');
                btn.innerHTML = '✅ Copied!';
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.innerHTML = '📋 Copy Payload';
                    btn.classList.remove('copied');
                }, 2000);
            });
        }

        function buyTools() { window.open('https://t.me/utkarsh_hackerr_bot', '_blank'); }

        document.getElementById('cmdInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault(); 
                executeSearch();
            }
        });
    </script>
</body>
</html>
"""

app = Flask(__name__)
init_db()

@app.route('/')
def index(): 
    return render_template_string(HTML_CODE)

@app.route('/run_live', methods=['POST'])
def run_live():
    data = request.json
    cmd = data.get('cmd').strip()
    print(f"\n🚀 [DEEP SCAN] Fetching Info: {cmd}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def fetch_all_pages():
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.connect()
        await client.send_message(TARGET_BOT, cmd)
        
        collected_html = []
        seen_clean_texts = set()
        
        target_msg = None
        for _ in range(30): 
            await asyncio.sleep(1)
            msgs = await client.get_messages(TARGET_BOT, limit=3)
            for m in msgs:
                if not m.out and m.message:
                    text_lower = m.message.lower()
                    if "processing" not in text_lower and "wait" not in text_lower:
                        target_msg = m
                        break
            if target_msg:
                break
                
        if not target_msg:
            print("❌ Target msg not found.")
            await client.disconnect()
            return []

        while True:
            raw_text = target_msg.message or ""
            clean = clean_bot_data(raw_text)
            
            if clean and clean not in seen_clean_texts:
                seen_clean_texts.add(clean)
                collected_html.append(clean)
                print(f"✅ Page fetched successfully!")
            
            is_last_page = False
            has_next_btn = False
            next_btn = None
            
            if target_msg.buttons:
                for row in target_msg.buttons:
                    for btn in row:
                        if btn.text:
                            m = re.search(r'(\d+)\s*[\/\\]\s*(\d+)', btn.text)
                            if m and int(m.group(1)) >= int(m.group(2)):
                                is_last_page = True
                            
                            if '➡' in btn.text:
                                has_next_btn = True
                                next_btn = btn
            
            if is_last_page or not has_next_btn or not next_btn:
                print("🏁 End of pages reached.")
                break
                
            old_text = raw_text
            
            try:
                print("➡️ Clicking Next button...")
                await next_btn.click()
            except Exception as e:
                print("❌ Button Click Error:", e)
                break
                
            changed = False
            for _ in range(30): 
                await asyncio.sleep(1)
                check_msg = await client.get_messages(TARGET_BOT, ids=target_msg.id)
                if check_msg and check_msg.message:
                    new_text = check_msg.message
                    if new_text != old_text and "processing" not in new_text.lower() and "wait" not in new_text.lower():
                        target_msg = check_msg
                        changed = True
                        break
            
            if not changed:
                print("⚠️ Timeout waiting for next page edit.")
                break
                
        await client.disconnect()
        return collected_html
        
    res_list = loop.run_until_complete(fetch_all_pages())
    loop.close()
    
    if res_list:
        final_reply = "".join(res_list)
        save_log(cmd, final_reply)
        return jsonify({'reply': final_reply, 'found': True})
    else:
        return jsonify({'reply': "Data Not Found", 'found': False})

@app.route('/search_db', methods=['POST'])
def search_db():
    data = request.json
    q = data.get('cmd')
    res = search_log(q)
    return jsonify({'reply': res if res else "Data Not Found", 'found': bool(res)})

# ==========================================
# 🔐 TERMINAL LOGIN SYSTEM
# ==========================================
async def login_system():
    print("\n=========================================")
    print("   🛡️ OSINT SYSTEM INITIALIZATION 🛡️   ")
    print("=========================================\n")
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("⚠️ FIRST TIME SETUP: LOGIN REQUIRED!")
        phone = input("👉 Enter Phone Number (e.g. +919876543210): ")
        await client.send_code_request(phone)
        
        print("\n📩 OTP sent to your Telegram App!")
        otp = input("👉 Enter the OTP: ")
        
        try:
            await client.sign_in(phone, otp)
            print("\n✅ LOGIN SUCCESSFUL! Session Saved.")
        except Exception as e:
            print(f"\n❌ LOGIN FAILED: {e}")
            await client.disconnect()
            os._exit(1)
    else:
        print("✅ Telegram Session Active. Bot Ready.")
        
    await client.disconnect()

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(login_system())
    
    print("\n" + "="*50)
    print("🚀 SERVER IS RUNNING PERFECTLY!")
    print("👉 OPEN YOUR CHROME/BROWSER AND TYPE THIS LINK:")
    print("🌐 http://127.0.0.1:5000")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
