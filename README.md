# Agentic Document Assistant

Workflow:

```text
User Question
  -> LangGraph Agent
  -> Planner
  -> Salary / Bank / Offer Letter Tool
  -> FAISS Search
  -> Gemini 2.5 Flash
  -> Final Answer
```

## Stack

- FastAPI for the backend API
- Streamlit for the UI
- LangGraph for agent orchestration
- Gemini 2.5 Flash for final answer generation
- FAISS for vector search
- BAAI/bge-small-en-v1.5 embeddings
- PyMuPDF for PDF extraction
- SQLite for chunk metadata

## Folder Structure

```text
agentic-doc-assistant/
├── app.py
├── main.py
├── agents/
├── tools/
├── documents/
│   ├── salary/
│   ├── bank/
│   └── offer/
├── vectorstore/
│   └── faiss_index/
├── embeddings/
├── llm/
├── data/
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Gemini API key:

```bash
$env:GEMINI_API_KEY="your-api-key"
```

Add PDFs to:

- `documents/salary`
- `documents/bank`
- `documents/offer`

## Run

Start the API:

```bash
uvicorn main:app --reload
```

Start the UI in another terminal:

```bash
streamlit run app.py
```

Open the Streamlit app, click **Rebuild FAISS index**, then ask questions.
