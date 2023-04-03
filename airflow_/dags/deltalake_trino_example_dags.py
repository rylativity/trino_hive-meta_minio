from airflow import Dataset
from airflow.decorators import task, dag
from airflow.providers.trino.operators.trino import TrinoOperator
from datetime import datetime

from deltalake.writer import write_deltalake
import pandas as pd


#### NOTE!!!!!
## The following DAGs use the Airflow Connection to Trino that is defined as an environment variable in the docker-compose-airflow.yml as AIRFLOW_CONN_TRINO_DEFAULT.
## The TrinoOperator looks for and uses the connection called `trino_default`

s3_options = {
    "ACCESS_KEY_ID":"airflowaccesskey",
    "SECRET_ACCESS_KEY":"airflowsupersecretkey",
    "ENDPOINT":"http://minio:9000",
    "REGION":"us-east",
    "AWS_STORAGE_ALLOW_HTTP": "true",
    "AWS_S3_ALLOW_UNSAFE_RENAME":"true"
}

TRINO_DB = "delta"
TRINO_SCHEMA = "my_schema"
TRINO_TABLE = "appl_stock_delta_table"
MINIO_BUCKET = "s3a://test/"

example_dataset = Dataset(f"{MINIO_BUCKET}{TRINO_TABLE}")

@dag(
    dag_id="create_and_register_delta_table",
    schedule="@once",  # Override to match your needs
    start_date=datetime(2022, 1, 1),
    catchup=False,
    tags=["example"]
)
def create_deltalake_table():

    ## Create a Delta Lake Table from CSV Using The Delta-RS Library
    @task()
    def deltalake_create_table():
        df = pd.read_csv("/data/appl_stock.csv")
        write_deltalake(f"{MINIO_BUCKET}{TRINO_TABLE}",data=df, storage_options=s3_options, mode="overwrite")


    ## Create the Trino Schema to Hold our Delta Tables (Using Minio/S3 as the storage location)
    trino_create_schema = TrinoOperator(
        task_id="trino_create_schema",
        sql=f"CREATE SCHEMA IF NOT EXISTS {TRINO_DB}.{TRINO_SCHEMA} WITH (location='{MINIO_BUCKET}')",
        handler=list
    )

    ## Register the Delta Lake Table Created In The First Task to the Schema Created in the Second Task
    trino_register_delta_table = TrinoOperator(
        task_id="trino_register_delta_table",
        sql=f"""
        CALL {TRINO_DB}.system.register_table(schema_name => '{TRINO_SCHEMA}', table_name => '{TRINO_TABLE}', table_location => '{MINIO_BUCKET}{TRINO_TABLE}')
        """,
        handler=list,
        outlets=[example_dataset]
    )

    deltalake_create_table() >> trino_create_schema >> trino_register_delta_table

@dag(
    dag_id="trino_create_delta_table",
    schedule=[example_dataset],  # Override to match your needs
    start_date=datetime(2022, 1, 1),
    catchup=False,
    tags=["example"],
)
def create_table_trino():

    ## This task will fail unless you create the source delta.my_schema.appl_stock_delta_table. 
    # You can create this table by going to http://localhost:8888 and running the `pyspark_delta_example.ipynb` notebook
    trino_create_table = TrinoOperator(
        task_id="trino_create_table",
        sql=f"""CREATE TABLE IF NOT EXISTS {TRINO_DB}.{TRINO_SCHEMA}.{TRINO_TABLE}_VERSION_2 AS(
        SELECT * FROM {TRINO_DB}.{TRINO_SCHEMA}.{TRINO_TABLE}
        )""",
        handler=list
    )


create_deltalake_table()
create_table_trino()
    