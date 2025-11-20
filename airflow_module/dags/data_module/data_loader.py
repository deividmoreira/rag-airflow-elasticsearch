"""Rotinas de carga de dados utilizadas pela DAG de preparação do RAG."""

import hashlib
import os
from typing import Dict, Iterable, List, Tuple

import orjsonl
import pandas as pd
from elasticsearch import Elasticsearch

from data_module.data_fetch import fetch_documents
from data_module.db_connection import get_postgres_connection

DOCUMENT_TABLE = "documents"
ES_INDEX_NAME = "rag_documents"
ES_HOST = os.getenv('ELASTICSEARCH_HOST', 'http://elasticsearch:9200')


def generate_document_id(document: Dict[str, str]) -> str:
    """Gera um identificador estável a partir do conteúdo do documento."""
    combined = f"{document['text'][:10]}-{document['question']}"
    return hashlib.md5(combined.encode()).hexdigest()[:8]


def create_documents_table() -> None:
    """Cria (ou limpa) a tabela de documentos no PostgreSQL."""
    conn, cur = get_postgres_connection()

    try:
        create_stmt = f"""
            CREATE TABLE {DOCUMENT_TABLE} (
                id SERIAL PRIMARY KEY,
                doc_id VARCHAR(10),
                question TEXT NOT NULL,
                answer TEXT NOT NULL
            );
        """
        cur.execute(create_stmt)
    except Exception:
        truncate_stmt = f"TRUNCATE TABLE {DOCUMENT_TABLE};"
        cur.execute(truncate_stmt)

    conn.commit()
    cur.close()
    conn.close()


def _bulk_insert(records: Iterable[Tuple[str, str, str]]) -> None:
    conn, cur = get_postgres_connection()
    try:
        values = ",".join(cur.mogrify("(%s,%s,%s)", record).decode("utf-8") for record in records)
        insert_stmt = f"INSERT INTO {DOCUMENT_TABLE} (doc_id, question, answer) VALUES" + values
        cur.execute(insert_stmt)
        conn.commit()
    except Exception as exc:
        print(f"Error while inserting data: {exc}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def load_documents_from_json(data_path: str = None, limit: int = 25) -> str:
    """Carrega documentos a partir do dataset JSONL."""
    if data_path:
        dataset_path = data_path
    else:
        dataset_path = os.path.join(os.getcwd(), "dags", "data", "dataset1.jsonl")
    raw_records: List[Dict[str, str]] = orjsonl.load(dataset_path)

    prepared_records = []
    for entry in raw_records[:limit]:
        document = {
            "question": str(entry["question"]),
            "text": str(entry["answer"]),
        }
        doc_id = generate_document_id(document)
        prepared_records.append((doc_id, document["question"], document["text"]))

    _bulk_insert(prepared_records)
    return "JSON documents ingested successfully."


def load_documents_from_csv(data_path: str = None, limit: int = 25) -> str:
    """Carrega documentos a partir do dataset CSV."""
    if data_path:
        dataset_path = data_path
    else:
        dataset_path = os.path.join(os.getcwd(), "dags", "data", "dataset2.csv")
    dataframe = pd.read_csv(dataset_path)

    prepared_records = []
    for _, row in dataframe.head(limit).iterrows():
        document = {
            "question": str(row["case_title"]),
            "text": str(row["case_text"]),
        }
        doc_id = generate_document_id(document)
        prepared_records.append((doc_id, document["question"], document["text"]))

    _bulk_insert(prepared_records)
    return "CSV documents ingested successfully."


def build_elasticsearch_index() -> str:
    """Recria o índice no ElasticSearch com os documentos armazenados no PostgreSQL."""
    es_client = Elasticsearch(ES_HOST)

    index_settings = {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "question": {"type": "text"},
                "text": {"type": "text"},
            }
        },
    }

    try:
        es_client.indices.create(index=ES_INDEX_NAME, body=index_settings)
    except Exception:
        pass

    if es_client.indices.exists(index=ES_INDEX_NAME):
        es_client.indices.delete(index=ES_INDEX_NAME)
        es_client.indices.create(index=ES_INDEX_NAME, body=index_settings)

    for document in fetch_documents():
        try:
            es_client.index(index=ES_INDEX_NAME, document=document)
        except Exception as exc:
            print(f"Error while indexing document: {exc}\nDocument: {document}")

    return "ElasticSearch index rebuilt successfully."
