import argparse
import json
import os
import time
import uuid
from datetime import datetime

import pika

# RabbitMQ connection settings (must match docker-compose.yml)
RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_USER = os.getenv("RABBIT_USER", "user")
RABBIT_PASS = os.getenv("RABBIT_PASS", "pass")
RABBIT_VHOST = os.getenv("RABBIT_VHOST", "/")

def connect():
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(
        host=RABBIT_HOST,
        virtual_host=RABBIT_VHOST,
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=300,
    )
    return pika.BlockingConnection(params)

def main():
    parser = argparse.ArgumentParser(description="RabbitMQ Producer (transactional)")
    parser.add_argument("--queue", default="test_queue", help="Queue name to publish to")
    parser.add_argument("--count", type=int, default=1_000_000, help="How many messages to publish")
    parser.add_argument("--batch", type=int, default=1000, help="Commit every N messages (AMQP tx)")
    args = parser.parse_args()

    os.makedirs("results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", "producer.log")

    start = time.time()
    published = 0
    batch_count = 0

    with connect() as conn:
        ch = conn.channel()

        # Ensure the queue exists and is durable
        ch.queue_declare(queue=args.queue, durable=True, arguments={})

        # Enable AMQP transactions
        ch.tx_select()

        for i in range(args.count):
            msg_id = f"{uuid.uuid4()}-{i}"
            body = json.dumps({
                "id": msg_id,
                "seq": i,
                "ts": datetime.utcnow().isoformat() + "Z",
            }).encode("utf-8")

            props = pika.BasicProperties(
                delivery_mode=2,                 # persistent message
                content_type="application/json",
                message_id=msg_id,
            )

            ch.basic_publish(
                exchange="",
                routing_key=args.queue,
                body=body,
                properties=props,
            )
            published += 1
            batch_count += 1

            if published % 50_000 == 0:
                print(f"[{datetime.utcnow().isoformat()}Z] Published: {published}")

            if batch_count >= args.batch:
                ch.tx_commit()   # commit the batch
                batch_count = 0

        # Commit any remaining messages
        if batch_count > 0:
            ch.tx_commit()

    elapsed = time.time() - start
    print(f"[✓] Published {published} messages in {elapsed:.2f}s (transactional)")

    with open(os.path.join("results", "producer_output.json"), "w") as f:
        json.dump({
            "queue": args.queue,
            "published": published,
            "elapsed_seconds": elapsed,
            "host": RABBIT_HOST
        }, f, indent=2)

    with open(log_path, "w") as f:
        f.write(f"Published {published} messages to {args.queue} in {elapsed:.2f}s (tx)\n")

if __name__ == "__main__":
    main()
