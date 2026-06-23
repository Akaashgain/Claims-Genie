import json
import os
from enum import Enum
from typing import Optional

import boto3
import httpx
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Claims Genie",
    description="Claims Genie generates STD/LTD claim letters using Claude and Bedrock.",
    version="1.0.0",
)

HUMAN_PROMPT = "\n\nHuman:"
AI_PROMPT = "\n\nAssistant:"

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-4.6")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3")
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "claude").lower()

PROMPT_TEMPLATES = {
    "std": (
        "You are a claims assistant that transforms raw claim manager notes into a professional short-term disability letter. "
        "Use the claim number, state the claim type clearly as short-term disability, and keep the tone formal and concise. "
        "Include a summary of the manager's notes and indicate any next steps or coverage decisions that are relevant.\n\n"
        "Claim number: {claim_number}\n"
        "Claim type: Short-Term Disability (STD)\n"
        "Raw claim notes:\n{claim_notes}\n\n"
        "Generate the final claim letter below."
    ),
    "ltd": (
        "You are a claims assistant that transforms raw claim manager notes into a professional long-term disability letter. "
        "Use the claim number, state the claim type clearly as long-term disability, and keep the tone formal, compassionate, and focused on the claimant's ongoing needs. "
        "Include a summary of the manager's notes and indicate any next steps or decisions that are relevant.\n\n"
        "Claim number: {claim_number}\n"
        "Claim type: Long-Term Disability (LTD)\n"
        "Raw claim notes:\n{claim_notes}\n\n"
        "Generate the final claim letter below."
    ),
}


class ClaimType(str, Enum):
    std = "std"
    ltd = "ltd"


class LetterRequest(BaseModel):
    claim_number: str = Field(..., description="Unique claim identifier")
    claim_type: ClaimType = Field(..., description="Claim type: std or ltd")
    claim_notes: str = Field(..., description="Raw claim notes from the claim manager")
    provider: Optional[str] = Field(
        None,
        description="Optional AI provider override: claude or bedrock. If omitted, the backend default is used.",
    )


class LetterResponse(BaseModel):
    claim_number: str
    claim_type: ClaimType
    provider: str
    letter: str


def build_prompt(claim_number: str, claim_type: ClaimType, claim_notes: str) -> str:
    template = PROMPT_TEMPLATES.get(claim_type.value)
    if not template:
        raise ValueError("Unsupported claim type")
    return template.format(claim_number=claim_number, claim_notes=claim_notes)


def get_provider(requested_provider: Optional[str]) -> str:
    if requested_provider:
        requested = requested_provider.strip().lower()
        if requested not in {"claude", "bedrock"}:
            raise ValueError("provider must be either 'claude' or 'bedrock'")
        return requested
    return DEFAULT_PROVIDER if DEFAULT_PROVIDER in {"claude", "bedrock"} else "claude"


async def call_claude(prompt: str) -> str:
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing CLAUDE_API_KEY environment variable")

    url = "https://api.anthropic.com/v1/complete"
    payload = {
        "model": CLAUDE_MODEL,
        "prompt": f"{HUMAN_PROMPT} {prompt}{AI_PROMPT}",
        "max_tokens_to_sample": 900,
        "temperature": 0.2,
        "top_p": 1,
        "stop_sequences": ["\n\nHuman:"],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(
            f"Claude request failed with status {response.status_code}: {response.text}"
        )

    body = response.json()
    return body.get("completion", "").strip()


def parse_bedrock_output(body_text: str) -> str:
    try:
        parsed = json.loads(body_text)
    except json.JSONDecodeError:
        return body_text.strip()

    if isinstance(parsed, str):
        return parsed.strip()

    if isinstance(parsed, dict):
        if "outputText" in parsed:
            return parsed["outputText"].strip()
        if "results" in parsed and isinstance(parsed["results"], list):
            for result in parsed["results"]:
                if isinstance(result, dict) and "outputText" in result:
                    return result["outputText"].strip()
        if "outputs" in parsed and isinstance(parsed["outputs"], list):
            for output in parsed["outputs"]:
                if isinstance(output, dict):
                    if "content" in output and isinstance(output["content"], list):
                        for item in output["content"]:
                            if item.get("type") == "text/plain" and item.get("text"):
                                return item["text"].strip()
                    if "text" in output:
                        return output["text"].strip()
    return body_text.strip()


async def call_bedrock(prompt: str) -> str:
    try:
        client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
        payload = {"inputText": prompt}
        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload).encode("utf-8"),
        )
        body_bytes = response["body"].read()
        return parse_bedrock_output(body_bytes.decode("utf-8"))
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Bedrock request failed: {exc}") from exc


@app.get("/health")
async def health():
    return {"status": "ok", "provider": get_provider(None)}


@app.post("/generate-letter", response_model=LetterResponse)
async def generate_letter(request: LetterRequest):
    try:
        provider = get_provider(request.provider)
        prompt = build_prompt(request.claim_number, request.claim_type, request.claim_notes)

        if provider == "claude":
            letter_text = await call_claude(prompt)
        else:
            letter_text = await call_bedrock(prompt)

        if not letter_text:
            raise RuntimeError("AI provider returned an empty response")

        return LetterResponse(
            claim_number=request.claim_number,
            claim_type=request.claim_type,
            provider=provider,
            letter=letter_text,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
