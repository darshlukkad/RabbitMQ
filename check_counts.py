import json
import os
import requests

# RabbitMQ Management API settings
RABBIT_HTTP = os.getenv("RABBIT_HTTP", "http://localhost:15672")
RABBIT_USER = os.getenv("RABBIT_USER", "user")
RABBIT_PASS = os.getenv("RABBIT_PASS", "pass")
RABBIT_VHOST = os.getenv("RABBIT_VHOST", "/")

def get_queue_stats(queue: str):
    # URL-encode "/" vhost
    vhost_enc = "%2F" if RABBIT_VHOST == "/" else RABBIT_VHOST
    url = f"{RABBIT_HTTP}/api/queues/{vhost_enc}/{queue}"
    resp = requests.get(url, auth=(RABBIT_USER, RABBIT_PASS), timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "name": data.get("name"),
        "vhost": data.get("vhost"),
        "messages": data.get("messages"),
        "messages_ready": data.get("messages_ready"),
        "messages_unacknowledged": data.get("messages_unacknowledged"),
        "consumers": data.get("consumers"),
    }

def main():
    os.makedirs("results", exist_ok=True)

    # Determine queue name from producer/consumer outputs, fallback to default
    queue = "test_queue"
    for fname in ("producer_output.json", "consumer_output.json"):
        p = os.path.join("results", fname)
        if os.path.exists(p):
            try:
                with open(p) as f:
                    q = json.load(f).get("queue")
                    if q:
                        queue = q
            except Exception:
                pass

    stats = get_queue_stats(queue)

    # Merge producer/consumer summaries (if present) with API stats into one file
    combined = {}
    for fname in ("producer_output.json", "consumer_output.json"):
        p = os.path.join("results", fname)
        if os.path.exists(p):
            with open(p) as f:
                combined.update(json.load(f))

    combined["queue_stats"] = stats

    out_path = os.path.join("results", "results.json")
    with open(out_path, "w") as f:
        json.dump(combined, f, indent=2)

    print("Wrote", out_path)
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
