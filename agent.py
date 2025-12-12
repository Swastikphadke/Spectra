import asyncio
import sys
import json
import re
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --- 🛠️ CONFIGURATION ---

# 1. WhatsApp
wa_params = StdioServerParameters(
    command="uv",
    args=["--directory", r"D:\WHACK\whatsapp-mcp\whatsapp-mcp-server", "run", "main.py"],
    env={"PYTHONUNBUFFERED": "1"}
)

# 2. NASA
nasa_params = StdioServerParameters(
    command="cmd",
    args=["/c", "node", r"D:\Spectra\NASA-MCP-server\dist\index.js"],
    env={"NASA_API_KEY": "kWiy0mz0ocWHh1zUIrqfTX6tzfYQRmOfob1ysWw2"}
)

# 3. GIS (Real Engine)
gis_params = StdioServerParameters(
    command="uv", 
    args=["--directory", r"D:\Spectra\GIS-Real", "run", "gis-mcp"], 
    env={"PYTHONUNBUFFERED": "1"}
)

# --- 🧠 HELPER: SMART ADDRESS RESOLVER (FIXED) ---
def resolve_jid(sender_raw):
    """
    Determines if the sender is a Standard Phone, a Hidden User (LID), or a Group.
    """
    sender = sender_raw.strip().replace("+", "").replace(" ", "")
    
    # 1. Trust if domain exists
    if "@" in sender: return sender
    
    # 2. Group Check (contains hyphen)
    if "-" in sender: return f"{sender}@g.us"
    
    # 3. LID Check (Long IDs usually starting with 1 or 2)
    #    Your log showed '206420960088238' (15 digits). Standard mobile is ~10-13.
    if len(sender) >= 15: 
        return f"{sender}@lid"   # <--- THIS IS THE FIX 🟢

    # 4. Standard Phone
    return f"{sender}@s.whatsapp.net"

# --- 🧠 HELPER: PARSER ---
def parse_stream_line(line):
    clean = line.strip()
    if not clean: return None
    match = re.search(r"\[(.*?)\] (?:<-|←) (.*?): (.*)", clean)
    if match:
        ts, sender, text = match.groups()
        return {"sender": sender.strip(), "text": text.strip()}
    return None

# --- 🚀 MAIN ORCHESTRATOR ---
async def main():
    print("\n🧠 SPECTRA BRAIN: ONLINE (V22 - LID FIX)")
    print("==========================================")

    try:
        async with stdio_client(wa_params) as (wa_r, wa_w), \
                   stdio_client(nasa_params) as (nasa_r, nasa_w), \
                   stdio_client(gis_params) as (gis_r, gis_w):
            
            async with ClientSession(wa_r, wa_w) as wa_sess, \
                       ClientSession(nasa_r, nasa_w) as nasa_sess, \
                       ClientSession(gis_r, gis_w) as gis_sess:

                print("1. [Connecting] MCP Pipelines...", end=" ")
                await asyncio.gather(wa_sess.initialize(), nasa_sess.initialize(), gis_sess.initialize())
                print("✅ ALL SYSTEMS LIVE.")
                
                print("2. [Runtime] Launching WhatsApp Bridge...")
                process = await asyncio.create_subprocess_shell(
                    "go run main.go",
                    cwd=r"D:\WHACK\whatsapp-mcp\whatsapp-bridge",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                print("   ✅ SPECTRA LISTENING.")

                while True:
                    line_bytes = await process.stdout.readline()
                    if not line_bytes: break
                    line = line_bytes.decode('utf-8', errors='replace').strip()
                    
                    if line and "[Go]" not in line: print(f"   [Log] {line}") 

                    msg = parse_stream_line(line)
                    if msg:
                        sender_raw = msg['sender']
                        text = msg['text']
                        
                        # --- 🔧 FIX APPLIED HERE ---
                        jid = resolve_jid(sender_raw)
                        
                        print(f"\n📩 INCOMING: {text} (ID: {sender_raw})")
                        print(f"   🎯 Routing to: {jid}") # <--- Verify this says @lid
                        
                        query = text.lower()
                        reply = ""

                        # --- LOGIC ---
                        if "nasa" in query:
                            print("   🛰️ NASA Request...")
                            try:
                                res = await nasa_sess.call_tool("nasa_apod", arguments={})
                                raw_data = res.content[0].text
                                
                                # Check if it's JSON or Markdown Text
                                if raw_data.strip().startswith("{"):
                                    data = json.loads(raw_data)
                                    reply = f"🤖 NASA: {data.get('title')}"
                                else:
                                    # Handle the "Northern Fox Fires" text block
                                    first_line = raw_data.split('\n')[0].replace("#", "").strip()
                                    reply = f"🤖 NASA Info: {first_line}\n(Full details in console)"
                            except Exception as e: 
                                reply = f"🤖 NASA Failed: {e}"

                        elif "map" in query:
                            print("   🗺️ GIS Request...")
                            try:
                                await gis_sess.call_tool("get_coordinates", arguments={"geometry": "POINT(0 0)"})
                                reply = "🤖 GIS: Connection Successful (Engine Active)"
                            except:
                                reply = "🤖 GIS Online! (Ready for data)"
                        
                        else:
                            reply = f"🤖 Echo: {text}"

                        # --- SEND ---
                        print(f"   📤 Sending...")
                        try:
                            await wa_sess.call_tool("send_message", arguments={"recipient": jid, "message": reply})
                        except Exception as e:
                            print(f"   ❌ FAIL: {e}")

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())