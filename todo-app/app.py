import html
import json
import os
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", "3000"))
CACHE_DIR = os.getenv("CACHE_DIR", "/usr/src/app/files")
IMAGE_URL = os.getenv("IMAGE_URL", "https://picsum.photos/1200")
IMAGE_TTL = int(os.getenv("IMAGE_TTL_SECONDS", "600"))

IMAGE_FILE = os.path.join(CACHE_DIR, "image.jpg")
META_FILE = os.path.join(CACHE_DIR, "image.json")

HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Todo App</title>
</head>
<body>
  <h1>Todo App</h1>
  <img src="/image?v={version}" alt="Random image" style="max-width: 600px; width: 100%;">
  <form onsubmit="event.preventDefault()">
    <input type="text" name="todo" maxlength="140" required placeholder="Todo (max 140 characters)">
    <button type="submit">Send</button>
  </form>
  <ul>
{todos}
  </ul>
  <p>DevOps with Kubernetes 2026</p>
</body>
</html>
"""

TODOS = [
    "Learn JavaScript",
    "Learn React",
    "Build a project",
]

def load_meta():
    try:
        with open(META_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def save_meta(meta):
    tmp = META_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(meta, f)
    os.replace(tmp, META_FILE)

def fetch_image():
    print(f"Fetching new image from {IMAGE_URL}", flush=True)
    with urllib.request.urlopen(IMAGE_URL, timeout=10) as response:
        data = response.read()
    tmp = IMAGE_FILE + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, IMAGE_FILE)
    meta = {"fetched_at": time.time(), "stale_served": False}
    save_meta(meta)
    return meta

def current_image():
    """Return the cached image's metadata, refreshing it when it has expired.

    Once the image is older than IMAGE_TTL, it is served one more time and
    the request after that gets a new image.
    """
    meta = load_meta()
    if meta is None or not os.path.exists(IMAGE_FILE):
        return fetch_image()
    if time.time() - meta["fetched_at"] < IMAGE_TTL:
        return meta
    if not meta["stale_served"]:
        meta["stale_served"] = True
        save_meta(meta)
        return meta
    try:
        return fetch_image()
    except OSError as e:
        print(f"Failed to fetch new image, keeping the old one: {e}", flush=True)
        return meta

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            meta = current_image()
            todos = "\n".join(f"    <li>{html.escape(todo)}</li>" for todo in TODOS)
            body = HTML.format(version=int(meta["fetched_at"]), todos=todos).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        elif path == "/image":
            try:
                with open(IMAGE_FILE, "rb") as f:
                    data = f.read()
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.end_headers()
            self.wfile.write(data)
        elif path == "/shutdown":
            # For testing that the cached image survives a container crash
            print("Shutting down", flush=True)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Shutting down")
            self.wfile.flush()
            os._exit(1)
        else:
            self.send_response(404)
            self.end_headers()

os.makedirs(CACHE_DIR, exist_ok=True)

print(f"Server started in port {PORT}", flush=True)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
