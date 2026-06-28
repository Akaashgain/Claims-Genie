from llm.gemini import generate_answer
from tools.bank_tool import answer_bank_question
from tools.offer_letter_tool import answer_offer_question
from tools.salary_tool import answer_salary_question
from tools.search_tool import search_documents


def answer_document_question(question: str, document_type: str) -> dict:
    if document_type == "salary":
        return answer_salary_question(question)
    if document_type == "bank":
        return answer_bank_question(question)
    if document_type == "offer":
        return answer_offer_question(question)

    matches = search_documents(question, document_type="all")
    answer = generate_answer(question=question, context_chunks=matches, document_type="all")
    return {"answer": answer, "sources": matches}
