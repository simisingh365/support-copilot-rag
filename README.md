# RAG Customer Support System

A Python-based Retrieval-Augmented Generation (RAG) system for customer support, featuring document ingestion, semantic search, and AI-powered responses with source citations.

## Features

- **Document Ingestion**: Upload and index documents with multiple chunking strategies
- **Semantic Search**: Find relevant information using vector embeddings
- **RAG-Powered Responses**: Generate answers with source citations [1], [2], [3]
- **Ticket Management**: Track customer support tickets and conversations
- **Analytics Dashboard**: Monitor query performance and system usage
- **Streamlit UI**: User-friendly interface for easy interaction
- **RESTful API**: Full API for integration with other systems

## Quick Start

### 1. Clone and Install

```bash
git clone <repository-url>
cd support-copilot-rag-1
pip install -r requirements.txt
```

### 2. Get Your API Key

This project uses **Chutes.ai** for LLM capabilities. Get your free API key:

1. Go to [chutes.ai](https://chutes.ai)
2. Sign up for a free account
3. Copy your API token from your dashboard

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# Use your favorite editor, e.g.:
# nano .env
```

Your `.env` file should look like:
```env
CHUTES_API_TOKEN=your_chutes_api_token_here
CHUTES_API_BASE_URL=https://llm.chutes.ai/v1
CHUTES_MODEL=Qwen/Qwen3-32B
DATABASE_URL=sqlite:///./rag_system.db
CHROMA_HOST=localhost
CHROMA_PORT=8001
ANONYMIZED_TELEMETRY=False
```

### 4. Start ChromaDB

ChromaDB must be running before starting the application:

```bash
python run_chroma_server.py
```

### 5. Start the Application

**Option A: Start FastAPI Server + Streamlit UI**

```bash
# Terminal 1: FastAPI Server
python app/main.py

# Terminal 2: Streamlit UI
streamlit run app/ui/streamlit_app.py
```

**Option B: Just Streamlit UI** (if you only need the web interface)

```bash
streamlit run app/ui/streamlit_app.py
```

### 6. Access the Application

- **Streamlit UI**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs

---

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Web Framework | FastAPI | 0.104.1 |
| ASGI Server | Uvicorn | 0.24.0 |
| ORM | SQLAlchemy | 2.0.23 |
| LLM Provider | Chutes.ai/OpenAI | - |
| Vector Database | ChromaDB | 0.4.18 |
| UI Framework | Streamlit | 1.29.0 |

## Project Structure

```
support-copilot-rag-1/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── rag.py                       # RAG query endpoint
│   │   ├── knowledge.py                 # Document ingestion/listing
│   │   ├── tickets.py                   # Ticket management
│   │   └── analytics.py                 # Analytics endpoint
│   ├── core/
│   │   ├── __init__.py
│   │   ├── rag.py                       # RAG chain implementation
│   │   ├── retrieval.py                 # ChromaDB retrieval engine
│   │   ├── chunking.py                  # Text chunking strategies
│   │   └── embeddings.py                # OpenAI embedding generation
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py                    # SQLAlchemy models
│   │   └── session.py                   # Database session management
│   └── ui/
│       ├── streamlit_app.py             # Streamlit main app
│       └── pages/
│           ├── chat.py                  # Chat interface
│           ├── knowledge.py             # Knowledge base management
│           ├── tickets.py               # Ticket management UI
│           └── analytics.py             # Analytics dashboard
├── data/
│   └── knowledge_base/                  # Sample markdown documents
├── .env.example                         # Environment variables template
├── .gitignore                           # Git ignore rules
├── requirements.txt                     # Python dependencies
├── run_chroma_server.py                 # ChromaDB server launcher
└── README.md                            # This file
```

## API Endpoints

### RAG Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/rag/query` | Query the RAG system |
| GET | `/api/rag/health` | Check RAG API health |

### Knowledge Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/knowledge/ingest` | Ingest a document |
| GET | `/api/knowledge/documents` | List all documents |
| GET | `/api/knowledge/documents/{id}` | Get document details |
| DELETE | `/api/knowledge/documents/{id}` | Delete a document |

### Ticket Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tickets/` | Create a ticket |
| GET | `/api/tickets/` | List all tickets |
| GET | `/api/tickets/{id}` | Get ticket details |
| GET | `/api/tickets/{id}/messages` | Get ticket messages |
| POST | `/api/tickets/{id}/messages` | Add message to ticket |
| PATCH | `/api/tickets/{id}/status` | Update ticket status |

### Analytics Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/overview` | Get analytics overview |
| GET | `/api/analytics/queries` | Get recent queries |
| GET | `/api/analytics/stats` | Get system statistics |

## Example API Usage

### Query the RAG System

```bash
curl -X POST "http://localhost:8000/api/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the refund policy?",
    "k": 5
  }'
```

### Ingest a Document

```bash
curl -X POST "http://localhost:8000/api/knowledge/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Refund Policy",
    "content": "Our refund policy allows...",
    "category": "Policies",
    "tags": ["refund", "policy"],
    "chunking_strategy": "fixed_size"
  }'
```

### Create a Ticket

```bash
curl -X POST "http://localhost:8000/api/tickets/" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Issue with API",
    "content": "I am having trouble with the API...",
    "priority": "HIGH",
    "customer_id": "cust_123"
  }'
```

## Chunking Strategies

### Fixed Size Chunking

Splits text into fixed-size chunks (default 512 characters) with configurable overlap (default 50 characters).

```python
from app.core.chunking import FixedSizeChunker

chunker = FixedSizeChunker(chunk_size=512, overlap=50)
chunks = chunker.chunk(text)
```

### Semantic Chunking

Splits text at paragraph boundaries to preserve semantic coherence.

```python
from app.core.chunking import SemanticChunker

chunker = SemanticChunker(min_chunk_size=50)
chunks = chunker.chunk(text)
```

## Sample Knowledge Base

The project includes sample documents in `data/knowledge_base/`:

- `refund_policy.md` - Company refund policy
- `api_pricing.md` - API pricing tiers
- `account_deletion.md` - How to delete account
- `rate_limits.md` - API rate limits and handling
- `troubleshooting.md` - Common issues and solutions

## Development

### Running Tests

```bash
python app/test_rag.py
```

### Database Management

```python
from app.db.session import init_db, reset_db

# Initialize database (create tables)
init_db()

# Reset database (drop and recreate all tables)
reset_db()
```

## Troubleshooting

### ChromaDB Connection Issues

If you see connection errors:

1. Verify ChromaDB is running: `curl http://localhost:8001`
2. Check your `.env` file for correct `CHROMA_HOST` and `CHROMA_PORT`
3. Ensure no firewall is blocking the connection
4. If `chroma-server` command is not recognized, use: `python -m chromadb.cli.cli run --host localhost --port 8001`

### API Errors

If you encounter API errors:

1. Verify your API key is correct in `.env`
2. Check your API key has available credits
3. Review the Chutes.ai status page for service issues

### Import Errors

If you see import errors:

1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check you're using Python 3.9 or higher
3. Verify you're running from the project root directory

## Git Setup

This project is ready for git:

```bash
# Initialize git (if not already done)
git init

# Create your first commit
git add .
git commit -m "Initial commit: RAG Customer Support System"

# Add your remote repository
git remote add origin <your-repository-url>

# Push to GitHub
git push -u origin main
```

**Note**: The `.env` file is gitignored to protect your API keys. Each developer should:
1. Copy `.env.example` to `.env`
2. Add their own API keys
3. Never commit `.env` to git

---

**Built with ❤️ using FastAPI, ChromaDB, and Chutes.ai**
