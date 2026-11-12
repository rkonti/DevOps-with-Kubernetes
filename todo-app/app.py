import html
import json
import os
import signal
import sys
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ["PORT"])
CACHE_DIR = os.environ["CACHE_DIR"]
IMAGE_URL = os.environ["IMAGE_URL"]
IMAGE_TTL = int(os.environ["IMAGE_TTL_SECONDS"])
TODOS_URL = os.environ["TODOS_URL"]
TODO_MAX_LENGTH = int(os.environ["TODO_MAX_LENGTH"])

BACKEND_HEALTH_URL = urllib.parse.urljoin(TODOS_URL, "/healthz")

IMAGE_FILE = os.path.join(CACHE_DIR, "image.jpg")
META_FILE = os.path.join(CACHE_DIR, "image.json")

# Set to False by the "Break the app" button. The liveness probe then fails
# and Kubernetes restarts the container, which starts healthy again.
is_healthy = True

HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Todo App</title>
</head>
<body>
  <h1>Todo App</h1>
  <img src="/image?v={version}" alt="Random image" style="max-width: 600px; width: 100%;">
  <form method="post" action="/todos">
    <input type="text" name="todo" maxlength="{max_length}" required placeholder="Todo (max {max_length} characters)">
    <button type="submit">Send</button>
  </form>
  <h2>Todo</h2>
  <ul>
{todos}
  </ul>
  <h2>Done</h2>
  <ul>
{done}
  </ul>
  <form method="post" action="/break">
    <button type="submit">Break the app</button>
  </form>
  <p>DevOps with Kubernetes 2026</p>
</body>
</html>
"""

BROKEN_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Todo App</title>
</head>
<body>
  <h1>Todo App is broken</h1>
  <p>Kubernetes will restart it shortly.</p>
</body>
</html>
"""

def fetch_todos():
    with urllib.request.urlopen(TODOS_URL, timeout=5) as response:
        return json.load(response)

def create_todo(content):
    request = urllib.request.Request(
        TODOS_URL,
        data=json.dumps({"content": content}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5):
        pass

def mark_done(todo_id):
    request = urllib.request.Request(
        f"{TODOS_URL}/{todo_id}",
        data=json.dumps({"done": True}).encode(),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(request, timeout=5):
        pass

def render_todo(todo):
    content = html.escape(todo["content"])
    if todo["done"]:
        return f"    <li>{content}</li>"
    # Browsers can only send GET and POST from a form, so the button posts
    # here and the app sends the PUT to the backend
    return (
        f'    <li>{content} '
        f'<form method="post" action="/todos/{todo["id"]}/done" style="display: inline;">'
        f'<button type="submit">Mark as done</button></form></li>'
    )

def backend_ready():
    try:
        with urllib.request.urlopen(BACKEND_HEALTH_URL, timeout=2):
            return True
    except OSError:
        return False

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
    the request after that gets a new image. Returns None when there is no
    cached image and a new one can't be fetched.
    """
    meta = load_meta()
    if meta is None or not os.path.exists(IMAGE_FILE):
        try:
            return fetch_image()
        except OSError as e:
            print(f"Failed to fetch an image, showing the page without one: {e}", flush=True)
            return None
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
    def send_status(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        path = self.path.split("?")[0]
        # Liveness probe: fails only when the app has been broken
        if path == "/healthz":
            self.send_status(200 if is_healthy else 500, "ok" if is_healthy else "broken")
        # Readiness probe: also requires the backend (and so the database) to be ready
        elif path == "/readyz":
            ready = is_healthy and backend_ready()
            self.send_status(200 if ready else 500, "ready" if ready else "not ready")
        elif not is_healthy:
            self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(BROKEN_HTML.encode())
        elif path == "/":
            meta = current_image()
            try:
                all_todos = fetch_todos()
                todos = "\n".join(render_todo(t) for t in all_todos if not t["done"])
                done = "\n".join(render_todo(t) for t in all_todos if t["done"])
            except OSError as e:
                print(f"Failed to fetch todos: {e}", flush=True)
                todos = "    <li>Could not load todos</li>"
                done = ""
            body = HTML.format(
                version=int(meta["fetched_at"]) if meta else 0,
                todos=todos,
                done=done,
                max_length=TODO_MAX_LENGTH,
            ).encode()
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

    def do_POST(self):
        global is_healthy
        if self.path == "/break":
            print("App broken via the button, liveness probe will now fail", flush=True)
            is_healthy = False
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return
        parts = self.path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "todos" and parts[1].isdigit() and parts[2] == "done":
            try:
                mark_done(int(parts[1]))
            except OSError as e:
                print(f"Failed to mark todo {parts[1]} as done: {e}", flush=True)
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return
        if self.path != "/todos":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        form = urllib.parse.parse_qs(self.rfile.read(length).decode())
        content = form.get("todo", [""])[0]
        try:
            create_todo(content)
        except OSError as e:
            print(f"Failed to create todo: {e}", flush=True)
        # Redirect back so a page refresh doesn't resubmit the form
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

os.makedirs(CACHE_DIR, exist_ok=True)

# As PID 1 the process ignores SIGTERM by default, so Kubernetes would wait out
# the whole grace period before killing it on a restart
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

print(f"Server started in port {PORT}", flush=True)

# Threaded, so a slow request (like fetching the image) can't block the
# Kubernetes probes and make the pod look unhealthy
server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
