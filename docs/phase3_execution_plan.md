# Phase 3 Execution Plan — Agent Building & Integration
**Building AI Agents for Construction Field Procedures**
**Owner: Riya (Agent Developer)**

---

## Goal
Connect everything built in Phase 2 into a working, testable AI agent. By the end of this phase you will have a system where a construction technician can type a question, and the agent retrieves relevant chunks from ChromaDB, sends them to Claude, and returns a grounded, cited answer — or flags the question as unanswered if no relevant content is found.

---

## Architectural Decisions (Locked Before You Write Any Code)

These are confirmed before starting Step 3.1:

| Decision | Value | Reason |
|---|---|---|
| Similarity threshold | 0.5 | Scores 0.70–0.74 are excellent for technical docs |
| Top-K retrieval | 5 | Start here; tune up to 7 in Phase 4 if retrieval fails |
| Out-of-scope handling | Hybrid guided refusal | Log unanswered Qs for gap repo, don't just say "I don't know" |
| Citation format | Regulation number + section title | e.g., "Per section 1670..." |
| Conversation memory | Stateless (v1) | Simplest to build; revisit in Phase 4 if needed |
| Safety disclaimer | Always on for fall/electrical/confined space | Hardcoded into system prompt |
| Temperature | 0.0 | Deterministic answers, no hallucination drift |
| Max tokens per response | 1024 | Prevents runaway API costs |

---

## Files You Will Create or Edit This Phase

| File | What It Does |
|---|---|
| `agent/system_prompt.txt` | The instructions Claude follows for every query |
| `agent/rag_pipeline.py` | The core engine: query → retrieve → prompt → respond → log |
| `api/main.py` | FastAPI wrapper that exposes the pipeline as an `/ask` endpoint |
| `frontend/app.py` | Streamlit chat UI (owned by Docs & Demo Lead) |
| `requirements.txt` | Updated with any new dependencies |

---

## Step 3.1 — System Prompt Engineering
**Owner: Riya | File: `agent/system_prompt.txt`**

### What it is
The system prompt is the set of instructions you give Claude before every user question. It defines the agent's persona, what it can and cannot do, how it must cite sources, and what to say when it can't find an answer.

### What to write
Create `agent/system_prompt.txt` with the following content:

```
You are a construction safety assistant trained on Cal/OSHA and OSHA procedure documents.
Your job is to help construction technicians answer safety and procedure questions quickly and accurately on the job site.

RULES YOU MUST FOLLOW:

1. ONLY answer based on the provided context from the procedure documents. Never make up
   information or use outside knowledge.

2. When you answer a question, ALWAYS cite the specific section or regulation number
   from the source material (e.g., "Per section 1670..." or "According to Cal/OSHA 3395...").

3. If the provided context does not contain enough information to answer the question,
   respond EXACTLY with:
   "I cannot find this information in the available procedures. This question has been logged for review by the team lead."

4. Keep answers concise but complete. Construction workers need quick, actionable answers.

5. If a question involves a safety-critical situation (fall protection, electrical hazards,
   confined spaces, heat illness), always add this disclaimer at the end:
   "⚠️ Safety-critical topic: When in doubt, stop work and consult a qualified supervisor."

6. Format answers for easy reading: use short paragraphs and highlight key numbers,
   distances, or requirements.

7. Never provide medical advice. For injury or illness questions, direct the worker to
   seek immediate medical attention.

CONTEXT FROM PROCEDURE DOCUMENTS:
{context}

USER QUESTION:
{question}
```

### How to verify it's done
Run 5 manual tests directly via the Claude API (before the full pipeline is built) using hard-coded context chunks. Check that:
- Answers cite regulation numbers
- Out-of-scope questions trigger the exact fallback message
- Safety topics include the disclaimer

### Commit when done
```bash
git add agent/system_prompt.txt
git commit -m "Step 3.1: System prompt written and tested"
git push origin main
```

---

## Step 3.2 — RAG Pipeline Construction
**Owner: Riya | File: `agent/rag_pipeline.py`**

### What it is
This is the core of the project. It connects ChromaDB → Claude API → SQLite logging into one function call.

### How it works (plain English)
1. User sends a question
2. Pipeline converts the question into an embedding and searches ChromaDB for the top-5 most relevant chunks
3. Those chunks are inserted into the system prompt as `{context}`
4. The full prompt is sent to Claude API
5. Claude returns a grounded answer
6. The query, chunks retrieved, response, and timestamp are logged to SQLite
7. The answer is returned to the caller

### The code
Create `agent/rag_pipeline.py`:

```python
import os
import sqlite3
import json
from datetime import datetime
import chromadb
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class RAGPipeline:
    def __init__(self,
                 chroma_path="./chroma_db",
                 collection_name="construction_procedures",
                 sqlite_path="qa_log.db",
                 top_k=5,
                 similarity_threshold=0.5):

        # Connect to ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.chroma_client.get_collection(collection_name)

        # Connect to Claude
        self.claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Load system prompt
        with open("agent/system_prompt.txt", "r") as f:
            self.system_prompt_template = f.read()

        # Settings
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.sqlite_path = sqlite_path

        # Set up SQLite logging
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.sqlite_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS qa_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                question TEXT,
                retrieved_chunks TEXT,
                response TEXT,
                answered INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def retrieve(self, query):
        """Search ChromaDB for the most relevant chunks."""
        results = self.collection.query(
            query_texts=[query],
            n_results=self.top_k
        )

        chunks = []
        sources = []

        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i]
                # ChromaDB cosine distance: lower = more similar
                # Convert to similarity score
                similarity = 1 - distance

                if similarity >= self.similarity_threshold:
                    chunks.append(doc)
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    source = meta.get("source_file", "unknown")
                    page = meta.get("page", "")
                    sources.append(f"{source} (page {page})")

        return chunks, sources

    def ask(self, question):
        """Run the full RAG pipeline for a question."""
        # Step 1: Retrieve relevant chunks
        chunks, sources = self.retrieve(question)

        # Step 2: Check if we have enough context
        answered = True
        if not chunks:
            answered = False
            context = "No relevant context found."
        else:
            context = "\n\n---\n\n".join(chunks)

        # Step 3: Build the prompt
        prompt = self.system_prompt_template.replace("{context}", context).replace("{question}", question)

        # Step 4: Call Claude API
        message = self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        response = message.content[0].text

        # Step 5: Check if agent flagged as unanswered
        if "I cannot find this information" in response:
            answered = False
            self._log_unanswered(question)

        # Step 6: Log to SQLite
        self._log_to_db(question, chunks, response, answered)

        return {
            "question": question,
            "response": response,
            "sources": sources,
            "answered": answered
        }

    def _log_to_db(self, question, chunks, response, answered):
        conn = sqlite3.connect(self.sqlite_path)
        conn.execute("""
            INSERT INTO qa_log (timestamp, question, retrieved_chunks, response, answered)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            question,
            json.dumps(chunks),
            response,
            int(answered)
        ))
        conn.commit()
        conn.close()

    def _log_unanswered(self, question):
        """Append unanswered question to CSV for gap repository."""
        import csv
        filepath = "evaluation/unanswered_questions.csv"
        file_exists = os.path.exists(filepath)
        with open(filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "question"])
            writer.writerow([datetime.now().isoformat(), question])


# Quick test when run directly
if __name__ == "__main__":
    pipeline = RAGPipeline()
    test_questions = [
        "At what height is fall protection required?",
        "What are the water requirements for heat illness prevention?",
        "What is the recipe for chocolate cake?"  # Should trigger unanswered
    ]
    for q in test_questions:
        print(f"\nQ: {q}")
        result = pipeline.ask(q)
        print(f"A: {result['response'][:300]}...")
        print(f"Sources: {result['sources']}")
        print(f"Answered: {result['answered']}")
```

### How to test it
```bash
source venv/bin/activate
python agent/rag_pipeline.py
```

You should see answers for the first two questions and the fallback message for the chocolate cake question.

### Commit when done
```bash
git add agent/rag_pipeline.py
git commit -m "Step 3.2: RAG pipeline built and tested end-to-end"
git push origin main
```

---

## Step 3.3 — Unanswered Question Detection
**Already built into Step 3.2 above.**

The pipeline automatically:
- Checks if retrieved chunks are below the similarity threshold → flags as unanswered
- Checks if Claude's response contains the fallback phrase → flags as unanswered
- Logs all unanswered questions to `evaluation/unanswered_questions.csv`

### Verify it works
Run the pipeline with an out-of-scope question:
```python
result = pipeline.ask("What is the maximum weight a forklift can carry?")
```
Then check:
```bash
cat evaluation/unanswered_questions.csv
```
The question should appear there.

---

## Step 3.4 — FastAPI Backend
**Owner: Riya | File: `api/main.py`**

### What it is
A lightweight web server that wraps the RAG pipeline. The Streamlit frontend and any other tool can send questions to it via HTTP and get answers back.

### The code
Create `api/main.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent.rag_pipeline import RAGPipeline
import os

app = FastAPI(title="Construction Safety AI Agent")

# Load pipeline once at startup
pipeline = RAGPipeline()

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    question: str
    response: str
    sources: list
    answered: bool

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Construction Safety Agent is running"}

@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    result = pipeline.ask(request.question)
    return result
```

### How to run it
```bash
source venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

Then open your browser and go to:
- `http://localhost:8000/health` → should return `{"status": "ok"}`
- `http://localhost:8000/docs` → interactive API docs (Swagger UI)

### Commit when done
```bash
git add api/main.py
git commit -m "Step 3.4: FastAPI backend running on /ask endpoint"
git push origin main
```

---

## Step 3.5 — Streamlit Frontend
**Owner: Docs & Demo Lead | File: `frontend/app.py`**

### What it is
A simple chat interface that sends questions to the FastAPI backend and displays answers with source citations.

### Minimum requirements
- Text input for the user's question
- Display of the agent's answer
- Display of source documents cited
- Visual flag when a question is unanswered
- Chat history so previous Q&As stay visible

### How to run it (once built)
```bash
streamlit run frontend/app.py
```

---

## Step 3.6 — Internal Alpha Testing
**Owner: Full Team**

### What to do
With the backend running (`uvicorn`) and frontend running (`streamlit`), manually test 20+ questions from `evaluation/ground_truth.csv` through the UI.

For each question record:
- Did it answer correctly?
- Did it cite a regulation number?
- Did it hallucinate anything not in the source documents?
- Did it correctly flag out-of-scope questions?

### Common failure modes and fixes

| Failure | Fix |
|---|---|
| Wrong chunks retrieved | Increase `top_k` from 5 to 7 |
| Answer too vague | Tighten system prompt wording |
| Hallucination detected | Lower temperature, add stronger grounding instructions |
| Out-of-scope not flagged | Lower similarity threshold from 0.5 to 0.4 |
| Answer too long | Add "Keep answers under 150 words" to system prompt |

### Commit when done
```bash
git add .
git commit -m "Phase 3 Complete: RAG pipeline, FastAPI, Streamlit UI, alpha tested"
git push origin main
```

---

## Phase 3 Milestone Checklist

- [ ] Architectural decisions locked (top-K=5, threshold=0.5, stateless, temp=0.0)
- [ ] `agent/system_prompt.txt` written and manually tested
- [ ] `agent/rag_pipeline.py` running end-to-end
- [ ] Unanswered questions logging to `evaluation/unanswered_questions.csv`
- [ ] FastAPI running at `http://localhost:8000/ask`
- [ ] Health check passing at `http://localhost:8000/health`
- [ ] Streamlit UI connected to backend
- [ ] 20+ alpha test questions run through the full system
- [ ] Obvious failure modes fixed
- [ ] All code committed and pushed to GitHub

---

## Execution Order (Do These In Sequence)

```
Step 3.1 → Write system_prompt.txt → test manually → commit
Step 3.2 → Write rag_pipeline.py → python agent/rag_pipeline.py → commit
Step 3.3 → Verify unanswered_questions.csv populates → commit
Step 3.4 → Write api/main.py → uvicorn → test /health → commit
Step 3.5 → Docs & Demo Lead builds frontend → connect to backend
Step 3.6 → Run 20+ alpha tests → fix failures → final commit
```

---

## Quick Reference Commands for Phase 3

| Action | Command |
|---|---|
| Activate venv | `source venv/bin/activate` |
| Test RAG pipeline directly | `python agent/rag_pipeline.py` |
| Start FastAPI backend | `uvicorn api.main:app --reload --port 8000` |
| Start Streamlit frontend | `streamlit run frontend/app.py` |
| Check unanswered questions | `cat evaluation/unanswered_questions.csv` |
| Commit progress | `git add . && git commit -m "message" && git push origin main` |
