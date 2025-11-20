# LLMOps Reference — RAG with Airflow, ElasticSearch and Streamlit

Reference architecture for operationalizing a Retrieval-Augmented Generation (RAG) pipeline focused on legal documents. The solution integrates Airflow, ElasticSearch, Streamlit, Grafana and PostgreSQL in a fully containerized environment via Docker Compose.

## Overview
- Airflow schedules data preparation in PostgreSQL and rebuilds the ElasticSearch index.
- Streamlit delivers the interface for English queries, consulting Hugging Face with context retrieved from ElasticSearch.
- Operational metrics and user feedback are persisted in PostgreSQL and visualized in Grafana.
- The entire stack is provisioned with `docker-compose`, facilitating replication and local testing.

```
+------------+        +-------------+        +---------------+        +------------------+
|  Airflow   | -----> | PostgreSQL  | -----> | ElasticSearch | -----> | Streamlit (LLM)  |
+------------+        +-------------+        +---------------+        +------------------+
        |                          ^                      |                        |
        |                          |                      |                        |
        +--------------------------+----------------------+------------------------+
                                   |                      v                        v
                                 Grafana            Metrics/Feedback         Hugging Face
```

## Prerequisites
- Docker Desktop (or Docker Engine) and Docker Compose.
- [Hugging Face](https://huggingface.co/) account with valid token.
- Ports 8080, 8501, 3000, 5432 and 9200/9300 available on local machine.

## Quick Setup
1. Generate a token in **Hugging Face → Settings → Access Tokens**.
2. Update `docker-compose.yaml`, inserting the token in the `HUGGINGFACE_KEY` field of the `app` service.
3. Adjust the ElasticSearch hostname in Python modules, if the container name is different from `elasticsearch`:
   - `airflow_module/dags/data_module/data_loader.py`
   - `streamlit_module/streamlit/app/elasticsearch_client.py`
4. Start all services:
   ```bash
   docker-compose -p ragstack up --build -d
   ```
5. Wait for the first DAG execution to populate the database and index.

To stop services:
```bash
docker-compose -p ragstack down
```

## Available Services
- Airflow UI: `http://localhost:8080` — user `airflow`, password `airflow`.
- Streamlit App: `http://localhost:8501`.
- Grafana: `http://localhost:3000` — user `admin`, password `admin`.
- ElasticSearch API: `http://localhost:9200`.

## Data Pipeline (Airflow)
The DAG `rag_data_ingestion` (`airflow_module/dags/rag_pipeline.py`) runs daily and performs:
1. Creation/cleanup of the `documents` table in PostgreSQL (`create_documents_table`).
2. Ingestion of the first 25 records from JSONL dataset (`load_documents_from_json`).
3. Ingestion of the first 25 records from CSV dataset (`load_documents_from_csv`).
4. Reconstruction of the `rag_documents` index in ElasticSearch (`build_elasticsearch_index`).

ETL utilities reside in `airflow_module/dags/data_module/`.

## Streamlit Application
- Main script: `streamlit_module/streamlit/app_main.py`.
- Searches context in ElasticSearch through `app/elasticsearch_client.py` and sends payloads to Hugging Face (`app/llm_client.py`).
- Persists performance metrics (`llm_evaluations`) and explicit feedback (`user_feedback`) in PostgreSQL.

## Observability with Grafana
- Dashboard: `grafana_dashboard/dashboard.json`.
- After starting Grafana, import the JSON and configure a PostgreSQL source pointing to the `postgres` container (`host: postgres`, `user: airflow`, `password: airflow`, `database: airflow`).
- Explore response time metrics, RAG accuracy and user satisfaction.

## Project Structure
```
.
├── airflow_module
│   ├── dags
│   │   ├── data_module
│   │   ├── data
│   │   └── rag_pipeline.py
│   ├── Dockerfile
│   └── requirements.txt
├── streamlit_module
│   ├── Dockerfile
│   └── streamlit
│       ├── app
│       └── app_main.py
├── grafana_dashboard
│   └── dashboard.json
├── docker-compose.yaml
├── LEIAME.txt
└── README.md
```

## Useful Commands
- Airflow webserver logs:
  ```bash
  docker-compose logs -f airflow-webserver
  ```
- Manual DAG trigger via Airflow UI (`Graph View → Trigger DAG`).
- Streamlit application dependency updates:
  ```bash
  docker-compose exec app pip install -r requirements.txt
  ```

## Troubleshooting
- **401 from Hugging Face API**: validate token and remove extra spaces.
- **ElasticSearch unavailable**: check configured hostname and use `docker-compose ps` to inspect containers.
- **Port conflicts**: customize mappings in `docker-compose.yaml` before starting the stack.
- **DAG doesn't start automatically**: enable it in Airflow interface (*On* button) or trigger manually.

## Additional Resources
- [Apache Airflow](https://airflow.apache.org/)
- [ElasticSearch](https://www.elastic.co/guide/index.html)
- [Streamlit](https://docs.streamlit.io/)
- [Hugging Face Inference API](https://huggingface.co/docs/api-inference/index)

---
Architecture provided for experimentation, metrics evaluation and prototyping of corporate RAG workflows.