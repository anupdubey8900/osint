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
# 🧹 SMART TEXT CLEANER
# ==========================================
def clean_bot_data(raw_text):
    lines = raw_text.split('\n')
    clean_lines = []
    
    ads = [
        "hiteckgroop", "bot is deleted", "free version", "1.8 billion",
        "subscription is over", "please note that", "mirror ("
    ]
    
    for line in lines:
        if not any(ad in line.lower() for ad in ads):
            clean_lines.append(line)
            
    return '\n'.join(clean_lines).strip()

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
            clean_text = clean_bot_data(text)
            if not clean_text: continue
            
            text_hash = hash(clean_text)
            if text_hash in seen: continue
            seen.add(text_hash)
            valid_records.append(clean_text)
        
        if not valid_records: return None
        return "\n\n" + ("━"*40) + "\n\n".join(valid_records)
    except: return None

# ==========================================
# 🎨 UI CODE (PC & ANDROID APP DESIGN + SCROLL FIX)
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
                radial-gradient(circle at 15% 50%, rgba(56, 189, 248, 0.08), transparent 25%),
                radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.08), transparent 25%);
            color: #e2e8f0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
            position: relative;
        }

        .watermark {
            position: absolute; bottom: 15px; right: 25px; color: rgba(255, 255, 255, 0.2);
            font-size: 13px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;
            z-index: 100; pointer-events: none; text-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
        }

        .grid-bg {
            position: absolute; top: 0; left: 0; width: 100vw; height: 100vh;
            background-size: 40px 40px;
            background-image: linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
                              linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
            z-index: -1; pointer-events: none;
            mask-image: linear-gradient(to bottom, rgba(0,0,0,1), rgba(0,0,0,0));
            -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,1), rgba(0,0,0,0));
        }

        /* ---------------- MAIN DASHBOARD ---------------- */
        .dashboard {
            background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            width: 100%; max-width: 1000px; height: 85vh; border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
            display: flex; overflow: hidden; z-index: 1;
        }

        /* ---------------- SIDEBAR (PC) / HEADER (MOBILE) ---------------- */
        .sidebar {
            width: 280px; background: rgba(2, 6, 23, 0.4);
            border-right: 1px solid rgba(255, 255, 255, 0.05); padding: 35px 25px;
            display: flex; flex-direction: column;
        }
        .brand {
            display: flex; align-items: center; gap: 15px; font-size: 22px; font-weight: 800; color: #fff;
            letter-spacing: 1px; margin-bottom: 50px;
        }
        .brand-icon {
            background: linear-gradient(135deg, #0ea5e9, #6366f1); color: white; width: 42px; height: 42px;
            border-radius: 12px; display: flex; align-items: center; justify-content: center;
            font-size: 20px; box-shadow: 0 0 15px rgba(14, 165, 233, 0.4); flex-shrink: 0;
        }

        .nav-label { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; padding-left: 5px; }
        
        .nav-group { display: flex; flex-direction: column; gap: 10px; }
        
        .nav-btn {
            width: 100%; background: transparent; border: 1px solid transparent; padding: 14px 18px; border-radius: 12px; font-size: 14px; font-weight: 600;
            color: #94a3b8; text-align: left; cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; gap: 12px;
        }
        .nav-btn:hover { background: rgba(255, 255, 255, 0.03); color: #e2e8f0; }
        .nav-btn.active {
            background: rgba(14, 165, 233, 0.1); border: 1px solid rgba(14, 165, 233, 0.3);
            color: #38bdf8; box-shadow: inset 0 0 15px rgba(14, 165, 233, 0.05);
        }

        .buy-tools-btn {
            margin-top: auto; background: linear-gradient(135deg, #10b981, #047857); color: #fff; border: none; padding: 16px; border-radius: 14px;
            font-size: 14px; font-weight: 600; cursor: pointer; text-align: center; display: flex; align-items: center; justify-content: center; gap: 10px;
            box-shadow: 0 8px 20px rgba(16, 185, 129, 0.25); transition: 0.3s; position: relative; overflow: hidden;
        }

        /* ---------------- MAIN CONTENT ---------------- */
        .main { flex: 1; display: flex; flex-direction: column; padding: 40px; overflow: hidden; position: relative; }

        .page-header { margin-bottom: 25px; }
        .page-title { font-size: 32px; font-weight: 800; color: #fff; letter-spacing: -0.5px; }
        .page-desc { color: #94a3b8; font-size: 14px; margin-top: 5px; font-weight: 300; }

        .search-wrapper {
            background: rgba(0, 0, 0, 0.3); padding: 8px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex; gap: 10px; margin-bottom: 25px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5); transition: all 0.3s ease;
        }
        .search-wrapper:focus-within { border-color: rgba(56, 189, 248, 0.5); box-shadow: 0 0 20px rgba(56, 189, 248, 0.15), inset 0 2px 4px rgba(0,0,0,0.5); }
        .search-input { flex: 1; border: none; background: transparent; padding: 15px 20px; font-size: 16px; font-weight: 500; color: #fff; outline: none; font-family: 'Fira Code', monospace; letter-spacing: 1px; width: 100%;}
        .search-input::placeholder { color: #475569; font-family: 'Outfit', sans-serif; letter-spacing: 0; }
        
        .search-btn {
            background: #e2e8f0; color: #0f172a; border: none; padding: 0 35px; border-radius: 14px; font-size: 15px; font-weight: 800;
            cursor: pointer; transition: 0.3s; text-transform: uppercase; letter-spacing: 1px; flex-shrink: 0;
        }
        .search-btn:hover { background: #fff; transform: scale(1.02); box-shadow: 0 0 15px rgba(255,255,255,0.2); }

        .results-container {
            flex: 1; background: rgba(2, 6, 23, 0.4); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.05);
            display: flex; flex-direction: column; overflow: hidden; position: relative;
        }

        .result-header {
            padding: 15px 25px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.02);
        }
        .result-title { font-size: 12px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
        
        .copy-btn {
            background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); color: #cbd5e1;
            padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; transition: 0.3s; display: flex; align-items: center; gap: 6px;
        }
        .copy-btn:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }
        .copy-btn.copied { background: rgba(16, 185, 129, 0.2); color: #10b981; border-color: rgba(16, 185, 129, 0.4); }

        /* SCROLL CUT FIX: Increased padding-bottom to 60px so the text clears the border completely */
        .result-body { padding: 25px 25px 60px 25px; overflow-y: auto; flex: 1; scrollbar-width: thin; scrollbar-color: #334155 transparent; }
        .result-body::-webkit-scrollbar { width: 4px; }
        .result-body::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
        
        .data-text { font-family: 'Fira Code', monospace; font-size: 13px; line-height: 1.8; color: #38bdf8; white-space: pre-wrap; word-wrap: break-word; text-shadow: 0 0 10px rgba(56, 189, 248, 0.2); }

        .empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #475569; text-align: center;}
        .error-text { color: #f43f5e !important; text-shadow: 0 0 10px rgba(244, 63, 94, 0.2) !important; font-weight: 500; font-family: 'Outfit', sans-serif; }

        .loader-wrapper { display: none; text-align: center; padding: 40px 0; height: 100%; flex-direction: column; justify-content: center; align-items: center; }
        .spinner { width: 40px; height: 40px; border: 3px solid rgba(255, 255, 255, 0.05); border-top: 3px solid #38bdf8; border-right: 3px solid #8b5cf6; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 15px auto; }
        .scan-text { font-family: 'Fira Code', monospace; color: #38bdf8; font-size: 12px; letter-spacing: 2px; animation: pulse 1.5s infinite; }
        
        @keyframes spin { 100% { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

        /* ==========================================
           📱 MOBILE ANDROID APP RESPONSIVENESS
           ========================================== */
        @media (max-width: 768px) {
            body { align-items: flex-start; }
            .watermark { display: none; } 
            
            .dashboard {
                flex-direction: column; height: 100vh; max-height: 100vh; border-radius: 0; border: none;
            }
            
            .sidebar {
                width: 100%; padding: 15px 20px; border-right: none; border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                flex-direction: row; align-items: center; justify-content: space-between; flex-wrap: wrap; background: rgba(2, 6, 23, 0.8);
            }
            .brand { margin-bottom: 0; font-size: 18px; }
            .brand-icon { width: 35px; height: 35px; font-size: 16px; }
            .nav-label { display: none; }
            
            .nav-group { flex-direction: row; width: 100%; margin-top: 15px; }
            .nav-btn { flex: 1; padding: 10px; justify-content: center; font-size: 13px; margin-bottom: 0; }
            
            .buy-tools-btn { display: none; } 
            
            /* SCROLL CUT FIX FOR MOBILE: Extra padding at bottom so navbar doesn't cover data */
            .main { padding: 20px 20px 40px 20px; overflow-y: auto; }
            .page-header { margin-bottom: 15px; }
            .page-title { font-size: 24px; }
            .page-desc { font-size: 13px; }
            
            .search-wrapper { flex-direction: column; background: transparent; border: none; box-shadow: none; padding: 0; gap: 10px; }
            .search-input { background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; }
            .search-btn { padding: 15px; border-radius: 12px; font-size: 14px; width: 100%; }
            
            .result-header { flex-direction: column; gap: 10px; align-items: flex-start; }
            .copy-btn { width: 100%; justify-content: center; }
            
            /* Extra scroll space for mobile screens */
            .result-body { padding-bottom: 80px; }
        }
    </style>
</head>
<body>
    <div class="watermark">Made by Utkarsh</div>
    <div class="grid-bg"></div>

    <div class="dashboard">
        <div class="sidebar">
            <div class="brand">
                <div class="brand-icon">⚡</div> UTKARSH
            </div>

            <div class="nav-label">Extraction Protocol</div>
            <div class="nav-group">
                <button class="nav-btn active" id="btn-live" onclick="setMode('live')"><span style="font-size: 16px;">📡</span> Live Scan</button>
                <button class="nav-btn" id="btn-db" onclick="setMode('db')"><span style="font-size: 16px;">🗄️</span> DB Vault</button>
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
                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom:15px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                        <p style="font-size: 13px;">Awaiting command parameters...</p>
                    </div>
                    
                    <div class="loader-wrapper" id="loaderState">
                        <div class="spinner"></div>
                        <div class="scan-text">CONNECTING...</div>
                    </div>

                    <div class="data-text" id="finalData" style="display:none; animation: slideUp 0.3s ease-out;"></div>
                </div>
            </div>
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
        }

        function executeSearch() {
            let val = document.getElementById('cmdInput').value.trim();
            if(!val) return;

            document.getElementById('initialState').style.display = 'none';
            document.getElementById('finalData').style.display = 'none';
            document.getElementById('copyBtn').style.display = 'none';
            document.getElementById('loaderState').style.display = 'flex';
            document.getElementById('resHeaderTitle').innerText = `TARGET ACQUIRED: ${val}`;
            document.querySelector('.scan-text').innerText = mode === 'live' ? 'BYPASSING SECURITY...' : 'SCANNING DB...';

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
                    document.getElementById('resHeaderTitle').style.color = '#38bdf8';
                    document.getElementById('copyBtn').style.display = 'flex';
                    dataBox.classList.remove('error-text');
                    dataBox.innerHTML = data.reply.replace(/\\n/g, '<br>');
                } else {
                    document.getElementById('resHeaderTitle').innerText = `❌ DATA NOT FOUND`;
                    document.getElementById('resHeaderTitle').style.color = '#f43f5e';
                    dataBox.classList.add('error-text');
                    
                    if(data.reply && data.reply !== "Data Not Found") {
                        dataBox.innerHTML = data.reply.replace(/\\n/g, '<br>');
                    } else {
                        dataBox.innerHTML = "DATA NOT FOUND!<br><br><span style='color:#94a3b8; font-size:13px;'>Target record does not exist or bot did not reply.</span>";
                    }
                }
            })
            .catch(err => {
                document.getElementById('loaderState').style.display = 'none';
                let dataBox = document.getElementById('finalData');
                dataBox.style.display = 'block';
                dataBox.classList.add('error-text');
                dataBox.innerHTML = "FATAL ERROR: Connection failed.";
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
    print(f"\n🚀 [INSTANT LIVE] Searching: {cmd} via {TARGET_BOT}")
    
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    final_reply = "Data Not Found"
    found = False

    try:
        with TelegramClient(SESSION_NAME, API_ID, API_HASH, loop=new_loop) as client:
            client.send_message(TARGET_BOT, cmd)
            start_time = time.time()
            collected_messages = []
            new_msg_found = False
            
            # FAST DUAL-CATCH POLLING (Max wait ~8 sec)
            for i in range(40): 
                time.sleep(0.2)
                msgs = client.get_messages(TARGET_BOT, limit=3)
                
                for msg in msgs:
                    if not msg.out and (msg.date.timestamp() > start_time - 1):
                        text = msg.message or ""
                        if text.lower().strip() in ["processing...", "wait...", "searching...", "please wait..."]: 
                            continue
                            
                        cleaned_text = clean_bot_data(text)
                        if cleaned_text and cleaned_text not in collected_messages: 
                            collected_messages.append(cleaned_text)
                            new_msg_found = True
                
                if new_msg_found:
                    time.sleep(0.5) 
                    msgs = client.get_messages(TARGET_BOT, limit=5)
                    for msg in msgs:
                        if not msg.out and (msg.date.timestamp() > start_time - 1):
                            text = msg.message or ""
                            cleaned_text = clean_bot_data(text)
                            if cleaned_text and cleaned_text not in collected_messages and text.lower().strip() not in ["processing...", "wait...", "searching...", "please wait..."]:
                                collected_messages.append(cleaned_text)
                    break 
            
            if collected_messages:
                final_reply = "\n\n".join(collected_messages)
                save_log(cmd, final_reply)
                found = True
            else:
                final_reply = "Data Not Found"

    except Exception as e:
        print(f"❌ ERROR: {e}")
        final_reply = "System Error"
    finally: 
        new_loop.close()
        
    return jsonify({'reply': final_reply, 'found': found})

@app.route('/search_db', methods=['POST'])
def search_db():
    data = request.json
    q = data.get('cmd')
    print(f"\n🔍 [DATABASE] Searching for: {q}")
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
    # Login check
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(login_system())
    
    # TERMUX / PC FRIENDLY STARTUP
    print("\n" + "="*50)
    print("🚀 SERVER IS RUNNING PERFECTLY!")
    print("👉 OPEN YOUR CHROME/BROWSER AND TYPE THIS LINK:")
    print("🌐 http://127.0.0.1:5000")
    print("="*50 + "\n")
    
    # Start web server automatically
    app.run(host='0.0.0.0', port=5000, debug=False)
