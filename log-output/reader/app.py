import os
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", "3000"))
LOG_FILE = os.getenv("LOG_FILE", "/usr/src/app/files/log.txt")
PINGS_URL = os.getenv("PINGS_URL", "http://ping-pong-svc/pings")
INFO_FILE = os.getenv("INFO_FILE", "/usr/src/app/config/information.txt")
MESSAGE = os.getenv("MESSAGE", "")

def latest_line():
    try:
        with open(LOG_FILE) as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        return "No logs yet"
    return lines[-1] if lines else "No logs yet"

def information():
    try:
        with open(INFO_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def pingpong_count():
    try:
        with urllib.request.urlopen(PINGS_URL, timeout=2) as res:
            return int(res.read().decode().strip())
    except (OSError, ValueError):
        return "unavailable"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Readiness probe: ready only when ping-pong answers with a count
        if self.path == "/healthz":
            ready = isinstance(pingpong_count(), int)
            self.send_response(200 if ready else 500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok" if ready else b"ping-pong unavailable")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        body = (
            f"file content: {information()}\n"
            f"env variable: MESSAGE={MESSAGE}\n"
            f"{latest_line()}.\n"
            f"Ping / Pongs: {pingpong_count()}"
        )
        self.wfile.write(body.encode())

print(f"Server started in port {PORT}", flush=True)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
