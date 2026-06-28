from llm.gemini import generate_answer
from tools.search_tool import search_documents


def answer_salary_question(question: str) -> dict:
    matches = search_documents(question, document_type="salary")
    answer = generate_answer(question=question, context_chunks=matches, document_type="salary")
    return {"answer": answer, "sources": matches}
