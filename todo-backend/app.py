import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", "3000"))
MAX_LENGTH = 140

todos = []

class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/todos":
            self.send_json(200, todos)
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/todos":
            self.send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            content = json.loads(self.rfile.read(length))["content"].strip()
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            self.send_json(400, {"error": "expected JSON body with a 'content' string"})
            return
        if not content or len(content) > MAX_LENGTH:
            self.send_json(400, {"error": f"content must be 1-{MAX_LENGTH} characters"})
            return
        todo = {"id": len(todos) + 1, "content": content}
        todos.append(todo)
        self.send_json(201, todo)

print(f"Server started in port {PORT}", flush=True)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
