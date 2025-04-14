from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import *
import os

# For EMR, we'll use environment variables in a different way
# since we can configure these when submitting the job or store them in AWS Parameter Store
# For simplicity in this example, we're hardcoding them here
# In production, you should use AWS Secrets Manager or Parameter Store

# Database connection parameters
DB_HOST = (
    "terraform-20250405130438770700000001.c1zcqqywakmt.us-east-1.rds.amazonaws.com"
)
DB_PORT = "5432"
DB_NAME = "taxilookupdb"
DB_USER = "foo"
DB_PASSWORD = "foobarbaz"
SCHEMA_NAME = "taxi"
TABLE_NAME = "tb_taxi_zone_lookup"

url = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configure Spark session specifically for EMR
spark = (
    SparkSession.builder.appName("TaxiDataProcessor")
    .config("spark.jars.packages", "org.postgresql:postgresql:42.5.1")
    .getOrCreate()
)

# Set S3 access mode to path style - may be needed depending on your S3 configuration
spark._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")
spark._jsc.hadoopConfiguration().set(
    "fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem"
)

# Define schema - this matches the schema from your original script
schema = StructType(
    [
        StructField("VendorID", IntegerType(), True),
        StructField("tpep_pickup_datetime", TimestampType(), True),
        StructField("tpep_dropoff_datetime", TimestampType(), True),
        StructField("passenger_count", LongType(), True),
        StructField("trip_distance", DoubleType(), True),
        StructField("RatecodeID", LongType(), True),
        StructField("store_and_fwd_flag", StringType(), True),
        StructField("PULocationID", IntegerType(), True),
        StructField("DOLocationID", IntegerType(), True),
        StructField("payment_type", LongType(), True),
        StructField("fare_amount", DoubleType(), True),
        StructField("extra", DoubleType(), True),
        StructField("mta_tax", DoubleType(), True),
        StructField("tip_amount", DoubleType(), True),
        StructField("tolls_amount", DoubleType(), True),
        StructField("improvement_surcharge", DoubleType(), True),
        StructField("total_amount", DoubleType(), True),
        StructField("congestion_surcharge", DoubleType(), True),
        StructField("airport_fee", DoubleType(), True),
    ]
)

# S3 paths - using the same path from your original script
s3_path = "s3a://taxi-raw-grupo-5"

# Read data from S3
print(f"Reading Parquet files from: {s3_path}/bronze")
df = spark.read.schema(schema).format("parquet").load(f"{s3_path}/bronze")

# Remove rows with null passenger_count
df_cleaned = df.filter(col("passenger_count").isNotNull())
print(f"Data after cleaning: {df_cleaned.count()} rows")

# Load taxi zone data from PostgreSQL
print("Loading taxi zone data from PostgreSQL")
taxi_zone_df = (
    spark.read.format("jdbc")
    .option("url", url)
    .option("dbtable", f"{SCHEMA_NAME}.{TABLE_NAME}")
    .option("user", DB_USER)
    .option("password", DB_PASSWORD)
    .option("driver", "org.postgresql.Driver")
    .load()
)

# Join with location data
print("Joining with location data")
zone_df_pickup = taxi_zone_df.alias("pickup")
zone_df_dropoff = taxi_zone_df.alias("dropoff")

joined_df = (
    df_cleaned.alias("taxi")
    .join(
        zone_df_pickup,
        col("taxi.PULocationID") == col("pickup.locationid"),
        "inner",
    )
    .join(
        zone_df_dropoff,
        col("taxi.DOLocationID") == col("dropoff.locationid"),
        "inner",
    )
)

result_df = joined_df.select(
    col("taxi.*"),
    col("pickup.borough").alias("PU_borough"),
    col("pickup.zone").alias("PU_zone"),
    col("pickup.service_zone").alias("PU_service_zone"),
    col("dropoff.borough").alias("DO_borough"),
    col("dropoff.zone").alias("DO_zone"),
    col("dropoff.service_zone").alias("DO_service_zone"),
)

# Write output to S3
print(f"Writing processed data to: {s3_path}/silver")
result_df.repartition(5).write.mode("overwrite").parquet(f"{s3_path}/silver")

print("Processing complete")
spark.stop()
