# Construction Safety AI Agent
## Stakeholder Presentation
**Ampytics Practicum | May 2026**

---

## Slide 1 — The Problem

### Workers need safety answers fast. The current process is too slow.

On a construction job site, a worker faces a safety question:
- *"Do I need fall protection at this height?"*
- *"Is this trench deep enough to need a protective system?"*
- *"What PPE is required for this task?"*

**What happens today:**
- Search through a physical safety manual
- Wait for a supervisor to be available
- Call the safety officer — who may be on another site

**The risk:** Delays lead to shortcuts. Shortcuts lead to incidents.

**OSHA reports over 1,000 construction fatalities per year in the US — the highest of any industry.**

---

## Slide 2 — Our Solution

### An AI assistant that gives workers instant, cited safety answers

> *"At what height is fall protection required?"*
>
> **Agent:** *"Fall protection is required at 6 feet or more above a lower level, per Cal/OSHA Section 1670. The standard sets a uniform threshold height of 6 feet, meaning employees must be protected from fall hazards whenever on a walking/working surface 6 feet or more above a lower level. ⚠️ Safety-critical topic: When in doubt, stop work and consult a qualified supervisor."*

**Key principle:** The agent only answers from verified OSHA documents. It never guesses.

---

## Slide 3 — How It Works

```
Worker types a question
         ↓
Security check (validates input, blocks manipulation attempts)
         ↓
AI searches 288 indexed sections of OSHA documents
         ↓
Claude AI generates a grounded answer with regulation citations
         ↓
Answer delivered in seconds — with source document and page number
         ↓
If answer not found → worker is told clearly, question logged for review
```

**The knowledge base:** 3 verified OSHA/Cal-OSHA documents, chunked into 288 searchable sections.

---

## Slide 4 — What Makes This Different

| Traditional Chatbot | This Agent |
|---|---|
| May hallucinate answers | **0% hallucination rate** |
| No source citations | **Every answer cites a regulation** |
| No memory between questions | **Full conversation memory** |
| Single question only | **Multi-turn follow-up supported** |
| No safety guardrails | **Automatic safety disclaimers** |
| No gap detection | **Unknown questions logged for review** |

---

## Slide 5 — Results

### Tested against 75 real construction safety questions

| Metric | Result | Target |
|---|---|---|
| **Answer coverage** | **84%** (63/75 questions) | 80% |
| **Hallucination rate** | **0.0%** | < 5% |
| **Answer accuracy** | **2.92 / 3.0** | 2.5 / 3.0 |
| **Fully correct answers** | **94.3%** | 85% |

**Every target was met or exceeded.**

The 16% of questions not answered (12 questions) are confirmed content gaps — topics not covered in any of the 3 source documents. The agent correctly identifies these and tells the worker rather than guessing.

---

## Slide 6 — Question Difficulty Breakdown

The 75 test questions were designed across 3 difficulty levels:

| Difficulty | Questions | Examples |
|---|---|---|
| Easy | 20 | "At what height is fall protection required?" |
| Medium | 30 | "What are the three methods to prevent cave-ins?" |
| Hard | 25 | "What fall protection requirements apply to roofs with slopes greater than 4:12?" |

The agent performed consistently across all difficulty levels.

---

## Slide 7 — Security & Safety Built In

The agent is designed for a safety-critical environment:

**Prevents misuse:**
- Rate limiting — max 10 questions/minute per user (prevents cost abuse)
- Input validation — questions must be 1–500 characters
- Prompt injection protection — blocks attempts to manipulate the AI

**Prevents wrong answers:**
- Answers grounded in documents only — no outside knowledge
- Automatic safety disclaimers for falls, electrical, heat illness, confined spaces
- Clear fallback message when answer not found — never a guess
- All unanswered questions logged for team lead review

---

## Slide 8 — The Knowledge Base

### 3 verified source documents, 288 indexed sections

| Document | Key Topics |
|---|---|
| Cal/OSHA Pocket Guide (2022) | Fall protection, heat illness, PPE, electrical, scaffolding, confined spaces |
| OSHA Construction Safety Manual | Company rules, hazard communication, fire prevention, equipment safety |
| OSHA Trenching & Excavation Guide | Excavation hazards, soil classification, protective systems, cave-in prevention |

**The agent knows exactly what it knows — and exactly what it doesn't.**

---

## Slide 9 — Known Gaps (Honest Assessment)

12 questions (16%) cannot currently be answered. These are not failures — they are honest boundaries.

| Gap Area | Questions Affected |
|---|---|
| Heat illness specifics | Water quantity requirements, written prevention plan |
| California excavation rules | Permit requirements, atmospheric testing, support systems |
| Operational procedures | Toolbox talks, PPE program structure, emergency action plans |

**These gaps are documented and prioritized for future expansion.**

To close them: add the relevant Cal/OSHA PDF documents to the knowledge base and re-ingest. The infrastructure to do this is already built (`agent/ingest.py --append`).

---

## Slide 10 — Technology Stack

| Layer | Technology | Why |
|---|---|---|
| AI Model | Anthropic Claude (claude-sonnet) | Best-in-class instruction following, stays grounded |
| Vector Database | ChromaDB | Persistent, fast semantic search, no external API |
| Backend | FastAPI | Fast, secure, automatic input validation |
| Frontend | Streamlit | Rapid UI, works on any browser |
| Evaluation | Custom 75-Q pipeline + LLM judge | Quantitative, repeatable, defensible |

**Total cost per question:** ~$0.01–0.03 (Claude API usage)

---

## Slide 11 — How to Deploy

The system is ready to run. Any team member with Python can set it up in under 10 minutes:

1. Clone the GitHub repository
2. Install dependencies (`pip install -r requirements.txt`)
3. Add an Anthropic API key to `.env`
4. Start the backend: `uvicorn api.main:app --reload`
5. Start the frontend: `streamlit run frontend/app.py`

The knowledge base (vector store) is included in the repository — no re-processing of documents needed.

Full setup guide: `docs/technical_guide.md`
Full handover guide: `docs/handover.md`

---

## Slide 12 — Roadmap

### What's been delivered (Phase 4 complete)

- ✅ Working agent with 84% coverage and 0% hallucination
- ✅ Continuous conversation memory
- ✅ Security hardening
- ✅ Full evaluation framework and scored results
- ✅ Complete documentation and handover package

### Potential next steps (future phases)

| Priority | Enhancement | Impact |
|---|---|---|
| High | Add Cal/OSHA excavation PDF | Close 5 of 12 remaining gaps |
| High | Query rewriting for follow-ups | Improve pronoun resolution ("what about that?") |
| Medium | Mobile-optimized UI | Better field usability on phones |
| Medium | Multi-language support | Serve non-English speaking workers |
| Low | Offline mode | Works without internet on job site |

---

## Slide 13 — Summary

### What we built
A production-ready AI safety assistant grounded in verified OSHA regulations.

### What it does
Answers construction safety questions instantly, with citations, at 0% hallucination.

### Why it matters
Workers get correct answers in seconds instead of minutes — reducing the risk of safety shortcuts under time pressure.

### What's next
The infrastructure is built. Expanding the knowledge base and improving the UI are the highest-value next steps.

---

*Built by Riya | Ampytics Practicum | MSBA AI/ML Portfolio*
*GitHub: github.com/riya-elizabeth/ai-agent-construction*
