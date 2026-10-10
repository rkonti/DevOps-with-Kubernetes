import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", "3000"))
COUNT_FILE = os.getenv("COUNT_FILE", "/usr/src/app/files/pingpong.txt")

def load_counter():
    try:
        with open(COUNT_FILE) as f:
            return int(f.read().strip() or 0)
    except FileNotFoundError:
        return 0

def save_counter(value):
    with open(COUNT_FILE, "w") as f:
        f.write(str(value))

os.makedirs(os.path.dirname(COUNT_FILE), exist_ok=True)

counter = load_counter()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global counter
        if self.path != "/pingpong":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(f"pong {counter}".encode())
        counter += 1
        save_counter(counter)

print(f"Server started in port {PORT}", flush=True)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
