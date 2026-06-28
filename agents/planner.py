from typing import Literal


DocumentType = Literal["salary", "bank", "offer", "all"]


def plan_document(question: str) -> DocumentType:
    text = question.lower()

    salary_terms = {"salary", "payslip", "pay slip", "ctc", "gross pay", "net pay"}
    bank_terms = {"bank", "statement", "transaction", "deposit", "withdrawal", "balance"}
    offer_terms = {"offer", "appointment", "joining", "designation", "employment"}

    scores = {
        "salary": sum(term in text for term in salary_terms),
        "bank": sum(term in text for term in bank_terms),
        "offer": sum(term in text for term in offer_terms),
    }

    best_type = max(scores, key=scores.get)
    return best_type if scores[best_type] > 0 else "all"
