from llm.gemini import generate_answer
from tools.search_tool import search_documents


def answer_bank_question(question: str) -> dict:
    matches = search_documents(question, document_type="bank")
    answer = generate_answer(question=question, context_chunks=matches, document_type="bank")
    return {"answer": answer, "sources": matches}
