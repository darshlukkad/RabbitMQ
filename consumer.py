import argparse
import json
import os
import time
from datetime import datetime

import pika

# RabbitMQ connection settings (match docker-compose.yml)
RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_USER = os.getenv("RABBIT_USER", "user")
RABBIT_PASS = os.getenv("RABBIT_PASS", "pass")
RABBIT_VHOST = os.getenv("RABBIT_VHOST", "/")

def connect():
    """Create a robust blocking connection to RabbitMQ."""
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
    parser = argparse.ArgumentParser(description="RabbitMQ Consumer")
    parser.add_argument("--queue", default="test_queue", help="Queue name to consume from")
    parser.add_argument("--count", type=int, default=10000, help="How many messages to consume before exiting")
    args = parser.parse_args()

    os.makedirs("results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", "consumer.log")

    consumed = 0
    start = time.time()

    with connect() as conn:
        ch = conn.channel()

        # Ensure queue exists and is durable (won't disappear when broker restarts)
        ch.queue_declare(queue=args.queue, durable=True)

        # Backpressure: don't flood this consumer; process at most 100 unacked at a time
        ch.basic_qos(prefetch_count=100)

        def callback(ch_, method, properties, body):
            nonlocal consumed
            consumed += 1

            # Here is where you'd process the message.
            # We'll keep it simple, but still ack only after "processing".
            # If processing fails, don't ack and the message can be redelivered.
            ch_.basic_ack(delivery_tag=method.delivery_tag)

            # Progress output every 1000 messages
            if consumed % 1000 == 0:
                print(f"[{datetime.utcnow().isoformat()}Z] Consumed: {consumed}")

            # Stop after reaching the requested count
            if consumed >= args.count:
                ch_.stop_consuming()

        # Manual acks to prevent message loss on consumer failure
        ch.basic_consume(queue=args.queue, on_message_callback=callback, auto_ack=False)

        print(f"[*] Waiting for {args.count} messages on '{args.queue}' ...")
        ch.start_consuming()

    elapsed = time.time() - start
    print(f"[✓] Consumed {consumed} messages in {elapsed:.2f}s")

    # Persist a JSON summary for later verification/report
    with open(os.path.join("results", "consumer_output.json"), "w") as f:
        json.dump({
            "queue": args.queue,
            "consumed": consumed,
            "elapsed_seconds": elapsed,
            "host": RABBIT_HOST
        }, f, indent=2)

    # Keep a simple text log too
    with open(log_path, "w") as f:
        f.write(f"Consumed {consumed} messages from {args.queue} in {elapsed:.2f}s\n")

if __name__ == "__main__":
    main()
