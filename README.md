# ctrl-shift-defeat
# Spectra — WhatsApp + FastAPI + Gemini Crop Advisory (Hackathon Build)

Spectra is a hackathon-grade backend that connects:
- **FastAPI** (main API + webhook)
- **WhatsApp Bridge** (Go / whatsmeow on `:8080`) for sending/receiving messages
- **Gemini 2.5 Flash** for responses
- **MCP servers** (NASA + GIS) for satellite/weather + NDVI calculation
- **gTTS** for MP3 voice notes (no ffmpeg / pydub)

This repo is designed to be demo-ready quickly: QR login, WhatsApp webhook, morning brief scheduler, and static MP3 hosting.

---

## Architecture

```
Farmer WhatsApp
   ↕ (whatsmeow)
WhatsApp Bridge (Go)  :8080
   ↕ (HTTP POST)
FastAPI Backend       :8000
   ↕
Gemini 2.5 Flash + MCP (NASA/GIS)
   ↕
gTTS → MP3 saved to backend/static/audio
```

---

## Features

- WhatsApp QR login in terminal (scannable QR)
- Inbound WhatsApp webhook → AI reply
- Tool-calling via MCP:
  - NASA MCP: satellite/weather context
  - GIS MCP: NDVI computation
- Voice notes:
  - **MP3 only** using `gTTS`
  - Served via `/static` (for downloading if needed)
  - **No extra localhost link message after sending audio**
- Scheduler:
  - Runs “morning brief” **once immediately on startup** (demo)
  - Then sleeps (default 24h)

---

## Services & Ports

| Service | Path | Port |
|--------|------|------|
| FastAPI backend | `d:\Spectra\backend` | `8000` |
| WhatsApp bridge | `d:\Spectra\whatsapp-mcp\whatsapp-bridge` | `8080` |

---

## Prerequisites

### Backend (Python)
- Python 3.10+ recommended
- MongoDB URI (local or Atlas)

Install dependencies:
```powershell
cd d:\Spectra\backend
pip install -r requirements.txt
```

### WhatsApp Bridge (Go)
- Go 1.21+ recommended

```powershell
cd d:\Spectra\whatsapp-mcp\whatsapp-bridge
go mod tidy
go run .
```

---

## Environment Variables

Create `d:\Spectra\.env` (repo root). Example:

```env
# Gemini
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
GEMINI_MODEL=gemini-2.5-flash

# MongoDB
MONGO_URI=mongodb://localhost:27017

# Optional: SMTP (OTP email)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASS=app_password

# Optional: bridge -> backend webhook override
BACKEND_WEBHOOK_URL=http://localhost:8000/whatsapp-webhook
```

> Note: If Gemini returns `403 ... API key was reported as leaked`, you must generate a new key.

---

## Run (Demo Mode)

### 1) Start WhatsApp Bridge (Go)
```powershell
cd d:\Spectra\whatsapp-mcp\whatsapp-bridge
go run .
```

Scan the QR in WhatsApp:
**WhatsApp → Linked Devices → Link a Device**

Bridge REST endpoints:
- `POST http://localhost:8080/api/send`
- `POST http://localhost:8080/api/send_audio`

### 2) Start FastAPI Backend
```powershell
cd d:\Spectra\backend
uvicorn main:app --reload --port 8000
```

Backend routes:
- `GET  /` → health
- `POST /whatsapp-webhook` → WhatsApp inbound messages
- `POST /send-otp` / `POST /verify-otp`
- `POST /save` (supports both farmer registration + insurance save)
- `POST /admin/run-morning-brief`
- `GET  /api/farmers`
- `GET  /api/claims`

Static MP3:
- `GET /static/...`

---

## WhatsApp Message Flow

1. User sends a WhatsApp message to the connected WhatsApp account.
2. The bridge forwards it to FastAPI `/whatsapp-webhook`.
3. The backend:
   - loads user profile (Mongo)
   - calls Gemini 2.5 Flash
   - optionally calls tools (MCP NASA/GIS)
4. The backend replies via bridge `/api/send`.
5. If voice is enabled, backend generates MP3 via `gTTS` and sends audio via `/api/send_audio`.

---

## “Health” Keyword Behavior (Crop Health / NDVI)

If the user message contains “health”, “crop health”, or “ndvi”, the agent is expected to:
1. fetch satellite/weather context using NASA MCP
2. compute NDVI using GIS MCP
3. send a simplified “crop greenness/health” explanation (no heavy jargon)

---

## CORS Notes (Frontend)

CORS is configured to allow any `localhost` / `127.0.0.1` port.
If your frontend runs on a different host/IP, add it to CORS settings in `backend/main.py`.

---

## Troubleshooting

### 1) `OPTIONS /save 400 Bad Request`
This is a **CORS preflight failure**. Confirm your browser’s `Origin` header is `localhost` or `127.0.0.1`. If not, update CORS in `backend/main.py`.

### 2) Bridge 500: `can't send message to unknown server 91xxxx`
The bridge must convert phone numbers to `number@s.whatsapp.net`. Ensure your bridge build includes the JID normalization fix.

### 3) Bridge 500: `no signal session established`
WhatsApp may block proactive sends to numbers that never messaged you. For demo reliability:
- have the judge send “hi” first
- then reply / send brief

### 4) Gemini JSON parse errors (`Invalid control character...`)
The agent uses a hardened JSON extraction + fallback-to-text to avoid crashes. If it still happens, log the raw model output and tighten the prompt.

---

## Repo Layout (Typical)

- `backend/`
  - `main.py` — FastAPI app + routes + CORS + static
  - `agent.py` — WhatsApp message handling + Gemini logic
  - `brain.py` — tools definitions + system prompt
  - `scheduler.py` — morning brief job + loop
  - `voice_service.py` — gTTS MP3 generation + send audio
  - `database.py` — MongoDB users/claims
  - `static/audio/` — generated MP3 files
- `whatsapp-mcp/whatsapp-bridge/`
  - `main.go` — whatsmeow client + REST API + QR login

---

## One-Command Demo Script (Manual)

1. Start bridge (`:8080`)
2. Start backend (`:8000`)
3. Send WhatsApp message from phone: “health of my crops”
4. Show: MCP tools → AI response → voice note reply

---

## License
Hackathon/demo use. Add a license if you plan to open-source.
