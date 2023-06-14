from datetime import datetime
import logging
import os

from airflow import Dataset
from airflow.decorators import dag
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator


log = logging.getLogger(__name__)

SOURCE_CSV_DATA_PATH = f"s3a://test/transaction_data.csv"

BUCKET = "warehouse"
TABLE_NAME = "transaction_data"
BRONZE_TABLE_PATH = f"s3a://{BUCKET}/bronze/{TABLE_NAME}"
SILVER_TABLE_PATH = f"s3a://{BUCKET}/silver/{TABLE_NAME}"
GOLD_TABLE_PATH = f"s3a://{BUCKET}/gold/{TABLE_NAME}"

@dag(
    schedule=None,
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["bronze"],
)
def load_bronze_table():
    """
    ### TaskFlow API Tutorial Documentation
    This is a simple data pipeline example which demonstrates the use of
    the TaskFlow API using three simple tasks for Extract, Transform, and Load.
    Documentation that goes along with the Airflow TaskFlow API tutorial is
    located
    [here](https://airflow.apache.org/docs/apache-airflow/stable/tutorial_taskflow_api.html)
    """

    packages = 'org.apache.hadoop:hadoop-aws:3.3.2,io.delta:delta-core_2.12:2.1.0'
    
    log.warn(f"Using Packages - {packages}")
    
    spark_load_job = SparkSubmitOperator(
        application="/opt/airflow/dags/pyspark_apps/load_bronze_table_app.py", task_id="load_bronze_table",
        packages=packages,
        # env_vars={},
        application_args=[f"--input-path={SOURCE_CSV_DATA_PATH}", f"--output-path={BRONZE_TABLE_PATH}"],
        inlets=[Dataset(SOURCE_CSV_DATA_PATH)],
        outlets=[Dataset(BRONZE_TABLE_PATH)]
    )
load_bronze_table()

@dag(
    schedule=[Dataset(BRONZE_TABLE_PATH)],
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["silver"],
)
def clean_and_load_silver_table():
    """
    ### TaskFlow API Tutorial Documentation
    This is a simple data pipeline example which demonstrates the use of
    the TaskFlow API using three simple tasks for Extract, Transform, and Load.
    Documentation that goes along with the Airflow TaskFlow API tutorial is
    located
    [here](https://airflow.apache.org/docs/apache-airflow/stable/tutorial_taskflow_api.html)
    """

    packages = 'org.apache.hadoop:hadoop-aws:3.3.2,io.delta:delta-core_2.12:2.1.0'
    
    log.warn(f"Using Packages - {packages}")
    
    spark_load_job = SparkSubmitOperator(
        application="/opt/airflow/dags/pyspark_apps/clean_and_load_silver_table_app.py", task_id="clean_and_load_silver_table",
        packages=packages,
        env_vars={},
        application_args=[f"--input-path={BRONZE_TABLE_PATH}", f"--output-path={SILVER_TABLE_PATH}"],
        outlets=[Dataset(SILVER_TABLE_PATH)]
    )
clean_and_load_silver_table()

@dag(
    schedule=[Dataset(SILVER_TABLE_PATH)],
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["silver"],
)
def process_and_load_gold_table():
    """
    ### TaskFlow API Tutorial Documentation
    This is a simple data pipeline example which demonstrates the use of
    the TaskFlow API using three simple tasks for Extract, Transform, and Load.
    Documentation that goes along with the Airflow TaskFlow API tutorial is
    located
    [here](https://airflow.apache.org/docs/apache-airflow/stable/tutorial_taskflow_api.html)
    """

    packages = 'org.apache.hadoop:hadoop-aws:3.3.2,io.delta:delta-core_2.12:2.1.0'
    
    log.warn(f"Using Packages - {packages}")
    
    spark_load_job = SparkSubmitOperator(
        application="/opt/airflow/dags/pyspark_apps/process_and_load_gold_table_app.py", task_id="process_and_load_gold_table",
        packages=packages,
        # env_vars={},
        application_args=[f"--input-path={SILVER_TABLE_PATH}", f"--output-path={GOLD_TABLE_PATH}"],
        outlets=[Dataset(GOLD_TABLE_PATH)]
    )
process_and_load_gold_table()
