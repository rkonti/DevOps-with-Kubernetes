import asyncio
import json
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import nats
import psycopg
from psycopg.rows import dict_row

PORT = int(os.environ["PORT"])
MAX_LENGTH = int(os.environ["TODO_MAX_LENGTH"])
NATS_URL = os.getenv("NATS_URL", "")
NATS_SUBJECT = os.getenv("NATS_SUBJECT", "todos")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("todo-backend")

# psycopg reads the connection settings from the standard libpq
# environment variables (PGHOST, PGUSER, PGPASSWORD, PGDATABASE)
def connect():
    return psycopg.connect(autocommit=True, row_factory=dict_row, connect_timeout=2)

db_initialized = False

def init_db():
    """Create the todos table once the database is reachable."""
    global db_initialized
    if db_initialized:
        return
    with connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS todos (id SERIAL PRIMARY KEY, content TEXT NOT NULL)"
        )
        # Added in exercise 4.5; existing todos start as not done
        conn.execute(
            "ALTER TABLE todos ADD COLUMN IF NOT EXISTS done BOOLEAN NOT NULL DEFAULT FALSE"
        )
    db_initialized = True

def check_db():
    init_db()
    with connect() as conn:
        conn.execute("SELECT 1")

def fetch_todos():
    with connect() as conn:
        return conn.execute("SELECT id, content, done FROM todos ORDER BY id").fetchall()

def create_todo(content):
    with connect() as conn:
        return conn.execute(
            "INSERT INTO todos (content) VALUES (%s) RETURNING id, content, done", (content,)
        ).fetchone()

# The HTTP server is synchronous but nats-py is asyncio based, so the NATS
# connection lives on its own event loop in a background thread
nats_loop = asyncio.new_event_loop()
threading.Thread(target=nats_loop.run_forever, daemon=True).start()
nats_client = None

async def nats_publish(payload):
    global nats_client
    if nats_client is None or nats_client.is_closed:
        nats_client = await nats.connect(NATS_URL, connect_timeout=2, max_reconnect_attempts=-1)
    await nats_client.publish(NATS_SUBJECT, payload)
    await nats_client.flush(timeout=2)

def publish_event(action, todo):
    """Tell the broadcaster about a change. The todo is already saved, so a
    NATS outage only means the chat message is skipped."""
    if not NATS_URL:
        return
    payload = json.dumps({"action": action, "todo": todo}).encode()
    future = asyncio.run_coroutine_threadsafe(nats_publish(payload), nats_loop)
    try:
        future.result(timeout=5)
    except Exception as e:
        log.warning("Could not publish %s event for todo %d to NATS: %s", action, todo["id"], e)

def update_todo(todo_id, done):
    """Return the updated todo, or None if there is no todo with that id."""
    with connect() as conn:
        return conn.execute(
            "UPDATE todos SET done = %s WHERE id = %s RETURNING id, content, done",
            (done, todo_id),
        ).fetchone()

class Handler(BaseHTTPRequestHandler):
    # Route the built-in access log through our logger, skipping the probes
    def log_message(self, format, *args):
        if self.path == "/healthz":
            return
        log.info("%s %s", self.address_string(), format % args)

    def send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        # Lets the client finish reading before the connection closes, so
        # publishing to NATS after the response doesn't delay it
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Readiness probe: ready only when the database is reachable
        if self.path == "/healthz":
            try:
                check_db()
                self.send_json(200, {"status": "ok"})
            except psycopg.Error as e:
                log.warning("Health check failed: %s", e)
                self.send_json(500, {"status": "database unavailable"})
            return
        if self.path != "/todos":
            self.send_json(404, {"error": "not found"})
            return
        try:
            init_db()
            self.send_json(200, fetch_todos())
        except psycopg.Error as e:
            log.error("Database error: %s", e)
            self.send_json(503, {"error": "database unavailable"})

    def do_POST(self):
        if self.path != "/todos":
            self.send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            content = json.loads(self.rfile.read(length))["content"].strip()
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            log.warning("Rejected todo: invalid request body")
            self.send_json(400, {"error": "expected JSON body with a 'content' string"})
            return
        if not content or len(content) > MAX_LENGTH:
            log.warning("Rejected todo (%d characters, limit %d): %r", len(content), MAX_LENGTH, content)
            self.send_json(400, {"error": f"content must be 1-{MAX_LENGTH} characters"})
            return
        try:
            init_db()
            todo = create_todo(content)
            log.info("Created todo %d: %r", todo["id"], content)
            self.send_json(201, todo)
            publish_event("created", todo)
        except psycopg.Error as e:
            log.error("Database error: %s", e)
            self.send_json(503, {"error": "database unavailable"})

    def do_PUT(self):
        parts = self.path.strip("/").split("/")
        if len(parts) != 2 or parts[0] != "todos" or not parts[1].isdigit():
            self.send_json(404, {"error": "not found"})
            return
        todo_id = int(parts[1])
        length = int(self.headers.get("Content-Length", 0))
        try:
            done = json.loads(self.rfile.read(length))["done"]
        except (json.JSONDecodeError, KeyError, TypeError):
            done = None
        if not isinstance(done, bool):
            log.warning("Rejected update of todo %d: invalid request body", todo_id)
            self.send_json(400, {"error": "expected JSON body with a boolean 'done'"})
            return
        try:
            init_db()
            todo = update_todo(todo_id, done)
        except psycopg.Error as e:
            log.error("Database error: %s", e)
            self.send_json(503, {"error": "database unavailable"})
            return
        if todo is None:
            self.send_json(404, {"error": f"todo {todo_id} not found"})
            return
        log.info("Marked todo %d as %s", todo_id, "done" if done else "not done")
        self.send_json(200, todo)
        publish_event("updated", todo)

log.info("Server started in port %d", PORT)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
