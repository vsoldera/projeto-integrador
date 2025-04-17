from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum, when, lit, avg

spark = SparkSession.builder.appName("TaxiDataAnalysis").getOrCreate()

bucket_name = os.getenv("S3_BUCKET")
file_key = "silver/*.parquet"
s3_path = f"s3a://{bucket_name}/{file_key}"
gold_path = f"s3a://{bucket_name}/gold"

payment_mapping = {
    1: "Credit card",
    2: "Cash",
    3: "No charge",
    4: "Dispute",
    5: "Unknown",
    6: "Voided trip",
}

rate_code_mapping = {
    1: "Standard rate",
    2: "JFK",
    3: "Newark",
    4: "Nassau or Westchester",
    5: "Negotiated fare",
    6: "Group ride",
    99: "Null/unknown",
}


def analyze_payment_types(df):
    payment_expr = when(col("payment_type") == 1, payment_mapping[1])
    for key, value in payment_mapping.items():
        payment_expr = payment_expr.when(col("payment_type") == key, value)
    df = df.withColumn("payment_name", payment_expr)

    payment_stats = (
        df.groupBy("payment_type", "payment_name")
        .agg(count("*").alias("count"), sum("total_amount").alias("total_amount"))
        .orderBy(col("count").desc())
    )

    return payment_stats


def analyze_rate_code_types(df):
    rate_code_expr = when(col("RatecodeID") == 1, rate_code_mapping[1])
    for key, value in rate_code_mapping.items():
        rate_code_expr = rate_code_expr.when(col("RatecodeID") == key, value)
    df = df.withColumn("rate_code_name", rate_code_expr)

    rate_code_stats = (
        df.groupBy("RatecodeID", "rate_code_name")
        .agg(count("*").alias("count"), sum("total_amount").alias("total_amount"))
        .orderBy(col("count").desc())
    )

    return rate_code_stats


def analyze_location_pu_do_frequency(df):
    pickup_df = df.select(col("PU_zone").alias("zone_name")).withColumn(
        "type", lit("pickup")
    )
    dropoff_df = df.select(col("DO_zone").alias("zone_name")).withColumn(
        "type", lit("dropoff")
    )
    return pickup_df.union(dropoff_df)


def analyze_fare_by_distance_bucket(df):
    df = df.withColumn(
        "distance_bucket",
        when(col("trip_distance") < 1, "<1 mile")
        .when((col("trip_distance") >= 1) & (col("trip_distance") < 3), "1-3 miles")
        .when((col("trip_distance") >= 3) & (col("trip_distance") < 6), "3-6 miles")
        .when((col("trip_distance") >= 6) & (col("trip_distance") < 10), "6-10 miles")
        .otherwise("10+ miles"),
    )

    distance_stats = (
        df.groupBy("distance_bucket")
        .agg(
            count("*").alias("trip_count"),
            avg("fare_amount").alias("avg_fare"),
            avg("total_amount").alias("avg_total"),
        )
        .orderBy("distance_bucket")
    )

    return distance_stats


def analyze_tip_by_payment_type(df):
    payment_expr = when(col("payment_type") == 1, payment_mapping[1])
    for key, value in payment_mapping.items():
        payment_expr = payment_expr.when(col("payment_type") == key, value)
    df = df.withColumn("payment_name", payment_expr)

    tip_stats = (
        df.groupBy("payment_name")
        .agg(
            count("*").alias("trip_count"),
            avg("tip_amount").alias("avg_tip"),
            sum("tip_amount").alias("total_tip"),
        )
        .orderBy(col("avg_tip").desc())
    )

    return tip_stats


def save_to_gold(df, analysis_name):
    output_path = f"{gold_path}/{analysis_name}"
    df.write.mode("overwrite").parquet(output_path)


if __name__ == "__main__":
    df = spark.read.parquet(s3_path)
    result_payment_type = analyze_payment_types(df)
    result_rate_code = analyze_rate_code_types(df)
    location_frequency_rate_code = analyze_location_pu_do_frequency(df)
    result_fare_by_distance = analyze_fare_by_distance_bucket(df)
    result_tip_by_payment = analyze_tip_by_payment_type(df)

    save_to_gold(result_payment_type, "payment_type")
    save_to_gold(result_rate_code, "rate_code_type")
    save_to_gold(
        location_frequency_rate_code.groupBy("zone_name", "type").agg(
            count("*").alias("count")
        ),
        "location_frequency",
    )
    save_to_gold(result_fare_by_distance, "fare_by_distance")
    save_to_gold(result_tip_by_payment, "tip_by_payment")
