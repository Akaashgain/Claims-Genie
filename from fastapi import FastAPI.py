from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class ChatRequest(BaseModel):
	message: str

ssss
class ChatResponse(BaseModel):
	reply: str


def simple_bot(message: str) -> str:
	text = message.strip().lower()
	if any(g in text for g in ("hello", "hi", "hey")):
		return "Hello! How can I help you today?"
	if "help" in text:
		return "I can echo messages or answer simple greetings. Try saying 'hello' or send any text to echo."
	if text.endswith("?"):
		return "That's a good question — I'm a simple chatbot and don't have an answer to that yet."
	return f"You said: {message}"


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
	"""Simple chatbot endpoint."""
	reply = simple_bot(req.message)
	return ChatResponse(reply=reply)


if __name__ == "__main__":
	import uvicorn

	uvicorn.run(app, host="127.0.0.1", port=8000)

