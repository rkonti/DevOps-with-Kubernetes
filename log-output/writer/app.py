import os
import time
import uuid
from datetime import datetime, timezone

LOG_FILE = os.getenv("LOG_FILE", "/usr/src/app/files/log.txt")

random_string = str(uuid.uuid4())

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

while True:
    timestamp = datetime.now(timezone.utc).isoformat()
    line = f"{timestamp}: {random_string}"
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
    print(line, flush=True)
    time.sleep(5)
