"""Conexão PostgreSQL compartilhada pela aplicação Streamlit."""

import psycopg2
from psycopg2.extras import RealDictCursor


def get_postgres_connection():
    """Retorna conexão e cursor PostgreSQL para uso transacional."""
    conn = psycopg2.connect(
        dbname="airflow",
        user="airflow",
        password="airflow",
        host="postgres",
        port="5432",
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    return conn, cursor
