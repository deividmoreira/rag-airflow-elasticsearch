"""Integrações com a API de inferência da Hugging Face e persistência de telemetria."""

import hashlib
import os
import time
from typing import Dict, Tuple

import requests

from app.db_connection import get_postgres_connection

EVALUATION_TABLE = "llm_evaluations"
FEEDBACK_TABLE = "user_feedback"


def generate_document_id(user_query: str, answer: str) -> str:
    """Cria um identificador determinístico a partir das strings informadas."""
    combined = f"{user_query[:10]}-{answer[:10]}"
    return hashlib.md5(combined.encode()).hexdigest()[:8]


def query_llm(payload: Dict) -> Tuple[Dict, float]:
    """Submete o payload à Inference API e retorna a resposta junto com o tempo decorrido."""
    api_url = "https://api-inference.huggingface.co/models/google-bert/bert-large-uncased-whole-word-masking-finetuned-squad"
    headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_KEY')}"}

    start_time = time.time()
    response = requests.post(api_url, headers=headers, json=payload)
    elapsed = round(time.time() - start_time, 2)
    return response.json(), elapsed


def _ensure_table(cursor, table_statement: str) -> None:
    try:
        cursor.execute(table_statement)
    except Exception:
        cursor.connection.rollback()
    else:
        cursor.connection.commit()


def store_user_input(
    doc_id: str,
    user_query: str,
    result: str,
    llm_score: float,
    response_time: float,
    hit_rate: float,
    mrr: float,
) -> str:
    """Garante a existência da tabela de avaliações e insere o registro informado."""
    conn, cur = get_postgres_connection()
    try:
        _ensure_table(
            cur,
            f"""
                CREATE TABLE {EVALUATION_TABLE} (
                    id SERIAL PRIMARY KEY,
                    doc_id VARCHAR(10) NOT NULL,
                    user_input TEXT NOT NULL,
                    result TEXT NOT NULL,
                    llm_score DOUBLE PRECISION NOT NULL,
                    response_time DOUBLE PRECISION NOT NULL,
                    hit_rate_score DOUBLE PRECISION NOT NULL,
                    mrr_score DOUBLE PRECISION NOT NULL,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """,
        )

        insert_stmt = f"""
            INSERT INTO {EVALUATION_TABLE}
            (doc_id, user_input, result, llm_score, response_time, hit_rate_score, mrr_score)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(
            insert_stmt,
            (doc_id, user_query, result, llm_score, response_time, hit_rate, mrr),
        )
        conn.commit()
    except Exception as exc:
        print(exc)
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    return "User input stored."


def store_user_feedback(doc_id: str, user_query: str, result: str, feedback: bool) -> str:
    """Persiste o feedback explícito fornecido pelo usuário."""
    conn, cur = get_postgres_connection()
    try:
        _ensure_table(
            cur,
            f"""
                CREATE TABLE {FEEDBACK_TABLE} (
                    id SERIAL PRIMARY KEY,
                    doc_id VARCHAR(10) NOT NULL,
                    user_input TEXT NOT NULL,
                    result TEXT NOT NULL,
                    is_satisfied BOOLEAN NOT NULL,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """,
        )

        insert_stmt = f"""
            INSERT INTO {FEEDBACK_TABLE}
            (doc_id, user_input, result, is_satisfied)
            VALUES
            (%s, %s, %s, %s)
        """
        cur.execute(insert_stmt, (doc_id, user_query, result, feedback))
        conn.commit()
    except Exception as exc:
        print(exc)
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    return "User feedback stored."
