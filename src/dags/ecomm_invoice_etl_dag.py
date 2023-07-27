from airflow import DAG
# from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from datetime import datetime
from airflow.utils import timezone
from datetime import timedelta
import requests
from kaggle.api.kaggle_api_extended import KaggleApi
import os
import tempfile
import shutil
from google.cloud import storage
import logging

from transform_load import clean_data_google, load_data_google, clear_staging_area
from alternative_cloud_etl import extract_api_aws, extract_url_aws, extract_database_aws, clean_aws

# get variables from .env file
project_id = os.environ["PROJECT_ID"]
gcp_bucket = os.environ["BUCKET_NAME"]
dataset_name = os.environ["DATASET_NAME"]
table_name = os.environ["TABLE_NAME"]
credentials_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
load_target_file = "ecomm_invoice_transaction.parquet"

aws_credentials_path = os.environ["AWS_CREDENTIALS_PATH"]
aws_bucket = os.environ["AWS_BUCKET"]


def extract_url_google():
    # retrieve data from url
    url = "https://raw.githubusercontent.com/Patcharanat/ecommerce-invoice/master/data/cleaned_data.csv"
    response = requests.get(url)
    data_url = response.text

    # specify desired file name and credentials path
    destination_blob_name = "data_url_uncleaned.csv"

    # write data to csv file created in GCS
    storage_client = storage.Client.from_service_account_json(credentials_path)
    bucket = storage_client.bucket(gcp_bucket)
    blob = bucket.blob(destination_blob_name)

    with blob.open("w") as file:
        file.write(data_url)
    file.close()
    logging.info(f"File {destination_blob_name} is stored.")


def extract_database_google():
    # initiate connection
    postgres_hook = PostgresHook(
        postgres_conn_id="postgres-source",
        schema="mydatabase"
    )
    conn = postgres_hook.get_conn()
    cursor = conn.cursor()

    # Define the SQL query to extract data
    query = "SELECT * FROM myschema.ecomm_invoice"

    # Define the COPY command with the query, CSV format, and headers
    copy_command = f"COPY ({query}) TO STDOUT WITH CSV HEADER"

    # specify desired file name and credentials path
    destination_blob_name = "data_postgres_cleaned.csv"

    # upload to GCS
    storage_client = storage.Client.from_service_account_json(credentials_path)
    bucket = storage_client.bucket(gcp_bucket)
    blob = bucket.blob(destination_blob_name)

    # Open the file in write mode
    with blob.open('w') as file:
        # Execute the COPY command and write the results to the file
        cursor.copy_expert(copy_command, file)
    
    # close cursor and connection
    cursor.close()
    conn.close()

    logging.info(f"Completed extracting data from postgres database loaded to {destination_blob_name}")


def extract_api_google():
    # authenticate and download data from Kaggle API
    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files('carrie1/ecommerce-data', path='./data/')

    # Extract the ZIP file to the temporary directory
    temp_dir = tempfile.mkdtemp()  # Create a temporary directory
    zip_path = './data/ecommerce-data.zip' # destination path
    shutil.unpack_archive(zip_path, temp_dir, format='zip')
    extracted_file_path = os.path.join(temp_dir, 'data.csv')

    # upload to GCS
    destination_blob_name = "data_api_uncleaned.csv"

    storage_client = storage.Client.from_service_account_json(credentials_path)
    bucket = storage_client.bucket(gcp_bucket)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(extracted_file_path)

    # remove created csv file from local
    # In order to not remove before aws load to s3
    # os.remove(zip_path)
    logging.info(f"Completed extracting data from API loaded to {destination_blob_name}")


default_args = {
    "owner": "Ken",
    # "email": ["XXXXX"],
    "start_date": timezone.datetime(2023, 6, 26),
    "retries": 3,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    'ecomm_invoice_etl_dag',
    start_date=datetime(2023, 5, 30), 
    schedule_interval=None # or '@daily'
    ) as dag:
    
    extract_data_url_google = PythonOperator(
        task_id='extract_data_url_google',
        python_callable=extract_url_google
    )

    extract_data_database_google = PythonOperator(
        task_id='extract_data_database_google',
        python_callable=extract_database_google
    )

    extract_data_api_google = PythonOperator(
        task_id='extract_data_api_google',
        python_callable=extract_api_google
    )

    transform_data_google = PythonOperator(
        task_id="transform_data_google",
        python_callable=clean_data_google,
        op_kwargs={
            "source_file": "data_api_uncleaned.csv",
            "destination_file": load_target_file,
            "project_id": project_id,
            "gcp_bucket": gcp_bucket,
            "credentials_path": credentials_path
        }
    )

    load_to_bigquery = PythonOperator(
        task_id="load_to_bigquery",
        python_callable=load_data_google,
        op_kwargs={
            "project_id": project_id,
            "gcp_bucket": gcp_bucket,
            "dataset_name": dataset_name,
            "table_name": table_name,
            "credentials_path": credentials_path
        }
    )

    load_to_bigquery_external = BigQueryCreateExternalTableOperator(
        task_id="load_to_bigquery_external",
        table_resource={
            "tableReference": {
                "projectId": project_id,
                "datasetId": dataset_name,
                "tableId": f"{table_name}_external",
            },
            "externalDataConfiguration": {
                "sourceFormat": "PARQUET",
                "sourceUris": [f"gs://{gcp_bucket}/staging_area/{load_target_file}"],
            },
        },
        gcp_conn_id="my_gcp_conn_id",
    )

    # clear_staging_area_gcs = PythonOperator(
    #     task_id="clear_staging_area_gcs",
    #     python_callable=clear_staging_area,
    #     op_kwargs={
    #         "gcp_bucket": gcp_bucket,
    #         "blob_name": f"staging_area/{load_target_file}",
    #         "credentials_path": credentials_path
    #     }
    # )

    extract_data_url_aws = PythonOperator(
        task_id="extract_data_url_aws",
        python_callable=extract_url_aws
    )

    extract_data_database_aws = PythonOperator(
        task_id="extract_data_database_aws",
        python_callable=extract_database_aws
    )

    extract_data_api_aws = PythonOperator(
        task_id="extract_data_api_aws",
        python_callable=extract_api_aws
    )

    transform_data_aws = PythonOperator(
        task_id="transform_data_aws",
        python_callable=clean_aws,
        op_kwargs={
            "gcp_bucket": aws_bucket,
            "object_name": "data_api_uncleaned.csv",
            "destination_file": load_target_file,
        }
    )

    load_to_redshift = PythonOperator()

    # Only applicable with CSV files
    # s3_to_redshift = S3ToRedshiftOperator(
    #     task_id='s3_to_redshift',
    #     schema='public',
    #     table='ecomm_invoice_transaction',
    #     s3_bucket=aws_bucket,
    #     s3_key='staging_area/ecomm_invoice_transaction.parquet',
    #     redshift_conn_id='redshift_default',
    #     aws_conn_id='aws_default',
    #     copy_options=[
    #         "DELIMITER AS ','"
    #     ],
    #     method='REPLACE'
    # )

    load_to_redshift_external = PythonOperator()

    # clear_staging_area_s3 = PythonOperator()

    # define task dependencies

    [extract_data_url_google, extract_data_database_google, extract_data_api_google] >> transform_data_google
    transform_data_google >> [load_to_bigquery, load_to_bigquery_external]
    # [load_to_bigquery, load_to_bigquery_external] >> clear_staging_area_gcs

    [extract_data_api_aws, extract_data_database_aws, extract_data_url_aws] >> transform_data_aws
    transform_data_aws >> [load_to_redshift, load_to_redshift_external]
    # transform_data_aws >> load_to_redshift >> clear_staging_area_s3
    