from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

KAFKA_BOOTSTRAP = "broker:29092"
TOPIC = "users_created"

CASSANDRA_HOST = "cassandra_db"
KEYSPACE = "realtime"
TABLE = "users"

# Define schema of incoming JSON
user_schema = StructType([
    StructField("user_id", IntegerType()),
    StructField("name", StringType()),
    StructField("email", StringType()),
    StructField("age", IntegerType()),
    StructField("country", StringType())
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

    parsed_df = json_df.select(from_json(col("json_data"), user_schema).alias("data")).select("data.*")

    # Write to Cassandra (continuous)
    query = parsed_df.writeStream \
        .format("org.apache.spark.sql.cassandra") \
        .option("keyspace", KEYSPACE) \
        .option("table", TABLE) \
        .option("checkpointLocation", "/tmp/checkpoints/users") \
        .outputMode("append") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
