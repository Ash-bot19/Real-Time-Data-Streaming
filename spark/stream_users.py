from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, concat_ws
from pyspark.sql.types import StructType, StructField, StringType

KAFKA_BOOTSTRAP = "broker:29092"
TOPIC = "users_created"

CASSANDRA_HOST = "cassandra_db"
KEYSPACE = "realtime"
TABLE = "users"

# Define schema that mirrors the payload produced by kafka_stream DAG
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

def main():
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

    # Kafka value is bytes → cast to string
    json_df = df.selectExpr("CAST(value AS STRING) as json_data")

    parsed_df = json_df.select(
        from_json(col("json_data"), user_schema).alias("data")
    ).select("data.*")

    # Build a deterministic user_id by combining first and last names
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

    # Write to Cassandra (continuous)
    query = final_df.writeStream \
        .format("org.apache.spark.sql.cassandra") \
        .option("keyspace", KEYSPACE) \
        .option("table", TABLE) \
        .option("checkpointLocation", "/tmp/checkpoints/users") \
        .outputMode("append") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
