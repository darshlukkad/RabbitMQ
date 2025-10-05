# 🐇 RabbitMQ Message Queue Assignment — 10,000 Messages (No Loss)

A minimal, reliable demo of **asynchronous messaging** using **RabbitMQ**.  
It includes a **Producer** that publishes **10,000** persistent messages and a **Consumer** that receives and manually acknowledges them.  
Verification is done via RabbitMQ’s **Management API** and an auto-generated **report**.

---

## ✨ Features
- **Durable queue** + **persistent messages** (`delivery_mode=2`)
- **Manual acks** to prevent loss on consumer failure
- **QoS prefetch** for backpressure (`prefetch_count=100`)
- **Transactional publishing** (AMQP `tx_select/tx_commit`) for robust broker-side acceptance
- **Counts captured** from producer, consumer, and HTTP API
- Auto **Report.md** (≤ 4 pages) for submission

---

## 🧰 Prerequisites
- **Docker Desktop** running
- **Python 3.9+**
- **pip**
- (Recommended) **VS Code** with Python extension

---

## 🚀 Quick Start

### 1) Start RabbitMQ
```bash
docker compose up -d
# UI: http://localhost:15672  (user / pass)
