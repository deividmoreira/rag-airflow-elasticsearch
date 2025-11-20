"""Interface Streamlit para interação com o assistente RAG."""

import streamlit as st

from app.elasticsearch_client import ES_INDEX_NAME, get_es_client, search_documents
from app.evaluation import evaluate
from app.llm_client import (
    generate_document_id,
    query_llm,
    store_user_feedback,
    store_user_input,
)


def main() -> None:
    st.set_page_config(page_title="RAG Assistant", page_icon=":robot:", layout="wide")

    st.sidebar.title("RAG Assistant")
    st.sidebar.write("Consultas jurídicas com recuperação aumentada por contexto.")
    st.sidebar.markdown("---")

    st.title("Assistente Jurídico com RAG")
    st.write("Envie perguntas em inglês para explorar decisões e precedentes jurídicos indexados.")

    if "result" not in st.session_state:
        st.session_state.result = None
    if "docId" not in st.session_state:
        st.session_state.docId = None
    if "userInput" not in st.session_state:
        st.session_state.userInput = ""
    if "feedbackSubmitted" not in st.session_state:
        st.session_state.feedbackSubmitted = False

    user_input = st.text_input("Digite sua pergunta:")

    try:
        es_client = get_es_client()
    except Exception as exc:
        st.error("ElasticSearch indisponível. Atualize a página quando o serviço estiver ativo.")
        st.stop()

    if st.button("Enviar"):
        if not user_input:
            st.warning("Informe uma pergunta antes de continuar.")
        else:
            with st.spinner("Preparando resposta..."):
                try:
                    search_results = search_documents(es_client, user_input, ES_INDEX_NAME)
                    context = "".join(result["answer"] for result in search_results)

                    evaluation = evaluate(
                        lambda record: search_documents(es_client, record["question"], ES_INDEX_NAME)
                    )

                    payload = {
                        "inputs": {
                            "question": user_input.replace("'", ""),
                            "context": context,
                        }
                    }

                    model_output, response_time = query_llm(payload)
                    result_text = model_output["answer"].replace("'", "")

                    doc_id = generate_document_id(user_input, result_text)
                    store_user_input(
                        doc_id,
                        user_input.replace("'", ""),
                        result_text,
                        model_output["score"],
                        response_time,
                        evaluation["hit_rate"],
                        evaluation["mrr"],
                    )

                    st.session_state.result = result_text
                    st.session_state.docId = doc_id
                    st.session_state.userInput = user_input.replace("'", "")
                    st.session_state.feedbackSubmitted = False
                except Exception as exc:
                    st.error("Não foi possível processar a consulta. Verifique os serviços dependentes e tente novamente.")

    if st.session_state.result:
        st.subheader("Resposta")
        st.write(st.session_state.result)

        if not st.session_state.feedbackSubmitted:
            st.write("A resposta foi útil?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Satisfeito"):
                    store_user_feedback(
                        st.session_state.docId,
                        st.session_state.userInput,
                        st.session_state.result,
                        True,
                    )
                    st.session_state.feedbackSubmitted = True
                    st.success("Feedback registrado.")
            with col_no:
                if st.button("Não satisfeito"):
                    store_user_feedback(
                        st.session_state.docId,
                        st.session_state.userInput,
                        st.session_state.result,
                        False,
                    )
                    st.session_state.feedbackSubmitted = True
                    st.warning("Feedback registrado.")


if __name__ == "__main__":
    main()
