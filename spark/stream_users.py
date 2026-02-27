from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, concat_ws
from pyspark.sql.types import StructType, StructField, StringType
from prometheus_client import Counter, Gauge, start_http_server
import time

KAFKA_BOOTSTRAP = "broker:29092"
TOPIC = "users_created"

CASSANDRA_HOST = "cassandra_db"
KEYSPACE = "realtime"
TABLE = "users"

# ----------------------------
# Prometheus Business Metrics
# ----------------------------

records_processed_total = Counter(
    "records_processed_total",
    "Total records processed by Spark streaming job"
)

cassandra_write_total = Counter(
    "cassandra_write_total",
    "Total records written to Cassandra"
)

batch_duration_seconds = Gauge(
    "batch_duration_seconds",
    "Processing time per micro-batch"
)

# ----------------------------
# Schema Definition
# ----------------------------

user_schema = StructType([
    StructField("first_name", StringType()),
    StructField("last_name", StringType()),
    StructField("gender", StringType()),
    StructField("address", StringType()),
    StructField("email", StringType()),
    StructField("username", StringType()),
    StructField("dob", StringType()),
    StructField("registered", StringType()),
    StructField("phone", StringType()),
    StructField("picture", StringType()),
])


def process_batch(batch_df, batch_id):
    start_time = time.time()

    count = batch_df.count()

    if count > 0:
        batch_df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .options(keyspace=KEYSPACE, table=TABLE) \
            .save()

        records_processed_total.inc(count)
        cassandra_write_total.inc(count)

    duration = time.time() - start_time
    batch_duration_seconds.set(duration)


def main():
    # Start Prometheus metrics server
    start_http_server(8000)

    spark = SparkSession.builder \
        .appName("KafkaUserStream") \
        .config("spark.cassandra.connection.host", CASSANDRA_HOST) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Read from Kafka
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
        .option("subscribe", TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    json_df = df.selectExpr("CAST(value AS STRING) as json_data")

    parsed_df = json_df.select(
        from_json(col("json_data"), user_schema).alias("data")
    ).select("data.*")

    enriched_df = parsed_df.withColumn(
        "user_id", concat_ws("_", col("first_name"), col("last_name"))
    )

    final_df = enriched_df.select(
        "user_id",
        "first_name",
        "last_name",
        "gender",
        "address",
        "email",
        "username",
        "dob",
        "registered",
        "phone",
        "picture",
    )

    # Use foreachBatch for instrumentation
    query = final_df.writeStream \
        .foreachBatch(process_batch) \
        .option("checkpointLocation", "/tmp/checkpoints/users") \
        .outputMode("append") \
        .start()

    query.awaitTermination()


if __name__ == "__main__":
    main()