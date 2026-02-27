import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

PROM_RANGE_URL = "http://prometheus:9090/api/v1/query_range"
PROM_INSTANT_URL = "http://prometheus:9090/api/v1/query"

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
    start = datetime.combine(start_date, datetime.min.time())
    end = datetime.combine(end_date, datetime.min.time())

# -------------------------
# Kafka Ingestion Rate
# -------------------------

kafka_query = "rate(kafka_server_brokertopicmetrics_messagesinpersec_topic_users_created[1m])"

params_kafka = {
    "query": kafka_query,
    "start": start.timestamp(),
    "end": end.timestamp(),
    "step": "30s"
}

response_kafka = requests.get(PROM_RANGE_URL, params=params_kafka)
data_kafka = response_kafka.json()

if data_kafka["data"]["result"]:
    values = data_kafka["data"]["result"][0]["values"]
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

params_cassandra = {
    "query": cassandra_query,
    "start": start.timestamp(),
    "end": end.timestamp(),
    "step": "30s"
}

response_cassandra = requests.get(PROM_RANGE_URL, params=params_cassandra)
data_cassandra = response_cassandra.json()

if data_cassandra["data"]["result"]:
    values_c = data_cassandra["data"]["result"][0]["values"]
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

params_replication = {
    "query": replication_query
}

response_replication = requests.get(PROM_INSTANT_URL, params=params_replication)
data_replication = response_replication.json()

if data_replication["data"]["result"]:
    replication_health = float(data_replication["data"]["result"][0]["value"][1])
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