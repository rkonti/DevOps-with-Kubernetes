import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", "3000"))

HTML = b"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Todo App</title>
</head>
<body>
  <h1>Todo App</h1>
  <p>Hello from the todo app running in Kubernetes!</p>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML)

print(f"Server started in port {PORT}", flush=True)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
