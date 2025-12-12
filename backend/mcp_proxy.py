import sys
import subprocess
import threading
import json
import os

def forward_stdin(process):
    """Reads from system stdin and writes to subprocess stdin."""
    try:
        while True:
            data = sys.stdin.read(1)
            if not data:
                break
            process.stdin.write(data)
            process.stdin.flush()
    except Exception:
        pass

def forward_stderr(process):
    """Reads from subprocess stderr and writes to system stderr."""
    try:
        while True:
            line = process.stderr.readline()
            if not line:
                break
            sys.stderr.write(line)
            sys.stderr.flush()
    except Exception:
        pass

def filter_stdout(process):
    """Reads from subprocess stdout, filters for JSON, and writes to system stdout."""
    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            
            clean_line = line.strip()
            # Heuristic: Only pass lines that look like JSON objects
            if clean_line.startswith('{') and clean_line.endswith('}'):
                try:
                    # Verify it's valid JSON
                    json.loads(clean_line)
                    sys.stdout.write(line)
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    # Log invalid JSON to stderr so we can see it but it doesn't break MCP
                    sys.stderr.write(f"[MCP-FILTERED-INVALID] {clean_line}\n")
            else:
                # Log non-JSON text (like logs) to stderr
                sys.stderr.write(f"[MCP-FILTERED-LOG] {clean_line}\n")
    except Exception:
        pass

def main():
    # The command to run is passed as arguments to this script
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python mcp_proxy.py <command> [args...]\n")
        sys.exit(1)

    cmd = sys.argv[1:]
    
    # Start the actual MCP server process
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )

    # Start threads to handle streams
    t_in = threading.Thread(target=forward_stdin, args=(process,), daemon=True)
    t_err = threading.Thread(target=forward_stderr, args=(process,), daemon=True)
    t_out = threading.Thread(target=filter_stdout, args=(process,), daemon=True)

    t_in.start()
    t_err.start()
    t_out.start()

    # Wait for process to finish
    process.wait()
    sys.exit(process.returncode)

if __name__ == "__main__":
    main()