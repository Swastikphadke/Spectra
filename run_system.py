import subprocess
import time
import os
import sys

# Paths
BACKEND_DIR = os.path.join(os.getcwd(), "backend")
BRIDGE_DIR = os.path.join(os.getcwd(), "whatsapp-mcp", "whatsapp-bridge")

def run_system():
    print("🚀 Starting Spectra System...")

    # 1. Start FastAPI Backend
    print("Starting Backend (FastAPI)...")
    backend_process = subprocess.Popen(
        ["uvicorn", "main:app", "--reload", "--port", "8000"],
        cwd=BACKEND_DIR,
        shell=True
    )

    # 2. Start WhatsApp Bridge
    print("Starting WhatsApp Bridge (Go)...")
    # We use 'go run .' or 'go run main.go'
    bridge_process = subprocess.Popen(
        ["go", "run", "main.go"],
        cwd=BRIDGE_DIR,
        shell=True
    )

    print("\n✅ System is running!")
    print("   - Backend: http://localhost:8000")
    print("   - Bridge:  http://localhost:8080")
    print("   - Webhook: http://localhost:8000/whatsapp-webhook")
    print("\nPress Ctrl+C to stop all services.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        backend_process.terminate()
        bridge_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    run_system()
