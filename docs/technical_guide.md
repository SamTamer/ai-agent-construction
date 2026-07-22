# Technical Guide
## Construction Safety AI Agent — Setup & Architecture

---

## Prerequisites

- Python 3.10+
- An Anthropic API key (get one at console.anthropic.com)
- ~500MB disk space (ChromaDB + venv)

---

## Setup

**1. Clone the repository**
```bash
git clone https://github.com/riya-elizabeth/ai-agent-construction.git
cd ai-agent-construction
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**
```bash
cp .env.example .env
```
Open `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

**5. Run the FastAPI backend**
```bash
uvicorn api.main:app --reload --port 8000
```
Verify it's running: open `http://localhost:8000/health` in your browser.

**6. Run the Streamlit frontend** (new terminal)
```bash
streamlit run frontend/app.py
```
The UI opens at `http://localhost:8501`.

---

## Re-ingesting Documents

The ChromaDB vector store is pre-built and committed. If you need to re-ingest (e.g., after adding new PDFs):

```bash
# Default — creates/overwrites construction_procedures_v2 collection
python agent/ingest.py

# Custom collection name and chunk settings
python agent/ingest.py --collection my_collection --chunk-size 1800 --chunk-overlap 200

# Append new PDFs to an existing collection (preserves existing chunks)
python agent/ingest.py --pdf-dir data/procedures/new --collection construction_procedures --append
```

**Important:** The production collection (`construction_procedures`) uses page/section-based chunks (~1,880 chars avg) built from the original chunking pipeline — not the algorithmic splitter. Do not overwrite this collection unless you have verified the new chunks produce equivalent or better evaluation scores.

---

## Running Evaluations

**Quick coverage evaluation (75 questions):**
```bash
python evaluate_quick.py
# Against a specific collection:
python evaluate_quick.py --collection construction_procedures --out evaluation/my_results.json
```

**Hallucination scoring (LLM-as-judge):**
```bash
python evaluation/score_hallucination.py
```
Scores are written to `evaluation/eval_results.csv` — columns `correctness`, `completeness`, `hallucination`, `notes`.

---

## Architecture

```
User Question
     │
     ▼
Streamlit Frontend (frontend/app.py)
     │   ├── Renders chat UI with session history
     │   ├── Sends: {question, history[]} to API
     │
     ▼
FastAPI Backend (api/main.py)  — localhost:8000
     │   ├── Rate limiting: 10 req/min per IP
     │   ├── Input validation: non-empty, ≤500 chars
     │   ├── Prompt injection detection: regex patterns
     │
     ▼
RAG Pipeline (agent/rag_pipeline.py)
     │   ├── retrieve(): ChromaDB cosine similarity search
     │   │     └── top_k=5, similarity_threshold=0.50
     │   ├── Filters chunks below threshold
     │   ├── Builds prompt from system_prompt.txt template
     │   ├── Prepends full conversation history to Claude messages
     │
     ▼
Claude API (claude-sonnet-4-20250514)
     │   ├── temperature=0.0 (deterministic)
     │   ├── max_tokens=1024
     │   └── Answers grounded in retrieved context only
     │
     ▼
Response
     ├── Logged to qa_log.db (SQLite)
     └── If unanswered: logged to evaluation/unanswered_questions.csv
```

---

## Key Configuration Parameters

| Parameter | Location | Default | Notes |
|---|---|---|---|
| `top_k` | `rag_pipeline.py` | 5 | Chunks retrieved per query |
| `similarity_threshold` | `rag_pipeline.py` | 0.50 | Min cosine similarity to include a chunk |
| `max_tokens` | `rag_pipeline.py` | 1024 | Max response length |
| `temperature` | `rag_pipeline.py` | 0.0 | Deterministic responses |
| `RATE_LIMIT` | `api/main.py` | 10 | Max requests per minute per IP |
| `WINDOW_SECS` | `api/main.py` | 60 | Rate limit window |

---

## File Reference

| File | Purpose |
|---|---|
| `agent/rag_pipeline.py` | Core RAG engine — retrieval, prompt building, Claude API call |
| `agent/ingest.py` | PDF ingestion — chunking and ChromaDB loading |
| `agent/system_prompt.txt` | Agent behavior rules and response constraints |
| `api/main.py` | FastAPI backend — validation, rate limiting, injection detection |
| `frontend/app.py` | Streamlit chat UI |
| `evaluation/ground_truth.csv` | 75-question ground truth Q&A set |
| `evaluation/eval_results.csv` | Full evaluation results with hallucination scores |
| `evaluate_quick.py` | Coverage evaluation script |
| `evaluation/score_hallucination.py` | LLM-as-judge hallucination scoring |
| `chroma_db/` | ChromaDB persistent vector store (288 chunks) |
| `qa_log.db` | SQLite log of all queries and responses |
| `evaluation/unanswered_questions.csv` | Auto-populated gap repository |
