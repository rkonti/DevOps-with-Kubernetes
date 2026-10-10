import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", "3000"))
LOG_FILE = os.getenv("LOG_FILE", "/usr/src/app/files/log.txt")
COUNT_FILE = os.getenv("COUNT_FILE", "/usr/src/app/files/pingpong.txt")

def latest_line():
    try:
        with open(LOG_FILE) as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        return "No logs yet"
    return lines[-1] if lines else "No logs yet"

def pingpong_count():
    try:
        with open(COUNT_FILE) as f:
            return int(f.read().strip() or 0)
    except FileNotFoundError:
        return 0

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        body = f"{latest_line()}.\nPing / Pongs: {pingpong_count()}"
        self.wfile.write(body.encode())

print(f"Server started in port {PORT}", flush=True)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
