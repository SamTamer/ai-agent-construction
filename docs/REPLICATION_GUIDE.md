# Replication Guide
## How to Build a RAG Agent for Domain-Specific Q&A

*Based on the Construction Safety AI Agent — MSBA Practicum, Ampytics, May 2026*

This guide walks through building a production-quality Retrieval-Augmented Generation (RAG) chatbot from scratch. The construction safety use case is used throughout, but every step generalizes — the same architecture works for HR policy, legal Q&A, medical guidelines, or any domain where you need cited, document-grounded answers.

---

## What You're Building

A system where users ask questions in plain English and receive cited answers grounded exclusively in verified source documents. The system never guesses — if the answer isn't in the documents, it says so and logs the gap for review.

```
User Question
     ↓
Chat UI (Streamlit)
     ↓
API Backend (FastAPI) — validation, rate limiting, security
     ↓
RAG Pipeline — retrieves relevant document chunks
     ↓
Claude API — generates answer from retrieved context only
     ↓
Cited Response + Confidence Indicator
     ↓
Logging (SQLite + CSV for unanswered questions)
```

**Why RAG instead of fine-tuning?**
- Fine-tuning requires labeled training data, compute cost, and retraining whenever documents update
- RAG updates by re-ingesting new documents — no model changes needed
- For regulatory/compliance use cases, RAG is almost always the right choice
- RAG is fully auditable: every answer traces back to a specific chunk from a specific document

---

## Prerequisites

- Python 3.10+
- An Anthropic API key ([console.anthropic.com](https://console.anthropic.com))
- Your source documents as PDFs
- ~500MB disk space (ChromaDB + virtual environment)

**Technology choices in this project:**

| Component | Choice | Why |
|---|---|---|
| LLM | Anthropic Claude | Reliable instruction-following, stays grounded in context |
| Vector database | ChromaDB | Persistent, simple Python API, bundles its own embeddings |
| Embeddings | Sentence Transformers (ChromaDB default) | No extra API costs or latency |
| Backend | FastAPI | Lightweight, fast, built-in validation |
| Frontend | Streamlit | Chat UI in ~100 lines of Python |

---

## Step 0: Choose Your Domain and Source Documents

Before writing any code, decide:

1. **What questions will users ask?** Write 20–30 example questions at the start. This forces you to be specific about scope and will become the seed for your evaluation set.

2. **What documents will ground the answers?** Collect the authoritative PDFs. For construction safety: Cal/OSHA Pocket Guide, OSHA Construction Safety Manual, OSHA Trenching Guide. For another domain: policy manuals, regulation documents, product documentation, etc.

3. **What happens when the system can't answer?** Design this before you build. In this project: the agent returns a fixed fallback phrase and logs the question. Don't let "I don't know" be an afterthought.

Store your PDFs in `data/procedures/` (or any directory — you'll reference it later).

---

## Step 1: Set Up the Environment

```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
pip install anthropic chromadb fastapi uvicorn streamlit python-dotenv pypdf requests
pip freeze > requirements.txt
```

Create `.env` in the project root:
```
ANTHROPIC_API_KEY=your-key-here
```

Create `.env.example` (safe to commit):
```
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

Add `.env` to `.gitignore` immediately. Never commit API keys.

---

## Step 2: Build the Evaluation Framework First

**This is the most important step — do it before writing any agent code.**

Build a ground truth dataset of 50–75 questions with expected answers, covering:
- Easy questions (directly stated in one section of the source documents)
- Medium questions (require synthesizing across sections)
- Hard questions (edge cases, specific numbers, multi-part answers)

Also include 10–15 questions you know cannot be answered from the documents. These validate that your agent correctly refuses rather than guessing.

For this project: `evaluation/ground_truth.csv` with columns `question`, `expected_answer`, `difficulty`, `topic`.

**Why build this first?** Every subsequent decision — chunking strategy, similarity threshold, system prompt wording — can be measured objectively against this dataset. Without it, you're guessing whether changes help. With it, you have a regression test for every experiment.

---

## Step 3: Ingest Documents into ChromaDB

`agent/ingest.py` handles PDF reading, chunking, and loading into ChromaDB.

**Core logic:**
```python
import chromadb
from pypdf import PdfReader

# Initialize persistent ChromaDB
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection("your_collection_name")

# Read and chunk PDFs
reader = PdfReader("data/procedures/your_doc.pdf")
chunks = []
for page_num, page in enumerate(reader.pages):
    text = page.extract_text()
    if text.strip():
        chunks.append({
            "text": text,
            "metadata": {"source_file": "your_doc.pdf", "page": page_num + 1}
        })

# Load into ChromaDB
collection.add(
    documents=[c["text"] for c in chunks],
    metadatas=[c["metadata"] for c in chunks],
    ids=[f"doc_{i}" for i in range(len(chunks))]
)
```

**Critical chunking decision:** This project tested three strategies:

| Strategy | Chunks | Coverage |
|---|---|---|
| Page/section-based (~1,880 chars avg) | 288 | **84%** |
| Algorithmic 500-char splits | 1,101 | 24% |
| Algorithmic 1,200-char splits | 497 | 13% |

Smaller chunks sound more precise but they fragment regulatory sections, destroying the context that makes answers accurate. For dense, structured documents (regulations, manuals, policies), preserve natural boundaries — pages or sections — rather than splitting at fixed character counts.

**Run ingestion:**
```bash
python agent/ingest.py --pdf-dir data/procedures --collection your_collection --chunk-size 1800 --chunk-overlap 200
```

See `agent/ingest.py` for the full implementation with CLI arguments, append mode, and metadata handling.

---

## Step 4: Write the System Prompt

The system prompt is the most important single file in the project. It defines the agent's behavior, constraints, and fallback responses.

`agent/system_prompt.txt` — key rules enforced in this project:

1. **Answer only from provided context.** The agent must not draw on general training knowledge.
2. **Always cite the regulation section.** Every answer must include the source document and section number.
3. **Use a fixed fallback phrase** when context is insufficient: *"I cannot find this information in the available procedures."* Using an exact phrase lets you programmatically detect unanswered questions.
4. **Append safety disclaimers** for critical topics (falls, electrical, confined spaces, heat illness).
5. **Do not speculate or estimate.** If the number isn't in the document, say so.

Write your system prompt before building the pipeline. Test it manually against edge cases before automating evaluation.

---

## Step 5: Build the RAG Pipeline

`agent/rag_pipeline.py` — the core retrieval and generation logic.

**Retrieval:**
```python
def retrieve(query: str, collection, top_k: int = 5, threshold: float = 0.50):
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    # Filter by similarity threshold
    chunks = []
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        similarity = 1 - dist  # ChromaDB returns cosine distance
        if similarity >= threshold:
            chunks.append({"text": doc, "metadata": meta, "similarity": similarity})
    return chunks
```

**Generation:**
```python
import anthropic
from pathlib import Path

client = anthropic.Anthropic()
system_prompt = Path("agent/system_prompt.txt").read_text()

def ask(question: str, history: list = []) -> dict:
    chunks = retrieve(question, collection)

    if not chunks:
        # No chunks above threshold — route to fallback
        return {"response": "I cannot find this information in the available procedures.",
                "answered": False, "sources": []}

    context = "\n\n".join([f"[{c['metadata']['source_file']}, p.{c['metadata']['page']}]\n{c['text']}"
                           for c in chunks])

    messages = history + [{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        temperature=0.0,   # Deterministic — critical for safety-critical answers
        system=system_prompt,
        messages=messages
    )

    answer = response.content[0].text
    answered = "I cannot find this information" not in answer

    return {"response": answer, "answered": answered,
            "sources": [c["metadata"] for c in chunks]}
```

**Key parameters:**
- `top_k=5` — retrieve 5 chunks per query
- `similarity_threshold=0.50` — chunks below this are excluded
- `temperature=0.0` — deterministic; never use >0 for regulatory Q&A
- `max_tokens=1024` — sufficient for most cited regulatory answers

Log every query and response to SQLite for later analysis.

---

## Step 6: Build the API Layer

`api/main.py` — FastAPI backend that wraps the RAG pipeline with security.

**Essential middleware:**
```python
from fastapi import FastAPI, Request, HTTPException
from collections import defaultdict
import time, re

app = FastAPI()

# Rate limiting
request_counts = defaultdict(list)
RATE_LIMIT = 10
WINDOW_SECS = 60

def check_rate_limit(ip: str):
    now = time.time()
    request_counts[ip] = [t for t in request_counts[ip] if now - t < WINDOW_SECS]
    if len(request_counts[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    request_counts[ip].append(now)

# Prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore (previous|prior|all) instructions",
    r"disregard (your|the) (system|previous)",
    r"you are now",
    r"act as (if you are|a)",
]

def detect_injection(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in INJECTION_PATTERNS)

@app.post("/ask")
async def ask_endpoint(request: Request, body: dict):
    check_rate_limit(request.client.host)
    question = body.get("question", "").strip()

    if not question or len(question) > 500:
        raise HTTPException(status_code=400, detail="Question must be 1–500 characters")
    if detect_injection(question):
        raise HTTPException(status_code=400, detail="Invalid input")

    result = ask(question, body.get("history", []))
    return result
```

See `api/main.py` for the full implementation.

**Run:**
```bash
uvicorn api.main:app --reload --port 8000
```

---

## Step 7: Build the Chat UI

`frontend/app.py` — Streamlit chat interface.

Key features to include:
- Session history (pass prior turns to the API as `history`)
- Source citations displayed per answer
- Confidence indicator (high/medium based on similarity score)
- Visual flag for unanswered questions
- Download button for conversation export
- Coverage statistics (% of questions answered in session)

```bash
streamlit run frontend/app.py
```

See `frontend/app.py` for the full implementation (~200 lines).

---

## Step 8: Evaluate Your Agent

Run all ground truth questions through the pipeline and measure coverage:

```bash
python evaluate_quick.py
```

`evaluate_quick.py` runs each question from `evaluation/ground_truth.csv`, records whether the agent answered or used the fallback, and outputs:
- Coverage % (answered / total)
- Per-question results as JSON
- Source documents cited per answer

**Hallucination scoring** (LLM-as-judge):
```bash
python evaluation/score_hallucination.py
```

This uses Claude to score each answer on:
- `correctness` (0–3): Is the answer factually accurate per the source documents?
- `completeness` (0–3): Does it cover all required parts of the expected answer?
- `hallucination` (yes/no): Does it state anything not in the retrieved context?

Results go to `evaluation/eval_results.csv`.

**Target metrics for a production-ready system:**
- Coverage: ≥80% (the remaining 20% should be confirmed knowledge gaps, not retrieval failures)
- Hallucination rate: 0% (non-negotiable for safety-critical domains)
- Correctness: ≥2.5/3.0

This project achieved: **84% coverage | 0% hallucination | 2.92/3.0 correctness**

---

## Step 9: Tune and Improve

If coverage is below target, investigate systematically — don't guess.

**Chunking experiments:** Test different chunking strategies against your eval set. Run `python evaluate_quick.py --collection test_collection` to compare. In this project, reducing chunk size from 1,800 to 500 chars dropped coverage from 84% to 24% — smaller is not better for regulatory text.

**Similarity threshold:** Lower threshold (e.g., 0.35) retrieves more chunks, which can help borderline questions but introduces noise. Higher threshold (e.g., 0.65) is more precise but increases fallback rate. Run the eval set at multiple thresholds and plot coverage vs. false-positive rate.

**System prompt iteration:** If correctly retrieved chunks are producing wrong answers, the problem is the system prompt, not retrieval. Add explicit rules, better fallback detection, or clearer citation formatting.

**Expanding the knowledge base:** If unanswered questions consistently cluster around a topic, that topic isn't in your source documents. The fix is adding documents, not tuning parameters.

```bash
# Add a new PDF
python agent/ingest.py \
  --pdf-dir data/procedures \
  --collection your_collection \
  --chunk-size 1800 --chunk-overlap 200 \
  --append

# Re-evaluate
python evaluate_quick.py
```

Log every experiment with the parameter change, coverage result, and your interpretation. See `docs/tuning_log.md` for this project's full experiment log.

---

## Key Lessons Learned

**Build evaluation first.** Every team that skips this spends weeks debating whether a change "feels better." Objective metrics end those debates immediately.

**Bigger chunks are better for regulatory text.** This is counterintuitive — you'd expect smaller, more targeted chunks to retrieve more precisely. But OSHA regulations are densely cross-referenced; fragmenting them destroys the context that makes answers complete.

**The system prompt is the product.** The LLM is a commodity. The system prompt — the rules, constraints, fallback phrases, and citation requirements — is what differentiates a useful safety tool from a dangerous one.

**Document the gaps explicitly.** The 12 unanswered questions in this project are not bugs. They're honest documentation of what the system doesn't know. A system that says "I don't know" is more trustworthy than one that guesses.

**Rate limiting is not optional.** Even in a demo, one aggressive user can exhaust your API budget in minutes. Build it on day one.

---

## Adapting This to a New Domain

To build the same architecture for a different domain (HR policy, legal Q&A, medical guidelines):

1. Replace `data/procedures/` PDFs with your domain's source documents
2. Rewrite `agent/system_prompt.txt` with domain-appropriate rules and citation format
3. Rebuild `evaluation/ground_truth.csv` with 50–75 questions from your domain
4. Re-ingest: `python agent/ingest.py --collection your_domain --chunk-size 1800`
5. Re-evaluate: `python evaluate_quick.py --collection your_domain`
6. The API and frontend require no changes

Everything else — ChromaDB, FastAPI, Streamlit, Claude — stays identical. The domain-specific logic lives in three places: your PDFs, your system prompt, and your ground truth dataset.

---

## Further Reading

| File | Contents |
|---|---|
| `docs/creation_process.md` | Phase-by-phase decision log — the full reasoning behind every major choice |
| `docs/tuning_log.md` | All chunking and threshold experiments with numeric results |
| `docs/retrospective.md` | What went well, what didn't, and what we'd do differently |
| `model_limitations.md` | Detailed analysis of the 12 unanswered questions and root causes |
| `docs/risk_cba_report.md` | Cost estimates, risk analysis, and recommendations for deployment |
