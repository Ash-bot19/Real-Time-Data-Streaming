import json
import uuid
import time
import argparse
from kafka import KafkaProducer
from concurrent.futures import ThreadPoolExecutor

parser = argparse.ArgumentParser()
parser.add_argument("--messages", type=int, default=100000)
parser.add_argument("--workers", type=int, default=20)
args = parser.parse_args()

producer = KafkaProducer(
    bootstrap_servers=["broker:29092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    linger_ms=5,
    batch_size=32768,
    retries=5,
)

def generate_user():
    return {
        "first_name": "stress",
        "last_name": str(uuid.uuid4()),
        "gender": "test",
        "address": "load test address",
        "email": "load@test.com",
        "username": str(uuid.uuid4()),
        "dob": "2000-01-01",
        "registered": "2020-01-01",
        "phone": "0000000000",
        "picture": "none",
    }

def send():
    future = producer.send("users_created", generate_user())
    try:
        future.get(timeout=10)
    except Exception as e:
        print(f"[ERROR] Delivery failed: {e}", flush=True)

start = time.time()

with ThreadPoolExecutor(max_workers=args.workers) as executor:
    for _ in range(args.messages):
        executor.submit(send)

producer.flush()
end = time.time()

print(f"Sent {args.messages} messages")
print(f"Time taken: {round(end-start,2)} seconds")
print(f"Throughput: {round(args.messages/(end-start),2)} msg/sec")