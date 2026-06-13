# TravelAi Backend

This folder contains the backend API for the TravelAi agent. It exposes a FastAPI REST endpoint that forwards chat requests to a LangGraph-based agent using OpenRouter and tool integrations.

## Folder Structure

- `main.py` - FastAPI server and `/api/chat` endpoint implementation.
- `core/agent.py` - Agent definition, tool registration, and model configuration.
- `tools/` - Custom tool implementations for weather lookup, vector search, web search, and historical weather analysis.
- `requirements.txt` - Python dependencies for the backend.
- `test.py` - Local helper script for validating the backend tool functions and Pinecone connectivity.
- `.env.secret` - Environment variables required for runtime (not committed).

## Requirements

- `Python 3.12` recommended
- `pip` or `venv` available

## Setup

1. Create and activate a Python virtual environment:

```bash
cd back
python3 -m venv venv (or python3.12 -m venv venv)
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create or update `.env.secret` with the required secrets:

```bash
TAVILY_API_KEY=your_tavily_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_index_name
```
## Running the Server

Start the backend API server:

```bash
cd back
python3 main.py
```

The server will be available at `http://127.0.0.1:8000`.

## API Endpoints

### `GET /`
Simple health check endpoint.

### `POST /api/chat`
Send a chat request to the TravelAi agent.

Request body:

```json
{
  "message": "Plan a 3-day trip to Paris.",
  "user_id": "user123",
  "thread_id": "optional-thread-id"
}
```

Response body:

```json
{
  "thread_id": "<thread-id>",
  "response": "<agent response>",
  "history_snapshot": []
}
```

### `POST /api/preferences/ingest`
Ingest a user preference record into Pinecone for personalization.

Request body:

```json
{
  "user_id": "user123",
  "preference": "I prefer luxury resorts and avoid rainy seasons."
}
```

## Notes

- The backend uses OpenRouter via `langchain_openrouter` and a prebuilt LangGraph ReAct agent.
- The current backend can optionally fetch user preference metadata from Pinecone and inject it into the agent prompt.
- Use the `test.py` script to validate individual tool functions and vector DB connectivity.

## Troubleshooting

- If `uvicorn` is missing, install it with `pip install uvicorn`.
- If the OpenRouter provider returns a tool support error, confirm the configured model supports tool use.
- If Pinecone errors occur, verify `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` in `.env.secret`.
