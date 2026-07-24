# Creation Process
## Construction Safety AI Agent — Phase-by-Phase Decision Log

*Documented: May 2026*

---

## Phase 1 — Project Setup & Evaluation Framework

**Goal:** Define the problem, set up infrastructure, and build the evaluation framework before writing any agent code.

**Key decisions:**

**Chose RAG over fine-tuning**
Fine-tuning Claude on OSHA documents would have required labeled training data, significant compute cost, and re-training whenever regulations update. RAG with a vector store allows the knowledge base to be updated by simply re-ingesting new documents — no model changes required. For a regulatory compliance use case this was the clear choice.

**Built the 75-question ground truth dataset first**
Before writing a single line of agent code, we created a structured evaluation set covering 3 difficulty levels (easy/medium/hard) across all major topics in the source documents. This decision paid dividends throughout — every subsequent change could be measured objectively rather than guessed at.

**Chose ChromaDB as the vector store**
ChromaDB is persistent (survives server restarts), has a simple Python API, and bundles its own embedding model (sentence-transformers). No external embedding API calls needed, which reduces cost and latency.

**Chose Claude API over open-source LLMs**
Construction safety is safety-critical. Claude's instruction-following reliability and its ability to stay grounded in provided context (vs. drawing on general training) was the primary factor. Temperature=0.0 ensures deterministic, reproducible answers.

---

## Phase 2 — Knowledge Base Ingestion

**Goal:** Process source documents into a searchable vector store.

**Source documents selected:**
1. Cal/OSHA Pocket Guide for the Construction Industry (2022)
2. OSHA Construction Safety Manual
3. OSHA Trenching & Excavation Safety Guide

These were chosen for coverage of the most common construction safety topics: fall protection, excavation, PPE, heat illness, electrical, scaffolding, confined spaces.

**Chunking approach:**
Documents were chunked at natural page and section boundaries, producing 288 chunks at ~1,880 chars average. This preserved the semantic coherence of each regulatory section — a critical decision later validated by the Phase 4 chunking analysis.

**Metadata stored per chunk:**
- `source_file` — PDF filename
- `page` — page number
- `doc_id` — document identifier

This metadata enables source citations in every answer, which was a core product requirement.

---

## Phase 3 — Agent Building & Integration

**Goal:** Build the end-to-end pipeline and deploy a working agent.

**System prompt design**
The system prompt was the most critical design decision in Phase 3. Key rules enforced:
- Answer ONLY from provided context — no outside knowledge
- Always cite regulation numbers
- Return exact fallback phrase if context insufficient: *"I cannot find this information in the available procedures."*
- Append safety disclaimers for critical topics (falls, electrical, confined spaces, heat illness)

The exact fallback phrase was chosen deliberately so it could be detected programmatically to set `answered=False` — creating a reliable, automatable signal.

**FastAPI over Flask**
FastAPI provides automatic request validation via Pydantic models, async support, and auto-generated API docs. The rate limiting, input validation, and later prompt injection detection all fit cleanly into FastAPI's middleware pattern.

**Streamlit for the frontend**
Streamlit was chosen for speed of development and built-in session state management (which later made conversation memory straightforward to implement). The chat UI, source citations, confidence indicators, and session statistics were all built in a single `app.py` file.

**Alpha testing result: 84% coverage**
The initial evaluation run returned 84% (63/75). The 12 unanswered questions were logged and categorized into three topic patterns. This became the baseline for all Phase 4 work.

---

## Phase 4 — Tuning, Evaluation & Security

**Goal:** Validate quality, harden security, and complete the project.

**Chunking analysis**
Three chunking strategies tested:
- v1 (original, 288 chunks): **84% coverage**
- v2 (500-char algorithmic): **24% coverage**
- v3 (1,200-char algorithmic): **13% coverage**

Finding confirmed the original chunking was optimal. v2 and v3 collections deleted.

**Knowledge base expansion (tried and reverted)**
Added 3 PDFs targeting the 12 knowledge gaps. Coverage improved from 84% → 88% (9 remaining gaps). Reverted because: the 5 remaining California excavation gaps weren't addressable with any available PDF, and adding large external documents for +4% coverage introduced maintenance burden without solving the core problem. Gaps documented as known knowledge boundaries.

**Hallucination scoring**
LLM-as-judge using Claude. Final results after prompt calibration:
- 0.0% hallucination rate
- 2.92/3.0 avg correctness
- 94.3% fully correct answers

**Prompt injection protection**
Added regex-based detection of 10 injection patterns in `api/main.py`. Returns HTTP 400 with a neutral message. All 7 test injection patterns blocked; all 4 legitimate safety questions passed.

**Conversation memory**
Added full session history to the Claude messages array. The Streamlit frontend extracts all prior turns from session state and sends them with each request. No turn cap — full conversation context preserved for the entire session.

**ChromaDB cosine distance fix**
During KB expansion revert, collection was recreated with L2 distance by default, dropping all similarity scores below the 0.50 threshold. Fixed by specifying `hnsw:space: cosine` on collection creation. Production collection restored and verified.

---

## Final Architecture Summary

| Layer | Technology | Key Design Choice |
|---|---|---|
| Vector store | ChromaDB (cosine similarity) | Page/section-based chunks preserve regulatory coherence |
| Embeddings | Sentence Transformers (default) | No external API dependency for embeddings |
| LLM | Claude claude-sonnet-4-20250514, temp=0.0 | Deterministic, instruction-following, grounded |
| Backend | FastAPI | Clean validation, rate limiting, injection detection |
| Frontend | Streamlit | Session state enables full conversation memory |
| Evaluation | 75-question ground truth + LLM judge | Quantitative basis for every decision |
