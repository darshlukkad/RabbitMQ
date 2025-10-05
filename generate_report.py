import json
import os
import textwrap
from datetime import datetime

def main():
    results_path = os.path.join("results", "results.json")
    if not os.path.exists(results_path):
        raise SystemExit("Run producer, consumer, then check_counts.py first to create results.json")

    with open(results_path) as f:
        r = json.load(f)

    published = r.get("published", 0)
    consumed = r.get("consumed", 0)
    queue_stats = r.get("queue_stats", {})
    messages = queue_stats.get("messages", "?")
    ready = queue_stats.get("messages_ready", "?")
    unacked = queue_stats.get("messages_unacknowledged", "?")
    queue = r.get("queue", "test_queue")

    # Pass if all conditions show no loss
    pass_fail = (
        published == 10000 and consumed == 10000 and messages == 0 and ready == 0 and unacked == 0
    )

    body = f"""
# RabbitMQ Asynchronous Messaging Verification

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Queue:** `{queue}`  
**Broker:** {r.get("host","localhost")} (HTTP API snapshot after run)

## 1. Objective
Validate asynchronous messaging with RabbitMQ by sending **10,000** persistent messages from a Producer and receiving them with a Consumer, ensuring **no message loss**. Verification uses durable queues, persistent messages, manual acknowledgements, and post-run queue metrics.

## 2. Architecture & Setup
- **Broker:** RabbitMQ (Docker, management plugin enabled)
- **Queue:** Durable queue; persistent messages
- **Producer:** Python + pika; **transactional publishing** (AMQP `tx_select/tx_commit`)
- **Consumer:** Python + pika; manual acks; `basic_qos(prefetch_count=100)`
- **Verification:** Producer/consumer JSON outputs + Management API stats

## 3. Methodology
1. Start RabbitMQ (`docker compose up -d`).
2. Run **consumer** first: `python consumer.py --count 10000`.
3. Run **producer**: `python producer.py --count 10000`.
4. Collect queue stats: `python check_counts.py` (writes `results/results.json`).
5. Render this report: `python generate_report.py`.

## 4. Results
- **Producer published:** {published}
- **Consumer consumed:** {consumed}
- **Queue metrics (post-run):**
  - `messages`: {messages}
  - `messages_ready`: {ready}
  - `messages_unacknowledged`: {unacked}

### Pass/Fail
- **Overall verdict:** {"PASS ✅" if pass_fail else "FAIL ❌"}

## 5. Reliability Considerations
- **Durability:** `queue_declare(..., durable=True)` and `delivery_mode=2`.
- **Transactional Publishing:** Batches committed with `tx_commit()` ensure broker acceptance.
- **Manual Acks:** `auto_ack=False` so unprocessed messages are re-queued on failure.
- **Backpressure:** `basic_qos(prefetch_count=100)` to avoid overload and preserve fairness.

## 6. Troubleshooting (if FAIL)
- Check the management UI (http://localhost:15672) for message buildup.
- Inspect logs in `logs/producer.log` and `logs/consumer.log`.
- Confirm both scripts used the **same queue** name.
- Ensure ports **5672** (AMQP) and **15672** (UI) are accessible.
- Retry with a clean queue or new name, e.g.: `--queue run_$(date +%s)`.
- Restart broker: `docker compose down -v && docker compose up -d`.

## 7. Conclusion
The test demonstrates fault-tolerant, event-driven, asynchronous messaging with RabbitMQ. When the metrics show all **10,000** messages were published and consumed, and the queue has **0 messages ready/unacknowledged**, we conclude **no message loss** under the tested conditions.
"""
    body = textwrap.dedent(body).strip() + "\n"

    with open("Report.md", "w") as f:
        f.write(body)

    print("Wrote Report.md")

if __name__ == "__main__":
    main()
