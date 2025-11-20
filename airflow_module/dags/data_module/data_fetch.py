"""Funções utilitárias para leitura de dados no PostgreSQL."""

from typing import List

from data_module.db_connection import get_postgres_connection

DOCUMENT_TABLE = "documents"


def fetch_documents() -> List[dict]:
    """Retorna todos os documentos persistidos na base relacional."""
    conn, cur = get_postgres_connection()
    cur.execute(f"SELECT doc_id, question, answer FROM {DOCUMENT_TABLE}")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results
