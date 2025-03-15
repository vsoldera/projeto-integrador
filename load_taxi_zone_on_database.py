import boto3
import pandas as pd
import psycopg2
import os
from io import StringIO
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")
CSV_FILE_KEY = os.getenv("CSV_FILE_KEY")

LOCAL_FILE_PATH = f"./{os.path.basename(CSV_FILE_KEY)}"

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
SCHEMA_NAME = os.getenv("SCHEMA_NAME", "public")
TABLE_NAME = os.getenv("TABLE_NAME")

s3_client = boto3.client("s3", region_name=AWS_REGION)


def check_local_file():
    if os.path.exists(LOCAL_FILE_PATH):
        return True
    return False


def download_csv_from_s3():
    obj = s3_client.get_object(Bucket=S3_BUCKET, Key=CSV_FILE_KEY)
    csv_content = obj["Body"].read().decode("utf-8")

    with open(LOCAL_FILE_PATH, "w") as file:
        file.write(csv_content)

    print(f"CSV file downloaded and saved locally as {LOCAL_FILE_PATH}")

    df = pd.read_csv(StringIO(csv_content))
    return df


def load_csv():
    if check_local_file():
        df = pd.read_csv(LOCAL_FILE_PATH)
    else:
        df = download_csv_from_s3()

    return df


def connect_to_postgres():
    print("Connecting to PostgreSQL RDS...")
    conn = psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT
    )
    print("Connected to PostgreSQL.")
    return conn, conn.cursor()


def create_schema_if_not_exists(cursor):
    print(f"Ensuring schema '{SCHEMA_NAME}' exists...")
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};")
    print(f"Schema '{SCHEMA_NAME}' is ready.")


def create_table_if_not_exists(df, cursor):
    print("Creating table if not exists...")

    columns = df.columns.tolist()
    sql_columns = ["LocationID INTEGER PRIMARY KEY"] + [
        f'"{col.lower()}" TEXT' for col in columns if col != "LocationID"
    ]
    sql_create_table = f"CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.{TABLE_NAME} ({', '.join(sql_columns)});"

    cursor.execute(sql_create_table)
    print(
        f"Table '{TABLE_NAME}' in schema '{SCHEMA_NAME}' checked/created successfully."
    )


def insert_data_into_table(df, conn, cursor, batch_size=500):
    print("Inserting data into PostgreSQL table in batches...")

    df = df.where(pd.notna(df), None)

    columns = df.columns.tolist()
    placeholders = ", ".join(["%s"] * len(columns))
    insert_query = f"""
    INSERT INTO {SCHEMA_NAME}.{TABLE_NAME} ({', '.join(columns)}) 
    VALUES ({placeholders}) 
    ON CONFLICT (LocationID) DO NOTHING;
    """

    data_tuples = [tuple(row) for row in df.itertuples(index=False, name=None)]

    for i in range(0, len(data_tuples), batch_size):
        batch = data_tuples[i : i + batch_size]
        cursor.executemany(insert_query, batch)
        conn.commit()

        print(
            f"Inserted {len(batch)} records (Total: {i + len(batch)}/{len(data_tuples)})"
        )

    print("Batch insertion completed successfully.")


def main():
    df = load_csv()

    conn, cursor = connect_to_postgres()

    try:
        create_schema_if_not_exists(cursor)

        create_table_if_not_exists(df, cursor)

        insert_data_into_table(df, conn, cursor)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
        print("PostgreSQL connection closed.")


if __name__ == "__main__":
    main()
