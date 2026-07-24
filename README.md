# Construction Safety AI Agent — RAG Pipeline

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)
![Claude API](https://img.shields.io/badge/Anthropic_Claude_API-CC785C?style=flat&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-6E40C9?style=flat)
![Status](https://img.shields.io/badge/Phase_4-Complete-brightgreen)

> **An agentic AI assistant that answers construction safety and OSHA compliance questions in real time — grounded entirely in verified source documents.**

---

## Results

| Metric | Value |
|---|---|
| **Question coverage** | **84% (63 / 75 questions answered)** |
| **Hallucination rate** | **0.0%** |
| **Avg correctness** | **2.92 / 3.0** |
| Fully correct answers (score 3) | 94.3% of answered questions |
| Confidence threshold | 0.55 (below = routed to fallback) |
| Knowledge base | 288 chunks from 3 OSHA documents |
| Unanswered questions | 12 — confirmed knowledge gaps, logged for review |

---

## Problem Statement

Construction workers on job sites need fast, accurate answers to safety and OSHA compliance questions — often in high-pressure situations where consulting a manual or waiting for a supervisor is not practical.

**This project builds a RAG (Retrieval-Augmented Generation) AI agent** that:
- Answers safety questions grounded exclusively in Cal/OSHA and OSHA source documents
- Cites the specific regulation or section number in every answer
- Flags unanswered questions for human review instead of hallucinating
- Adds automatic safety disclaimers for critical topics (falls, electrical, confined spaces, heat)

---

## Architecture

```
User Question
     │
     ▼
FastAPI Backend (/ask endpoint)
     │   ├── Input validation & rate limiting
     │
     ▼
RAG Pipeline
     │   ├── Query → ChromaDB vector store
     │   ├── Retrieve top-k chunks (similarity scored)
     │   ├── Confidence threshold check (≥ 0.55 to answer)
     │
     ▼
Claude API (Anthropic)
     │   ├── System prompt: OSHA safety assistant rules
     │   ├── Context: retrieved document chunks
     │   └── Answer with regulation citations
     │
     ▼
Response → User
     └── If unanswered: logged to CSV for team lead review
```

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Anthropic Claude API |
| Vector Database | ChromaDB |
| Embeddings | Sentence Transformers |
| Backend | FastAPI |
| Frontend | Streamlit |
| Evaluation | Custom 75-question ground truth pipeline + LLM-as-judge scoring |
| Language | Python 3.10 |

---

## Knowledge Base

The agent's knowledge is grounded in three verified OSHA documents:
- **Cal/OSHA Pocket Guide for the Construction Industry** (2022 Edition)
- **OSHA Construction Safety Manual**
- **OSHA Trenching & Excavation Safety Guide**

Chunked into **288 segments** using page/section-based splitting optimised for this corpus. No outside knowledge is used — the agent is explicitly prohibited from answering beyond its source documents.

**Chunking analysis:** Three strategies were tested (288 page-based chunks, 1,101 chunks at 500 chars, 497 chunks at 1,200 chars). The original page/section-based chunking at ~1,880 char avg achieved 84% coverage vs 24% and 13% for the algorithmic alternatives — larger semantically coherent chunks produce stronger embeddings for dense regulatory text.

---

## Key Features

**Source-grounded answers only**
Every response cites the specific regulation number or section. If the answer isn't in the documents, the agent says so — it does not hallucinate.

**Confidence thresholding**
Retrieval similarity scores below 0.55 are routed to a fallback response. Borderline retrievals do not produce low-confidence answers.

**Automatic fallback logging**
Unanswered questions are automatically logged to `evaluation/unanswered_questions.csv` for team lead review — building a feedback loop for future knowledge base expansion.

**Safety-critical disclaimers**
Questions about fall protection, electrical hazards, confined spaces, and heat illness automatically append: *"⚠️ Safety-critical topic: When in doubt, stop work and consult a qualified supervisor."*

**Rate limiting & input validation**
The FastAPI backend includes per-minute rate limiting and input sanitization to protect against misuse.

---

## Evaluation

### Coverage
Run the 75-question evaluation pipeline:
```bash
python evaluate_quick.py
# Compare collections: python evaluate_quick.py --collection construction_procedures_v2
```

### Hallucination Scoring
LLM-as-judge scoring using Claude on correctness (0–3), completeness (0–3), and hallucination (yes/no):
```bash
python evaluation/score_hallucination.py
```

Results are saved to `evaluation/eval_results.csv`.

### Final Metrics (Phase 4)

| Metric | Result |
|---|---|
| Coverage | 84% (63/75) |
| Hallucination rate | **0.0%** |
| Avg correctness | **2.92 / 3.0** |
| Correctness = 3 | 50/53 answered questions (94.3%) |
| Correctness ≤ 1 | 1/53 (1.9%) |
| Unanswered (knowledge gaps) | 12 questions across 3 topic areas |

---

## Known Limitations

The 16% unanswered rate (12 questions) represents confirmed **knowledge gaps** — content not present in any of the 3 source documents. They fall into three patterns:

- **Heat illness specifics** — water quantity requirements, written prevention plan details
- **California excavation rules** — permit requirements, atmospheric testing, support system details
- **Operational procedures** — toolbox talk format, PPE program components, mobile equipment checks

These questions are intentionally left unanswered rather than risk hallucination. See [`model_limitations.md`](model_limitations.md) for the full gap analysis.

---

## Project Structure

```
ai-agent-construction/
├── agent/
│   ├── rag_pipeline.py        # Core RAG logic — retrieval + Claude API call
│   ├── ingest.py              # PDF ingestion & ChromaDB loading
│   └── system_prompt.txt      # Agent behavior rules and constraints
├── api/
│   └── main.py                # FastAPI backend — validation, rate limiting, injection protection
├── frontend/
│   └── app.py                 # Streamlit chat UI with conversation memory
├── evaluation/
│   ├── ground_truth.csv       # 75-question ground truth Q&A set
│   ├── eval_results.csv       # Full evaluation results with hallucination scores
│   ├── evaluate.py            # Full batch evaluation pipeline
│   ├── score_hallucination.py # LLM-as-judge hallucination scoring
│   └── unanswered_questions.csv  # Auto-logged knowledge gaps
├── data/
│   └── procedures/            # Source OSHA PDF documents
├── chroma_db/                 # ChromaDB vector store (288 chunks, pre-built)
├── docs/
│   ├── handover.md            # Handover guide for new teams
│   ├── technical_guide.md     # Setup and architecture reference
│   ├── stakeholder_presentation.md  # 13-slide stakeholder deck
│   ├── risk_cba_report.md     # Limitations, risks & recommendations
│   ├── tuning_log.md          # Experiment results and decisions
│   ├── retrospective.md       # Lessons learned
│   ├── creation_process.md    # Phase-by-phase decision log
│   └── model_limitations.md  # Known gaps (also at root)
├── evaluate_quick.py          # Quick 75-question coverage evaluation
├── model_limitations.md       # Known gaps and knowledge boundaries
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
└── README.md
```

---

## Setup

**1. Clone the repo and install dependencies**
```bash
git clone https://github.com/riya-elizabeth/ai-agent-construction.git
cd ai-agent-construction
pip install -r requirements.txt
```

**2. Set up environment variables**
```bash
cp .env.example .env
# Add your Anthropic API key to .env
```

**3. Run the FastAPI backend**
```bash
uvicorn api.main:app --reload
```

**4. Run the Streamlit frontend**
```bash
streamlit run frontend/app.py
```

---

## Project Summary

### The Problem
Construction workers on job sites need fast, accurate answers to OSHA safety questions — in high-pressure situations where looking something up or waiting for a supervisor isn't practical. Getting the wrong answer on a safety question can be dangerous.

### The Solution
A RAG AI agent that searches verified OSHA documents and returns cited, regulation-grounded answers — or clearly says it doesn't know rather than guessing.

### Key Decisions & Why They Matter

**Grounding over hallucination**
The agent is strictly prohibited from answering outside its source documents. This produced the 0% hallucination rate — critical for a safety application.

**Original chunking was optimal**
Three chunking strategies were tested. The original page/section-based 288 chunks (84% coverage) outperformed algorithmic splits at 500 chars (24%) and 1,200 chars (13%). Dense regulatory text needs semantically coherent chunks, not character-count splits.

**Document the gaps, don't paper over them**
12 questions are genuinely unanswered. Rather than expanding the knowledge base to reach 88%, the decision was made to clearly document these as known content boundaries — a more honest and maintainable position.

**Full conversation memory**
The agent passes the entire session history to Claude on every turn, enabling natural multi-turn follow-up questions within a session.

### Phase Summary

| Phase | What Was Done | Outcome |
|---|---|---|
| Phase 1 | Project setup, 75-question ground truth dataset | Evaluation framework ready |
| Phase 2 | PDF ingestion, 288-chunk knowledge base | ChromaDB vector store built |
| Phase 3 | RAG pipeline, FastAPI backend, Streamlit UI | Working agent, 84% coverage |
| Phase 4 | Chunking analysis, hallucination scoring, security hardening, conversation memory, full documentation | 0% hallucination, production-ready |

### The Bottom Line
A production-quality RAG agent that answers construction safety questions with **zero hallucination** and **94% accuracy** on the questions it answers. The 16% it doesn't answer are known content gaps — it tells you honestly rather than making something up. For a safety-critical application, that's the right tradeoff.

---

## Context

Built as part of the **Ampytics Practicum** — an applied AI project for a construction industry client. The agent is designed to be deployed on job sites where workers need immediate, reliable access to OSHA safety guidance.

---

*Part of my MSBA AI/ML Portfolio · [GitHub](https://github.com/riya-elizabeth)*
