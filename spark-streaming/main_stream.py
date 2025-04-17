from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import StructType, StructField, String, Integer
from kafka import KafkaConsumer
import json

# Initialize Spark session
spark = SparkSession.builder.appName("SmartCityMonitor").getOrCreate()

# Define schema for traffic, AQI, weather data
traffic_schema = StructType([
    StructField("junction", String(), True),
    StructField("timestamp", String(), True),
    StructField("vehicles_per_minute", Integer(), True),
    StructField("avg_speed_kmph", Integer(), True)
])

# Consume traffic data
traffic_df = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "localhost:9093").option("subscribe", "traffic-data").load()

# Process traffic data
traffic_df = traffic_df.selectExpr("CAST(value AS STRING)").select(from_json("value", traffic_schema).alias("data"))
traffic_df = traffic_df.select("data.*")

# Example enrichment
enriched_df = traffic_df.withColumn("congestion_level", (col("vehicles_per_minute") > 150).cast("string"))

# Write to MongoDB (or another system)
enriched_df.writeStream.format("mongo").option("uri", "mongodb://localhost/smartcity.traffic_data").outputMode("append").start().awaitTermination()
