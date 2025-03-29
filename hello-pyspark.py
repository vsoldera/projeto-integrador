from pyspark.sql import SparkSession


def main():
    # Create a Spark session
    spark = (
        SparkSession.builder.appName("HelloWorld")
        .master("spark://localhost:7077")
        .getOrCreate()
    )

    # Create a DataFrame with a single message
    df = spark.createDataFrame([("Hello, World!",)], ["message"])

    # Show the DataFrame
    df.show()

    # Stop the Spark session
    spark.stop()


if __name__ == "__main__":
    main()
