from airflow import DAG
from airflow.providers.amazon.aws.operators.emr import EmrCreateJobFlowOperator, EmrTerminateJobFlowOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

SPARK_STEPS = [
    {
        'Name': 'RunTaxiDataProcessing',
        'ActionOnFailure': 'TERMINATE_CLUSTER',
        'HadoopJarStep': {
            'Jar': 'command-runner.jar',
            'Args': [
                'spark-submit',
                '--deploy-mode', 'cluster',
                '--packages', 'org.postgresql:postgresql:42.7.3',
                's3://taxi-raw-grupo-5/scripts/process_taxi_data.py'
            ]
        }
    }
]

JOB_FLOW_OVERRIDES = {
    'Name': 'TaxiDataProcessing',
    'ReleaseLabel': 'emr-6.15.0',
    'Applications': [{'Name': 'Spark'}],
    'Instances': {
        'InstanceGroups': [
            {
                'Name': 'Master',
                'Market': 'ON_DEMAND',
                'InstanceRole': 'MASTER',
                'InstanceType': 'm5.xlarge',
                'InstanceCount': 1,
            },
            {
                'Name': 'Workers',
                'Market': 'ON_DEMAND',
                'InstanceRole': 'CORE',
                'InstanceType': 'm5.xlarge',
                'InstanceCount': 2,
            }
        ],
        'KeepJobFlowAliveWhenNoSteps': False,
        'TerminationProtected': False,
    },
    'Steps': SPARK_STEPS,
    'JobFlowRole': 'EMR_EC2_DefaultRole',
    'ServiceRole': 'EMR_DefaultRole', 
    'LogUri': 's3://taxi-raw-grupo-5/',
}

with DAG(
    'emr_taxi_processing',
    default_args=default_args,
    schedule_interval=None,
) as dag:
    create_cluster = EmrCreateJobFlowOperator(
        task_id='create_cluster',
        job_flow_overrides=JOB_FLOW_OVERRIDES,
        aws_conn_id='aws_default',
        region_name='us-east-1'
    )

    terminate_cluster = EmrTerminateJobFlowOperator(
        task_id='terminate_cluster',
        job_flow_id="{{ task_instance.xcom_pull(task_ids='create_cluster', key='return_value') }}",
        aws_conn_id='aws_default'
    )

    create_cluster >> terminate_cluster