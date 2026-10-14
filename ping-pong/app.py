import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", "3000"))

counter = 0

class Handler(BaseHTTPRequestHandler):
    def send_text(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        global counter
        if self.path == "/pingpong":
            self.send_text(f"pong {counter}")
            counter += 1
        elif self.path == "/pings":
            self.send_text(str(counter))
        else:
            self.send_response(404)
            self.end_headers()

print(f"Server started in port {PORT}", flush=True)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
