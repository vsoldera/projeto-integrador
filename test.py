from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.operators.emr import (
    EmrCreateJobFlowOperator,
    EmrAddStepsOperator,
    EmrTerminateJobFlowOperator
)
from airflow.providers.amazon.aws.sensors.emr import EmrStepSensor
from airflow.providers.amazon.aws.transfers.local_to_s3 import LocalFilesystemToS3Operator
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

# Default arguments for DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

S3_BUCKET = "taxi-raw-grupo-5"  # Using the same bucket from your script
S3_SCRIPT_KEY = "scripts/taxi_data_processor.py"  # Path to store the script
LOCAL_SCRIPT_PATH = "/opt/airflow/dags/taxi_data_processor.py"  # Local path on EC2

# EMR Cluster configuration
JOB_FLOW_OVERRIDES = {
    "Name": "Taxi Data Processing Cluster",
    "ReleaseLabel": "emr-6.10.0",
    "Applications": [{"Name": "Spark"}],
    "Instances": {
        "InstanceGroups": [
            {
                "Name": "Master node",
                "Market": "ON_DEMAND",
                "InstanceRole": "MASTER",
                "InstanceType": "m5.xlarge",
                "InstanceCount": 1,
            },
            {
                "Name": "Core nodes",
                "Market": "ON_DEMAND",
                "InstanceRole": "CORE",
                "InstanceType": "m5.xlarge",
                "InstanceCount": 2,
            },
        ],
        "KeepJobFlowAliveWhenNoSteps": False,
        "TerminationProtected": False,
    },
    "JobFlowRole": "EMR_EC2_DefaultRole",
    "ServiceRole": "EMR_DefaultRole",
    "LogUri": f"s3://{S3_BUCKET}/logs/",
    "VisibleToAllUsers": True,
    "Tags": [
        {"Key": "Environment", "Value": "Development"},
        {"Key": "Project", "Value": "TaxiDataProcessing"}
    ]
}

# Spark step to run the PySpark script
SPARK_STEP = [
    {
        "Name": "Process Taxi Data",
        "ActionOnFailure": "TERMINATE_CLUSTER",
        "HadoopJarStep": {
            "Jar": "command-runner.jar",
            "Args": [
                "spark-submit",
                "--deploy-mode", "cluster",
                "--master", "yarn",
                "--conf", "spark.yarn.submit.waitAppCompletion=true",
                "--packages", "org.postgresql:postgresql:42.5.1,org.apache.hadoop:hadoop-aws:3.3.6,com.amazonaws:aws-java-sdk-bundle:1.12.540",
                f"s3://{S3_BUCKET}/{S3_SCRIPT_KEY}"
            ],
        },
    }
]

# Create the DAG
with DAG(
    'taxi_data_processing',
    default_args=default_args,
    description='Process taxi data using EMR',
    schedule_interval='@daily',
    start_date=datetime(2025, 4, 5),
    catchup=False
) as dag:

    # Task to upload the PySpark script to S3
    upload_script = LocalFilesystemToS3Operator(
        task_id='upload_script_to_s3',
        filename=LOCAL_SCRIPT_PATH,
        dest_bucket=S3_BUCKET,
        dest_key=S3_SCRIPT_KEY,
        replace=True
    )

    # Task to create EMR cluster
    create_emr_cluster = EmrCreateJobFlowOperator(
        task_id='create_emr_cluster',
        job_flow_overrides=JOB_FLOW_OVERRIDES,
        aws_conn_id='aws_default'
    )

    # Task to add Spark step to EMR cluster
    add_step = EmrAddStepsOperator(
        task_id='add_step',
        job_flow_id="{{ task_instance.xcom_pull(task_ids='create_emr_cluster', key='return_value') }}",
        steps=SPARK_STEP,
        aws_conn_id='aws_default'
    )

    # Task to monitor the Spark step
    watch_step = EmrStepSensor(
        task_id='watch_step',
        job_flow_id="{{ task_instance.xcom_pull(task_ids='create_emr_cluster', key='return_value') }}",
        step_id="{{ task_instance.xcom_pull(task_ids='add_step', key='return_value')[0] }}",
        aws_conn_id='aws_default'
    )

    # Task to terminate the EMR cluster
    terminate_emr_cluster = EmrTerminateJobFlowOperator(
        task_id='terminate_emr_cluster',
        job_flow_id="{{ task_instance.xcom_pull(task_ids='create_emr_cluster', key='return_value') }}",
        aws_conn_id='aws_default'
    )

    # Set up the task dependencies
    upload_script >> create_emr_cluster >> add_step >> watch_step >> terminate_emr_cluster