
import asyncio
import sys
import json
import re
import httpx
from collections import deque
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --- 🛠️ CONFIGURATION ---

# 1. WhatsApp Bridge (Subprocess + REST)
WA_BRIDGE_PATH = r"D:\WHACK\whatsapp-mcp\whatsapp-bridge"
WA_API_URL = "http://localhost:8080/api/send"  

# 2. NASA (MCP)
CLEAN_NODE_PATH = r"C:\Program Files\nodejs\node.exe"
nasa_params = StdioServerParameters(
    command=CLEAN_NODE_PATH, 
    args=[r"D:\Spectra\NASA-MCP-server\dist\index.js"],
    env={"NASA_API_KEY": "kWiy0mz0ocWHh1zUIrqfTX6tzfYQRmOfob1ysWw2"}
)

# 3. GIS (MCP)
gis_params = StdioServerParameters(
    command=r"D:\Spectra\GIS-Real\.venv\Scripts\python.exe", 
    args=[r"D:\Spectra\GIS-Real\main.py"],
    env={"PYTHONUNBUFFERED": "1"}
)

# --- 🧠 HELPERS ---
def parse_stream_line(line):
    clean = line.strip()
    if not clean: return None
    # Parse logs like: [2025-12-12 20:05:37] <- 917259443981: Hello
    match = re.search(r"\[(.*?)\] (?:<-|←) (.*?): (.*)", clean)
    if match:
        ts, sender, text = match.groups()
        return {"sender": sender.strip(), "text": text.strip()}
    return None

def resolve_jid(sender_raw):
    sender = sender_raw.strip().replace("+", "").replace(" ", "")
    if "@" in sender: return sender
    if "-" in sender: return f"{sender}@g.us"
    # FIX: Use >= 15 because your ID is exactly 15 digits
    if len(sender) >= 15: return f"{sender}@lid"
    return f"{sender}@s.whatsapp.net"

# --- 🚀 MAIN ORCHESTRATOR ---
async def main():
    print("\n🧠 SPECTRA BRAIN: ONLINE (V27 - Final Fix)")
    print("==========================================")

    wa_process = None
    whatsapp_send_queue = deque()

    try:
        # 1. Start WhatsApp (Subprocess Mode)
        print("1. [Runtime] Launching WhatsApp Bridge...")
        wa_process = await asyncio.create_subprocess_shell(
            "go run main.go",
            cwd=WA_BRIDGE_PATH,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        print("   ✅ WhatsApp Bridge started (Listening on stdout).")

        # 2. Connect to MCP Servers (NASA + GIS)
        print("2. [Connecting] MCP Pipelines...")
        
        async with stdio_client(nasa_params) as (nasa_r, nasa_w):
            async with ClientSession(nasa_r, nasa_w) as nasa_sess:
                print("   ✅ NASA Connected!")
                await nasa_sess.initialize()

                async with stdio_client(gis_params) as (gis_r, gis_w):
                    async with ClientSession(gis_r, gis_w) as gis_sess:
                        print("   ✅ GIS Connected!")
                        await gis_sess.initialize()
                        
                        print("   ✅ ALL SYSTEMS LIVE. Waiting for messages...")
                        
                        async with httpx.AsyncClient(timeout=10) as http_client:
                            
                            while True:
                                # --- A. READ WHATSAPP LOGS ---
                                try:
                                    line_bytes = await asyncio.wait_for(wa_process.stdout.readline(), timeout=0.1)
                                    if line_bytes:
                                        line = line_bytes.decode('utf-8', errors='replace').strip()
                                        if "<-" in line or "←" in line: # Only print incoming msgs logs
                                            print(f"   [Log] {line}")
                                            
                                            msg = parse_stream_line(line)
                                            if msg:
                                                sender = msg['sender']
                                                text = msg['text']
                                                jid = resolve_jid(sender)
                                                
                                                print(f"\n📩 INCOMING from {sender}: {text}")

                                                # --- BRAIN LOGIC ---
                                                reply = ""
                                                if "nasa" in text.lower():
                                                    print("   🛰️ Querying NASA...")
                                                    try:
                                                        res = await nasa_sess.call_tool("nasa_apod", arguments={})
                                                        # Handle JSON vs Text return from NASA tool
                                                        content = res.content[0].text
                                                        if content.strip().startswith("{"):
                                                            data = json.loads(content)
                                                            reply = f"🛰️ NASA: {data.get('title', 'Space Data')}"
                                                        else:
                                                            reply = f"🛰️ NASA: {content[:100]}..."
                                                    except Exception as e:
                                                        reply = "NASA Error."
                                                
                                                elif "map" in text.lower():
                                                    print("   🗺️ Querying GIS...")
                                                    try:
                                                        res = await gis_sess.call_tool("get_coordinates", arguments={"location": "Farm"})
                                                        reply = f"🗺️ GIS: {res.content[0].text}"
                                                    except:
                                                        reply = "GIS Error."
                                                
                                                else:
                                                    reply = f"Spectra: {text}"

                                                # Queue Reply
                                                whatsapp_send_queue.append({"jid": jid, "message": reply})

                                except asyncio.TimeoutError:
                                    pass

                                # --- B. SEND MESSAGES (VIA HTTP REST) ---
                                while whatsapp_send_queue:
                                    job = whatsapp_send_queue.popleft()
                                    jid = job['jid']
                                    content = job['message']
                                    
                                    print(f"   📤 Sending to {jid}...")
                                    
                                    try:
                                        # ✅ FIX 1: The bridge demands 'recipient', not 'phone'
                                        payload = {
                                            "recipient": jid, 
                                            "message": content
                                        }
                                        
                                        # Debug: See exactly what we send
                                        # print(f"      [Debug Payload] {payload}")
                                        
                                        resp = await http_client.post(WA_API_URL, json=payload)
                                        
                                        if resp.status_code == 200:
                                            print("      ✅ Sent Successfully!")
                                        else:
                                            print(f"      ⚠️ API Error {resp.status_code}: {resp.text}")
                                            
                                    except Exception as e:
                                        print(f"      ❌ Connection Failed: {e}")
                                        print("      (Check if bridge is running on port 8080)")

                                await asyncio.sleep(0.1)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    finally:
        if wa_process: wa_process.terminate()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())