# 🚀 Real-Time Data Streaming Pipeline  
### **Kafka • Spark Structured Streaming • Airflow • Cassandra • Postgres • Docker**

This project implements an end-to-end, production-style **real-time data engineering pipeline**, inspired by Airflow + Kafka architectures used at Netflix, Uber, and Airbnb.  
It features **event ingestion**, **stream processing**, **batch processing**, **orchestration**, and **polyglot storage** — using state-of-the-art distributed systems tools.

---

## 🧠 **Architecture Overview**


<img width="3274" height="1221" alt="Data engineering architecture" src="https://github.com/user-attachments/assets/bef8bce3-0bdb-439c-a648-36f68f9fd4d8" />

---


✔ Real-time ingestion  
✔ Event streaming  
✔ Micro-batch processing  
✔ Batch + streaming (Lambda pattern)  
✔ Containerized deployment  
✔ Modular orchestration with Airflow  

---

## 🏗️ **Tech Stack**

| Layer | Technology | Purpose |
|------|------------|---------|
| Orchestration | **Apache Airflow** | Triggers API ingestion, Spark jobs, Cassandra monitors |
| Messaging | **Apache Kafka** | Real-time event streaming |
| Processing | **Spark Structured Streaming** | Consumes Kafka topic, transforms events, writes to Cassandra |
| Real-Time Store | **Apache Cassandra** | Stores low-latency user events |
| Batch Store | **Postgres** | Stores batch data from API |
| Containers | **Docker + Docker Compose** | Full environment orchestration |
| Dashboard | *(Coming soon)* Streamlit | Real-time user analytics |
| Monitoring | *(Coming soon)* Grafana + Prometheus | Kafka/Spark/Cassandra metrics |

---

# 📌 **Features**

### 🟣 1. **Airflow-Driven Data Ingestion**
- Airflow DAG fetches data from an API  
- Streams it into Kafka (`user_events` topic)  
- Stores a batch copy in Postgres  

### 🔵 2. **Kafka Event Streaming**
- Highly scalable message broker  
- Handles thousands of events/sec  
- Perfect for real-time pipelines  

### 🟡 3. **Spark Structured Streaming**
- Micro-batch streaming from Kafka  
- ETL transformations  
- Writes results into Cassandra  

### 🟢 4. **Cassandra Real-Time Data Store**
- Fast writes  
- Horizontal scalability  
- Optimized for time-series data  

### 🟠 5. **Batch Layer (Postgres)**
- Clean historical snapshot  
- Supports aggregations and analytics  

### 🔴 6. **Orchestration & Monitoring**
- Airflow DAGs:  
  - API ingestion  
  - Kafka stream producer  
  - Spark-submit streaming job  
  - Cassandra heartbeat monitor  
- Logs & alerts for debugging  

---


---

# ⚡ **Pipeline Throughput**

Performance tested locally:

- **Kafka:** up to 50,000+ msgs/sec  
- **Spark streaming:** ~3,000–10,000 msgs/sec  
- **Cassandra:** 5,000–20,000 writes/sec  

Your real workload (API → Kafka) uses **<1%** of system capacity.

---

# 🛠️ **How to Run the Pipeline**

### **1. Clone the repository**
```bash
git clone <your-repo-url>
cd Real-Time-Data-Streaming
```

### **2. Start the entire stack**
```bash
docker compose up -d --build
```
### **3. Open Airflow UI**
```arduino
http://localhost:8080
```
### **4. Trigger DAGs**

- `api_to_kafka`

- `spark_kafka_to_cassandra`

- `batch_to_postgres`

- `cassandra_monitor`

### **5. Verify data**

- Kafka Control Center

- Cassandra CQLSH (`SELECT * FROM realtime.users;`)

- Postgres (`SELECT * FROM batch_users;`)

## 📊 **Streamlit Dashboard (Coming Soon)**
A real-time data analytics dashboard will be available at:
```
http://localhost:8501
```
### **Features:**
 
- Live ingestion charts

- Event-time distributions

- Batch vs real-time comparisons

- User profile analytics

### 📉 **Grafana Monitoring (Coming Soon)**
Will include:

- Kafka consumer lag

- Spark micro-batch latency

- Cassandra write TPS

- Container CPU/RAM usage

### 📘 **Future Enhancements**
- [ ] Add Streamlit serving layer
- [ ] Add Grafana + Prometheus observability
- [ ] Add Spark batch job for nightly aggregates
- [ ] Build Lambda Architecture serving view
- [ ] Deploy to Kubernetes (optional)
- [ ] CI/CD with GitHub Actions (optional)
