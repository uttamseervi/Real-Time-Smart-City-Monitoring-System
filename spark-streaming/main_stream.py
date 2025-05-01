# from pyspark.sql import SparkSession
# from pyspark.sql.functions import col
# from pyspark.sql.types import StructType, StructField, String, Integer
# from kafka import KafkaConsumer
# import json

# # Initialize Spark session
# spark = SparkSession.builder.appName("SmartCityMonitor").getOrCreate()

# # Define schema for traffic, AQI, weather data
# traffic_schema = StructType([
#     StructField("junction", String(), True),
#     StructField("timestamp", String(), True),
#     StructField("vehicles_per_minute", Integer(), True),
#     StructField("avg_speed_kmph", Integer(), True)
# ])

# # Consume traffic data
# traffic_df = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "localhost:9093").option("subscribe", "traffic-data").load()

# # Process traffic data
# traffic_df = traffic_df.selectExpr("CAST(value AS STRING)").select(from_json("value", traffic_schema).alias("data"))
# traffic_df = traffic_df.select("data.*")

# # Example enrichment
# enriched_df = traffic_df.withColumn("congestion_level", (col("vehicles_per_minute") > 150).cast("string"))

# # Write to MongoDB (or another system)
# enriched_df.writeStream.format("mongo").option("uri", "mongodb://localhost/smartcity.traffic_data").outputMode("append").start().awaitTermination()


# =========================
# 1. WEATHER CONSUMER
# =========================
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, FloatType, LongType

# WEATHER Schema
weather_schema = StructType() \
    .add("location", StringType()) \
    .add("temperature", FloatType()) \
    .add("feels_like", FloatType()) \
    .add("humidity", FloatType()) \
    .add("pressure", FloatType()) \
    .add("wind_speed", FloatType()) \
    .add("weather", StringType()) \
    .add("description", StringType()) \
    .add("timestamp", LongType())

spark = SparkSession.builder \
    .appName("WeatherConsumer") \
    .config("spark.mongodb.output.uri", "mongodb://localhost:27017/smart_city.weather_data") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

weather_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "192.168.5.218:9092") \
    .option("subscribe", "weather") \
    .option("startingOffsets", "latest") \
    .load()

weather_json = weather_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), weather_schema).alias("data")).select("data.*")

weather_query = weather_json.writeStream \
    .format("mongodb") \
    .option("checkpointLocation", "/tmp/checkpoints/weather") \
    .outputMode("append") \
    .start()


# =========================
# 2. AQI CONSUMER
# =========================
from pyspark.sql.types import IntegerType

# AQI Schema
aqi_schema = StructType() \
    .add("parameter", StringType()) \
    .add("value", FloatType()) \
    .add("unit", StringType()) \
    .add("coordinates", StructType() \
        .add("latitude", FloatType()) \
        .add("longitude", FloatType())) \
    .add("country", StringType()) \
    .add("city", StringType()) \
    .add("location", StringType()) \
    .add("date", StructType().add("utc", StringType()).add("local", StringType()))

spark_aqi = SparkSession.builder \
    .appName("AQIConsumer") \
    .config("spark.mongodb.output.uri", "mongodb://localhost:27017/smart_city.aqi_data") \
    .getOrCreate()

spark_aqi.sparkContext.setLogLevel("WARN")

aqi_df = spark_aqi.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "aqi_data") \
    .option("startingOffsets", "latest") \
    .load()

aqi_json = aqi_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), aqi_schema).alias("data")).select("data.*")

aqi_query = aqi_json.writeStream \
    .format("mongodb") \
    .option("checkpointLocation", "/tmp/checkpoints/aqi") \
    .outputMode("append") \
    .start()


# =========================
# 3. TRAFFIC CONSUMER
# =========================
# TRAFFIC Schema
traffic_schema = StructType() \
    .add("frc", StringType()) \
    .add("currentSpeed", FloatType()) \
    .add("freeFlowSpeed", FloatType()) \
    .add("currentTravelTime", IntegerType()) \
    .add("freeFlowTravelTime", IntegerType()) \
    .add("confidence", FloatType()) \
    .add("roadClosure", StringType())

spark_traffic = SparkSession.builder \
    .appName("TrafficConsumer") \
    .config("spark.mongodb.output.uri", "mongodb://localhost:27017/smart_city.traffic_data") \
    .getOrCreate()

spark_traffic.sparkContext.setLogLevel("WARN")

traffic_df = spark_traffic.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "traffic") \
    .option("startingOffsets", "latest") \
    .load()

traffic_json = traffic_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), traffic_schema).alias("data")).select("data.*")

traffic_query = traffic_json.writeStream \
    .format("mongodb") \
    .option("checkpointLocation", "/tmp/checkpoints/traffic") \
    .outputMode("append") \
    .start()

# Await Termination for all
weather_query.awaitTermination()
aqi_query.awaitTermination()
traffic_query.awaitTermination()
