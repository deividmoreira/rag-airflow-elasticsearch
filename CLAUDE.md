# CLAUDE.md

Orientações para colaboração com o código deste repositório.

## Overview

This project demonstrates a LLMOps architecture focused on RAG (Retrieval-Augmented Generation) for legal documents, combining Apache Airflow, ElasticSearch, Streamlit and Grafana in a Docker Compose environment.

## Arquitetura

Quatro módulos principais compõem a solução:

1. **airflow_module/** – Orquestra o pipeline de ingestão
   - DAG `rag_data_ingestion` with table creation, JSON/CSV dataset loading and ElasticSearch indexing steps
   - Utilities in `dags/data_module/` for PostgreSQL connection, data preparation and index recreation

2. **streamlit_module/** – Aplicação Streamlit de front-end
   - Script principal `streamlit/app_main.py`
   - Componentes em `streamlit/app/`: cliente ElasticSearch, integração com Hugging Face, avaliação e conexão ao banco
   - Interface em inglês para consultas sobre o corpus jurídico indexado

3. **elasticsearch** – Repositório de documentos (porta 9200)
   - Ambiente single-node, sem autenticação para desenvolvimento
   - Índice padrão `rag_documents`

4. **grafana** – Dashboard de monitoramento (porta 3000)
   - Conecta no PostgreSQL para exibir métricas de desempenho e feedback

## Comandos Úteis

```bash
# Inicialização (requer token da Hugging Face em docker-compose.yaml)
docker-compose -p ragstack up --build -d

# Shutdown
docker-compose -p ragstack down

# Logs
docker-compose -p ragstack logs [service]
```

## Fluxo de Trabalho

1. Configure o token da Hugging Face em `docker-compose.yaml`
2. Suba os serviços com `docker-compose -p ragstack up --build -d`
3. Ative a DAG `rag_data_ingestion` na interface do Airflow
4. Aguarde a conclusão da ingestão antes de testar a aplicação Streamlit
5. Utilize perguntas em inglês para validar o comportamento

## Arquivos Importantes

- `docker-compose.yaml`
- `airflow_module/config/airflow.cfg`
- `airflow_module/dags/rag_pipeline.py`
- `streamlit_module/streamlit/app_main.py`

## Dependências Principais

- Airflow module: `orjsonl`, `pandas`
- Streamlit app: `streamlit`, `elasticsearch`, `psycopg2`, `requests`

## Pipeline de Dados

1. `create_documents_table()` – provisiona a tabela `documents`
2. `load_documents_from_json()` – injeta dados do dataset JSONL
3. `load_documents_from_csv()` – injeta dados do dataset CSV
4. `build_elasticsearch_index()` – recria o índice `rag_documents`

## Observações

- O corpus e os exemplos estão em inglês
- Métricas de qualidade (hit rate, MRR) e feedback explícito são armazenados no PostgreSQL
- A aplicação depende da conclusão da indexação no ElasticSearch
- É necessário um token válido da Hugging Face para inferência
