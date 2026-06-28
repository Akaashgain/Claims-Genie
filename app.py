import requests
import streamlit as st


API_URL = "http://localhost:8000"


st.set_page_config(page_title="Agentic Document Assistant", page_icon="A", layout="wide")

st.title("Agentic Document Assistant")

with st.sidebar:
    st.header("Documents")
    st.caption("Put PDFs in documents/salary, documents/bank, or documents/offer.")
    rebuild = st.button("Rebuild FAISS index", use_container_width=True)

    if rebuild:
        with st.spinner("Indexing documents..."):
            try:
                response = requests.post(f"{API_URL}/index", timeout=120)
                response.raise_for_status()
                result = response.json()
                st.success(f"Indexed {result['chunks']} chunks from {result['documents']} files.")
            except requests.RequestException as exc:
                st.error(f"Indexing failed: {exc}")

question = st.text_area(
    "Ask a question",
    placeholder="Example: What salary is shown in my latest salary slip?",
    height=140,
)

ask = st.button("Ask", type="primary", use_container_width=True)

if ask:
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        with st.spinner("Planner is choosing documents and searching..."):
            try:
                response = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question.strip()},
                    timeout=120,
                )
                response.raise_for_status()
                result = response.json()
            except requests.RequestException as exc:
                st.error(f"Request failed: {exc}")
            else:
                st.subheader("Final Answer")
                st.write(result["answer"])

                col1, col2 = st.columns(2)
                col1.metric("Document Type", result["document_type"])
                col2.metric("Sources Used", len(result["sources"]))

                if result["sources"]:
                    st.subheader("Sources")
                    for source in result["sources"]:
                        st.write(
                            f"{source['document_type']} | {source['source']} | "
                            f"page {source.get('page', 'n/a')}"
                        )
