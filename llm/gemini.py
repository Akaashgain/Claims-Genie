import os

try:
    import google.generativeai as legacy_genai  # type: ignore
except ImportError:  # pragma: no cover - runtime fallback
    legacy_genai = None

try:
    from google import genai as google_genai  # type: ignore
except ImportError:  # pragma: no cover - runtime fallback
    google_genai = None


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")


def _format_context(context_chunks: list[dict]) -> str:
    if not context_chunks:
        return "No relevant document context was found."

    formatted = []
    for item in context_chunks:
        formatted.append(
            f"Source: {item['source']} | Type: {item['document_type']} | Page: {item['page']}\n"
            f"{item['chunk']}"
        )
    return "\n\n---\n\n".join(formatted)


def _extract_text(response) -> str:
    text = getattr(response, "text", None)
    if text:
        return text.strip()

    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            part_text = getattr(part, "text", None)
            if part_text:
                return part_text.strip()

    return ""


def generate_answer(question: str, context_chunks: list[dict], document_type: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return (
            "GEMINI_API_KEY is not set. Add it to your environment, then ask again. "
            "The document search ran, but the final LLM answer could not be generated."
        )

    prompt = f"""
You are an agentic document assistant.
The planner selected this document type: {document_type}.

Answer the user's question using only the document context below.
If the answer is not present, say that the uploaded documents do not contain enough information.
Be concise and mention source file names when helpful.

Question:
{question}

Document context:
{_format_context(context_chunks)}
"""

    if legacy_genai is not None and hasattr(legacy_genai, "configure") and hasattr(legacy_genai, "GenerativeModel"):
        legacy_genai.configure(api_key=api_key)
        model = legacy_genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return _extract_text(response)

    if google_genai is not None and hasattr(google_genai, "Client"):
        client = google_genai.Client(api_key=api_key)
        response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return _extract_text(response)

    raise RuntimeError("No supported Google Gemini SDK is installed. Install google-generativeai or google-genai.")
