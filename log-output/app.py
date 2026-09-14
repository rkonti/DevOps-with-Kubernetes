import time 
import uuid 
from datetime import datetime, timezone 

random_string = str(uuid.uuid4())

while True:
    timestamp = datetime.now(timezone.utc).isoformat()
    print(f"{timestamp}: {random_string}", flush=True)
    time.sleep(5)


