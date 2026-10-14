import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import psycopg
from psycopg.rows import dict_row

PORT = int(os.environ["PORT"])
MAX_LENGTH = int(os.environ["TODO_MAX_LENGTH"])

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
            print(f"Database not ready, retrying: {e}", flush=True)
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
            print(f"Database error: {e}", flush=True)
            self.send_json(503, {"error": "database unavailable"})

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
        try:
            self.send_json(201, create_todo(content))
        except psycopg.Error as e:
            print(f"Database error: {e}", flush=True)
            self.send_json(503, {"error": "database unavailable"})

init_db()

print(f"Server started in port {PORT}", flush=True)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
