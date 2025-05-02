from pyspark.sql import SparkSession

# Initialize Spark session
spark = SparkSession.builder.appName("test").getOrCreate()

# Test the Spark session
df = spark.range(100).toDF("number")
df.show()
