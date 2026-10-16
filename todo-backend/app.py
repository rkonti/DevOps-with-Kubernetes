import json
import logging
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import psycopg
from psycopg.rows import dict_row

PORT = int(os.environ["PORT"])
MAX_LENGTH = int(os.environ["TODO_MAX_LENGTH"])

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("todo-backend")

# psycopg reads the connection settings from the standard libpq
# environment variables (PGHOST, PGUSER, PGPASSWORD, PGDATABASE)
def connect():
    return psycopg.connect(autocommit=True, row_factory=dict_row)

def init_db():
    while True:
        try:
            with connect() as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS todos (id SERIAL PRIMARY KEY, content TEXT NOT NULL)"
                )
            return
        except psycopg.OperationalError as e:
            log.warning("Database not ready, retrying: %s", e)
            time.sleep(2)

def fetch_todos():
    with connect() as conn:
        return conn.execute("SELECT id, content FROM todos ORDER BY id").fetchall()

def create_todo(content):
    with connect() as conn:
        return conn.execute(
            "INSERT INTO todos (content) VALUES (%s) RETURNING id, content", (content,)
        ).fetchone()

class Handler(BaseHTTPRequestHandler):
    # Route the built-in access log through our logger
    def log_message(self, format, *args):
        log.info("%s %s", self.address_string(), format % args)

    def send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/todos":
            self.send_json(404, {"error": "not found"})
            return
        try:
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
            todo = create_todo(content)
            log.info("Created todo %d: %r", todo["id"], content)
            self.send_json(201, todo)
        except psycopg.Error as e:
            log.error("Database error: %s", e)
            self.send_json(503, {"error": "database unavailable"})

init_db()

log.info("Server started in port %d", PORT)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
