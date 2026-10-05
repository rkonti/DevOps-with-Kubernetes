import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", "3000"))
LOG_FILE = os.getenv("LOG_FILE", "/usr/src/app/files/log.txt")

def latest_line():
    try:
        with open(LOG_FILE) as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        return "No logs yet"
    return lines[-1] if lines else "No logs yet"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(latest_line().encode())

print(f"Server started in port {PORT}", flush=True)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
