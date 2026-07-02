import os
import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time

PROM_BASE = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
PROM_RANGE_URL = f"{PROM_BASE}/api/v1/query_range"
PROM_INSTANT_URL = f"{PROM_BASE}/api/v1/query"

st.set_page_config(layout="wide")
st.title("Operational Analytics – Streaming Pipeline")

# -------------------------
# Time Selector
# -------------------------

range_option = st.selectbox(
    "Select Time Range",
    ["1h", "6h", "24h", "Custom"],
    index=2
)

if range_option != "Custom":
    end = datetime.utcnow()
    if range_option == "1h":
        start = end - timedelta(hours=1)
    elif range_option == "6h":
        start = end - timedelta(hours=6)
    else:
        start = end - timedelta(hours=24)
else:
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    start = datetime.combine(start_date, time(0, 0, 0))
    end = datetime.combine(end_date, time(23, 59, 59))


# -------------------------
# Prometheus Query Helpers
# -------------------------

def query_prometheus_range(query, start, end, step="30s"):
    try:
        resp = requests.get(PROM_RANGE_URL, params={
            "query": query,
            "start": start.timestamp(),
            "end": end.timestamp(),
            "step": step,
        }, timeout=5)
        resp.raise_for_status()
        body = resp.json()
        if body.get("status") != "success":
            return []
        return body["data"]["result"]
    except Exception as e:
        st.warning(f"Prometheus range query failed: {e}")
        return []


def query_prometheus_instant(query):
    try:
        resp = requests.get(PROM_INSTANT_URL, params={"query": query}, timeout=5)
        resp.raise_for_status()
        body = resp.json()
        if body.get("status") != "success":
            return []
        return body["data"]["result"]
    except Exception as e:
        st.warning(f"Prometheus instant query failed: {e}")
        return []


# -------------------------
# Kafka Ingestion Rate
# -------------------------

# Note: _total suffix matches the COUNTER type in kafka-jmx.yml
kafka_query = "rate(kafka_server_brokertopicmetrics_messagesinpersec_topic_users_created_total[1m])"
result_kafka = query_prometheus_range(kafka_query, start, end)

if result_kafka:
    values = result_kafka[0]["values"]
    df = pd.DataFrame(values, columns=["timestamp", "value"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df["value"] = df["value"].astype(float)
else:
    df = pd.DataFrame(columns=["timestamp", "value"])

# -------------------------
# Kafka KPIs
# -------------------------

if not df.empty:
    total_events = np.trapz(df["value"], dx=30)
    avg_rate = df["value"].mean()
    peak_rate = df["value"].max()
    stability = df["value"].std() / avg_rate if avg_rate > 0 else 0
else:
    total_events = 0
    avg_rate = 0
    peak_rate = 0
    stability = 0

# -------------------------
# Cassandra Write Pressure
# -------------------------

cassandra_query = "rate(cassandra_clientrequest_scope_write_latency_total[1m])"
result_cassandra = query_prometheus_range(cassandra_query, start, end)

if result_cassandra:
    values_c = result_cassandra[0]["values"]
    df_c = pd.DataFrame(values_c, columns=["timestamp", "value"])
    df_c["value"] = df_c["value"].astype(float)
    write_pressure = df_c["value"].mean()
else:
    write_pressure = 0

# -------------------------
# Processing Ratio
# -------------------------

processing_ratio = write_pressure / avg_rate if avg_rate > 0 else 0

# -------------------------
# Replication Health
# -------------------------

replication_query = "kafka_server_replicamanager_underreplicatedpartitions"
result_replication = query_prometheus_instant(replication_query)

if result_replication:
    replication_health = float(result_replication[0]["value"][1])
else:
    replication_health = 0

# -------------------------
# Display KPIs
# -------------------------

# Row 1
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Events", f"{int(total_events)}")
col2.metric("Avg Rate (eps)", f"{avg_rate:.2f}")
col3.metric("Peak Rate (eps)", f"{peak_rate:.2f}")
col4.metric("Stability Index", f"{stability:.2f}")

# Row 2
col5, col6, col7, col8 = st.columns(4)
col5.metric("Processing Ratio", f"{processing_ratio:.2f}")
col6.metric("Write Pressure (µs/sec)", f"{write_pressure:.2f}")

if replication_health == 0:
    col7.metric("Replication Health", "Healthy")
else:
    col7.metric("Replication Health", f"{replication_health} Issues")

col8.empty()  # keeps spacing aligned

# -------------------------
# Trend Chart
# -------------------------

st.subheader("Ingestion Rate Trend")
if not df.empty:
    st.line_chart(df.set_index("timestamp")["value"])
else:
    st.info("No ingestion data available for selected range.")
