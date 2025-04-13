from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum, when

spark = SparkSession.builder \
    .appName("TaxiDataAnalysis") \
    .getOrCreate()

bucket_name = 'taxi-raw-grupo-555'
file_key = 'silver/*.parquet'
s3_path = f"s3a://{bucket_name}/{file_key}"

payment_mapping = {
    1: "Credit card",
    2: "Cash",
    3: "No charge",
    4: "Dispute",
    5: "Unknown",
    6: "Voided trip"
}

def analyze_payment_types():

    df = spark.read.parquet(s3_path)
    
    payment_expr = when(col("payment_type") == 1, payment_mapping[1])
    for key, value in payment_mapping.items():
        payment_expr = payment_expr.when(col("payment_type") == key, value)
    df = df.withColumn("payment_name", payment_expr)
    
    payment_stats = df.groupBy("payment_type", "payment_name") \
        .agg(
            count("*").alias("count"),
            sum("total_amount").alias("total_amount")
        ) \
        .orderBy(col("count").desc())
    
    return payment_stats

if __name__ == "__main__":
    result = analyze_payment_types()
    
    print("Tipos de pagamento mais usados com valores totais:")
    result.select(
        "payment_name",
        "count",
        col("total_amount").cast("decimal(38,2)").alias("total_amount")
    ).show(truncate=False)