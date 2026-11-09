import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import psycopg

PORT = int(os.environ["PORT"])

# psycopg reads the connection settings from the standard libpq
# environment variables (PGHOST, PGUSER, PGPASSWORD, PGDATABASE)
def connect():
    return psycopg.connect(autocommit=True, connect_timeout=2)

db_initialized = False

def init_db():
    """Create the counter table once the database is reachable."""
    global db_initialized
    if db_initialized:
        return
    with connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS counter (id INT PRIMARY KEY, value INT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO counter (id, value) VALUES (1, 0) ON CONFLICT (id) DO NOTHING"
        )
    db_initialized = True

def check_db():
    init_db()
    with connect() as conn:
        conn.execute("SELECT 1")

def increment_counter():
    """Increment the counter and return the value it had before."""
    with connect() as conn:
        row = conn.execute(
            "UPDATE counter SET value = value + 1 WHERE id = 1 RETURNING value - 1"
        ).fetchone()
    return row[0]

def get_counter():
    with connect() as conn:
        row = conn.execute("SELECT value FROM counter WHERE id = 1").fetchone()
    return row[0]

class Handler(BaseHTTPRequestHandler):
    def send_text(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        try:
            # Readiness probe: ready only when the database is reachable
            if self.path == "/healthz":
                check_db()
                self.send_text(200, "ok")
                return
            init_db()
            # The HTTPRoute rewrites /pingpong to /
            if self.path == "/":
                self.send_text(200, f"pong {increment_counter()}")
            elif self.path == "/pings":
                self.send_text(200, str(get_counter()))
            else:
                self.send_text(404, "Not found")
        except psycopg.Error as e:
            print(f"Database error: {e}", flush=True)
            self.send_text(503, "Database unavailable")

print(f"Server started in port {PORT}", flush=True)

server = HTTPServer(("0.0.0.0", PORT), Handler)
server.serve_forever()
