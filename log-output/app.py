import os
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", "3000"))

random_string = str(uuid.uuid4())

def status():
    timestamp = datetime.now(timezone.utc).isoformat()
    return f"{timestamp}: {random_string}"

def log_forever():
    while True:
        print(status(), flush=True)
        time.sleep(5)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(status().encode())

threading.Thread(target=log_forever, daemon=True).start()

print(f"Server started in port {PORT}", flush=True)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
