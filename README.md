# 🚀 Real-Time Data Streaming Pipeline
### **Kafka • Spark Structured Streaming • Airflow • Cassandra • Prometheus + Grafana • Docker**

An end-to-end, containerized **real-time data engineering pipeline**: an Airflow DAG pulls
events from a REST API into Kafka, Spark Structured Streaming processes them in micro-batches
and writes to Cassandra, and the whole system is instrumented with Prometheus + Grafana and a
Streamlit dashboard.

---

## 🧠 **Architecture Overview**

<img width="3274" height="1221" alt="Data engineering architecture" src="https://github.com/user-attachments/assets/bef8bce3-0bdb-439c-a648-36f68f9fd4d8" />

**Flow:** REST API → Airflow DAG → Kafka → Spark Structured Streaming → Cassandra, with
**JMX → Prometheus → Grafana** for metrics and a **Streamlit** app for the pipeline-level view.

✔ Real-time ingestion
✔ Event streaming
✔ Micro-batch processing (`foreachBatch` → Cassandra)
✔ Full observability (Prometheus + Grafana + Streamlit)
✔ Containerized deployment
✔ Restart-safe (persistent Spark checkpoint)

---

## 🏗️ **Tech Stack**

| Layer | Technology | Purpose |
|------|------------|---------|
| Orchestration | **Apache Airflow** | One DAG (`kafka_stream`): fetch from the REST API, publish to Kafka on a schedule |
| Messaging | **Apache Kafka** | Real-time event streaming (`users_created` topic) |
| Processing | **Spark Structured Streaming** | Consumes Kafka, transforms, writes to Cassandra via `foreachBatch` |
| Store | **Apache Cassandra** | Low-latency time-series store; time-based partition keys |
| Metrics | **Prometheus** | Scrapes Kafka + Cassandra JMX exporters and Spark's metrics sink |
| Dashboards | **Grafana + Streamlit** | Grafana for infra metrics; Streamlit for the pipeline-level view |
| Containers | **Docker + Docker Compose** | Full local environment |

> Note: this is a streaming pipeline — Cassandra is the only datastore. There is no Postgres /
> batch-serving layer.

---

## 📌 **Features**

### 1. Airflow-Driven Ingestion
- A single DAG (`kafka_stream`) fetches events from a REST API and publishes them to Kafka.
- Retry + logging around the producer send; chosen over cron for backfill and per-run visibility.

### 2. Kafka Event Streaming
- Partitioned `users_created` topic; retention configured to allow full replay on consumer failure.

### 3. Spark Structured Streaming
- Micro-batch consumption from Kafka, writing to Cassandra via `foreachBatch`.
- **Checkpointed to a persistent volume** (`/opt/spark/checkpoints`) so a restart resumes from the
  last committed Kafka offset instead of dropping or duplicating events.

### 4. Cassandra Real-Time Store
- Fast writes; time-based partition keys tuned for the time-series read pattern.

### 5. Observability — Prometheus + Grafana + Streamlit
- JMX exporters on Kafka and Cassandra + Spark's metrics sink → Prometheus → **Grafana panels**:
  msgs/sec, bytes in/out, under-replicated partitions, Cassandra write latency, storage, pending
  compactions.
- A **Streamlit** app surfaces the pipeline-level view: total events, average/peak events-per-second,
  write pressure, and replication health.

---

## ⚡ **Measured Throughput**

Load-tested locally with `stress_test_producer.py` on a single **2-core Spark worker**:

- **500,000 messages** sent in **179.38 s** → **~2,787 msg/sec** sustained producer throughput
- Grafana and the Streamlit dashboard show a peak of **~2.8k events/sec** end-to-end

The real API-driven workload runs well under this ceiling; the stress producer exists to exercise
the pipeline near its local limit.

---

## 🧱 **Reliability & Observability Hardening**

Correctness fixes applied after reviewing the pipeline's failure modes:

- **Checkpoint moved off `/tmp`** to a persistent volume — a container restart no longer wipes offset
  state (which would cause re-consume-from-latest data loss or re-consume-from-earliest duplication).
- **Prometheus counters incremented only after the Cassandra write confirms** (inside `try/except`
  with logging) — the dashboards no longer overcount on a failed or partial write.
- **Healthchecks on Kafka and Cassandra** so dependent services wait for readiness.
- **Corrected JMX exporter patterns** (COUNTER vs GAUGE) and Kafka metric names so the Grafana panels
  populate correctly.

---

## 🛠️ **How to Run the Pipeline**

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd Real-Time-Data-Streaming
```

### 2. (Optional) configure environment
```bash
cp .env.example .env   # set AIRFLOW_FERNET_KEY and GRAFANA_ADMIN_USER / GRAFANA_ADMIN_PASSWORD
```

### 3. Start the entire stack
```bash
docker compose up -d --build
```

### 4. Open the UIs
| Service | URL |
|---|---|
| Airflow | http://localhost:8080 |
| Spark Master | http://localhost:8085 |
| Grafana | http://localhost:3000 |
| Streamlit | http://localhost:8501 |

### 5. Trigger the ingestion DAG
Enable / trigger **`kafka_stream`** in the Airflow UI.

### 6. Verify data
- Kafka Control Center (topic `users_created`)
- Cassandra CQLSH: `SELECT * FROM realtime.users;`
- Grafana and Streamlit dashboards

### 7. (Optional) stress test
```bash
python stress_test_producer.py   # sends 500k messages to measure throughput
```

---

## 📘 **Future Enhancements**
- [ ] Spark batch job for nightly aggregates
- [ ] Grafana alerting on lag / write-timeout thresholds
- [ ] Deploy to Kubernetes (optional)
- [ ] CI/CD with GitHub Actions (optional)
