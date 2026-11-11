import asyncio
import json
import logging
import os
import signal
import sys
import urllib.request

import nats

NATS_URL = os.environ["NATS_URL"]
NATS_SUBJECT = "todos"
# All replicas join the same queue group, so NATS hands each message to only
# one of them and scaling up doesn't send duplicates
QUEUE_GROUP = "broadcaster"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
POD = os.getenv("HOSTNAME", "broadcaster")

logging.basicConfig(
    stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("broadcaster")

def format_message(event):
    todo = event["todo"]
    if event["action"] == "created":
        return f"A todo was created: {todo['content']}"
    if todo["done"]:
        return f"A todo was marked as done: {todo['content']}"
    return f"A todo was marked as not done: {todo['content']}"

def send_telegram(text):
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data=json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": text}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10):
        pass

async def handle(msg):
    try:
        text = format_message(json.loads(msg.data))
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        log.warning("Ignoring malformed message %r: %s", msg.data, e)
        return
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        log.info("[%s] Telegram not configured, would send: %s", POD, text)
        return
    try:
        await asyncio.to_thread(send_telegram, text)
        log.info("[%s] Sent to Telegram: %s", POD, text)
    except OSError as e:
        log.error("[%s] Failed to send to Telegram: %s", POD, e)

async def main():
    nc = await nats.connect(NATS_URL, max_reconnect_attempts=-1)
    await nc.subscribe(NATS_SUBJECT, queue=QUEUE_GROUP, cb=handle)
    log.info("[%s] Listening on subject %r in queue group %r", POD, NATS_SUBJECT, QUEUE_GROUP)

    stop = asyncio.Event()
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, stop.set)
    await stop.wait()
    # Finish the messages already received before shutting down
    await nc.drain()

asyncio.run(main())
