"""Abstrações de acesso ao ElasticSearch utilizadas pelo frontend."""

import os

from elasticsearch import Elasticsearch

ES_HOST = os.getenv('ELASTICSEARCH_HOST', 'http://elasticsearch:9200')
ES_INDEX_NAME = "rag_documents"


def get_es_client() -> Elasticsearch:
    """Retorna uma instância conectada do cliente ElasticSearch."""
    return Elasticsearch(ES_HOST)


def search_documents(es_client: Elasticsearch, query: str, index_name: str = ES_INDEX_NAME):
    """Executa uma consulta textual limitada a cinco resultados e retorna o payload bruto."""
    search_query = {
        "size": 5,
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["question^2", "text"],
                        "type": "best_fields",
                    }
                }
            }
        },
    }

    response = es_client.search(index=index_name, body=search_query)
    return [hit["_source"] for hit in response["hits"]["hits"]]
