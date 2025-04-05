from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import *
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
table = os.getenv("TABLE_NAME")
schema_table = os.getenv("SCHEMA_NAME")
url = f"jdbc:postgresql://{host}:{port}/{db_name}"


class S3ParquetReader:
    def __init__(self, s3_path: str):
        self.schema = StructType(
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
        self.s3_path = s3_path
        self.spark = spark = (
            SparkSession.builder.appName("S3ParquetReader")
            .config(
                "spark.jars.packages",
                "org.apache.hadoop:hadoop-aws:3.3.6,com.amazonaws:aws-java-sdk-bundle:1.12.540",
            )
            .config(
                "spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem"
            )
            .getOrCreate()
        )

    def read_parquet(self):
        print(f"Reading Parquet files from: {self.s3_path}")
        df = (
            self.spark.read.schema(self.schema)
            .format("parquet")
            .load(f"{self.s3_path}/bronze")
        )
        return df

    def remove_none_value_based_on_passenger(self, df):
        df_cleaned = df.filter(col("passenger_count").isNotNull())
        return df_cleaned

    def load_taxi_zone(self):
        df = (
            spark.read.format("jdbc")
            .option("url", url)
            .option("dbtable", f"{schema_table}.{table}")
            .option("user", user)
            .option("password", password)
            .option("driver", "org.postgresql.Driver")
            .load()
        )
        return df

    def join_locations(self, taxi_df, zone_df):
        zone_df_pickup = zone_df.alias("pickup")
        zone_df_dropoff = zone_df.alias("dropoff")

        joined_df = (
            taxi_df.alias("taxi")
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
        return result_df

    def write_parquet(self, df):
        df = df.repartition(5)
        df.write.mode("overwrite").parquet(f"{self.s3_path}/silver")

    def stop(self):
        self.spark.stop()


def main():
    s3_path = "s3a://taxi-lookup-projeto-integrador"
    reader = S3ParquetReader(s3_path)
    df = reader.read_parquet()
    taxi_zone_df = reader.load_taxi_zone()
    df_cleaned = reader.remove_none_value_based_on_passenger(df)
    joined_df = reader.join_locations(df_cleaned, taxi_zone_df)
    reader.write_parquet(joined_df)
    reader.stop()


main()
