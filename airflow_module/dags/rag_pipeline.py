"""Airflow DAG responsável por preparar a base de conhecimento utilizada pelo fluxo RAG."""

from datetime import timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

from data_module.data_loader import (
    build_elasticsearch_index,
    create_documents_table,
    load_documents_from_csv,
    load_documents_from_json,
)


default_args = {
    "owner": "Analytics Platform",
    "start_date": days_ago(1),
    "retries": 1,
    "retry_delay": timedelta(hours=1),
}

with DAG(
    dag_id="rag_data_ingestion",
    default_args=default_args,
    schedule_interval="0 0 * * *",
    description="Carrega os dados de suporte para o pipeline RAG",
) as dag:
    task_create_table = PythonOperator(
        task_id="create_documents_table",
        python_callable=create_documents_table,
    )

    task_load_json = PythonOperator(
        task_id="load_documents_from_json",
        python_callable=load_documents_from_json,
        op_kwargs={"data_path": "/opt/airflow/dags/data/dataset1.jsonl"},
    )

    task_load_csv = PythonOperator(
        task_id="load_documents_from_csv",
        python_callable=load_documents_from_csv,
        op_kwargs={"data_path": "/opt/airflow/dags/data/dataset2.csv"},
    )

    task_build_index = PythonOperator(
        task_id="build_elasticsearch_index",
        python_callable=build_elasticsearch_index,
    )

    task_create_table >> task_load_json >> task_load_csv >> task_build_index
