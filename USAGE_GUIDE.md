# RAG Support System - Usage Guide

## Overview

This is a Retrieval-Augmented Generation (RAG) system for customer support that uses:
- **GPT-OSS-120b-TEE** model via Chutes.ai API
- **ChromaDB** for vector storage (port 8001)
- **FastAPI** backend (port 8000)
- **Streamlit** frontend UI

## Prerequisites

- Python 3.12
- Virtual environment activated
- `.env` file configured with API keys

## Configuration (.env)

Your `.env` file should contain:

```env
# Chutes API for GPT-OSS-120b model
CHUTES_API_TOKEN=cpk_2f440db51a7d4c8484caacd1da18b951.5dc7e7da15ff507c9ab876c3d78c8858.bsCzLnmBl6su6Q13ZCx4NlYDkEKmznu1
CHUTES_API_BASE_URL=https://llm.chutes.ai/v1
CHUTES_MODEL=openai/gpt-oss-120b-TEE

# OpenAI API for embeddings (text-embedding-3-small)
OPENAI_API_KEY=cpk_2f440db51a7d4c8484caacd1da18b951.5dc7e7da15ff507c9ab876c3d78c8858.bsCzLnmBl6su6Q13ZCx4NlYDkEKmznu1

# Database
DATABASE_URL=sqlite:///./rag_system.db

# ChromaDB (vector database)
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

## How to Run the System

### Step 1: Start ChromaDB (Vector Database)

Open a new terminal and run:

```bash
chroma-server --host localhost --port 8001
```

Or using Docker:

```bash
docker run -p 8001:8000 chromadb/chroma
```

**Keep this terminal running!**

### Step 2: Start FastAPI Backend

Open a new terminal and run:

```bash
# Activate virtual environment (if not already activated)
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Start the FastAPI server
python -m app.main
```

The API will be available at: `http://localhost:8000`

**Keep this terminal running!**

### Step 3: Start Streamlit Frontend

Open a new terminal and run:

```bash
# Activate virtual environment (if not already activated)
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Start Streamlit
streamlit run app/ui/streamlit_app.py
```

The UI will open in your browser at: `http://localhost:8501`

## Using the Streamlit UI

### Navigation

The Streamlit app has 3 pages accessible from the sidebar:

1. **Chat** - Ask questions and get answers from the knowledge base
2. **Knowledge Base** - Manage documents in the knowledge base
3. **Analytics** - View query statistics and metrics

### Chat Page

The Chat page has the following controls:

| Control | Description | Default | Range |
|---------|-------------|---------|-------|
| **Context Chunks** | Number of document chunks to retrieve for each query | 5 | 1-10 |

**How to use:**
1. Type your question in the "Your Question" text area
2. Adjust "Context Chunks" if needed (more chunks = more context, but slower)
3. Click "🔍 Search"
4. View the answer with sources and metrics

### API Status Check

At the bottom of the Chat page, expand "🔧 API Status" to:
- Check if the backend API is healthy
- View collection count (number of documents in knowledge base)
- See the model being used

## Troubleshooting

### Streamlit Error - No Logs Shown

If you see an error in Streamlit but no detailed logs:

1. **Check the terminal** where Streamlit is running - errors are logged there
2. **Expand the error details** - click "View full error details" in the UI
3. **Check API Status** - expand "🔧 API Status" at the bottom of the Chat page

### Common Issues

| Issue | Solution |
|-------|----------|
| "Could not connect to the API" | Make sure FastAPI backend is running on port 8000 |
| "Failed to connect to ChromaDB" | Make sure ChromaDB is running on port 8001 |
| "API key not provided" | Check your `.env` file has `CHUTES_API_TOKEN` and `OPENAI_API_KEY` |
| "No documents in collection" | You need to ingest documents first via the Knowledge Base page |

### Port Conflicts

If you get port conflicts:

- **FastAPI**: Uses port 8000
- **ChromaDB**: Uses port 8001 (changed from 8000 to avoid conflict)
- **Streamlit**: Uses port 8501

To change ports, edit the `.env` file or the respective startup commands.

## API Endpoints

You can also interact with the system directly via API:

### Query the RAG System

```bash
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the refund policy?",
    "k": 5
  }'
```

### Health Check

```bash
curl http://localhost:8000/api/rag/health
```

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

## Streamlit Switches Summary

| Switch | Location | Description | Default | Range |
|--------|----------|-------------|---------|-------|
| **Context Chunks** | Chat page | Number of context chunks to retrieve | 5 | 1-10 |

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `CHUTES_API_TOKEN` | API key for Chutes.ai (GPT-OSS-120b) | Yes |
| `CHUTES_API_BASE_URL` | Chutes API base URL | Yes |
| `CHUTES_MODEL` | Model name to use | Yes |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | Yes |
| `DATABASE_URL` | SQLite database URL | Yes |
| `CHROMA_HOST` | ChromaDB host | Yes |
| `CHROMA_PORT` | ChromaDB port | Yes |
