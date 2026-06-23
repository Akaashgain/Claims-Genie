# Claims Genie

Claims Genie is a FastAPI service that generates short-term disability (STD) and long-term disability (LTD) claim letters using Claude or AWS Bedrock.

## Features

- FastAPI endpoint for generating claim letters
- Two prompt templates: STD and LTD
- Backend provider selection: `claude` or `bedrock`
- Easy environment-based configuration

## Setup

1. Create a virtual environment and activate it.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set required environment variables:

- `CLAUDE_API_KEY`
- `BEDROCK_REGION` (optional, defaults to `us-east-1`)
- `BEDROCK_MODEL_ID` (optional, defaults to `anthropic.claude-3`)
- `DEFAULT_PROVIDER` (optional, `claude` or `bedrock`)

## Run

```bash
uvicorn app:app --reload
```

## API

### POST /generate-letter

Request body:

```json
{
  "claim_number": "12345",
  "claim_type": "std",
  "claim_notes": "Patient is expected to be out for 6 weeks due to recovery...",
  "provider": "claude"
}
```

Response:

```json
{
  "claim_number": "12345",
  "claim_type": "std",
  "provider": "claude",
  "letter": "...generated letter text..."
}
```

### GET /health

Returns service health and default provider.
