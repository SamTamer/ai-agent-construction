# Handover Document
## Construction Safety AI Agent
**Prepared by:** Riya | **Date:** May 2026 | **Project:** Ampytics Practicum

---

## What This Project Is

An AI chatbot that answers OSHA construction safety questions. Workers on job sites can type a question in plain English and get a cited, regulation-grounded answer — or a clear message if the answer isn't in the knowledge base.

**It does not guess.** If the answer isn't in the source documents, it says so. This was a deliberate design choice to prevent the agent from giving wrong safety advice.

---

## What's Been Built

| Component | What It Does |
|---|---|
| AI Agent | Answers construction safety questions using OSHA documents |
| Knowledge Base | 288 indexed chunks from 3 OSHA/Cal-OSHA PDFs |
| Backend API | Handles requests, rate limiting, and security |
| Chat UI | Web interface where users type questions and get answers |
| Evaluation | 75-question test set with scored results |

---

## How Well Does It Work?

| Metric | Result | What It Means |
|---|---|---|
| Coverage | **84%** (63/75 questions) | Answers 84% of typical safety questions |
| Hallucination rate | **0%** | Never makes up or contradicts OSHA regulations |
| Correctness | **2.92 / 3.0** | Answers that are given are highly accurate |
| Unanswered | 12 questions | Known gaps — content not in any source document |

The 12 unanswered questions are **not bugs** — they are topics not covered in the 3 source PDFs. They are documented in `model_limitations.md`.

---

## Getting Started (Step by Step)

### What You Need
- A computer with Python 3.10 or newer
- An Anthropic API key (free to create at [console.anthropic.com](https://console.anthropic.com))
- Internet connection (for the Claude API calls)

### Step 1 — Get the code
```bash
git clone https://github.com/riya-elizabeth/ai-agent-construction.git
cd ai-agent-construction
```

### Step 2 — Set up Python environment
```bash
python3 -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### Step 3 — Add your API key
Create a file called `.env` in the project root:
```
ANTHROPIC_API_KEY=your-key-here
```
Replace `your-key-here` with your actual Anthropic API key.

> ⚠️ Never share this key or commit it to git. It bills your account for every question asked.

### Step 4 — Start the backend (Terminal 1)
```bash
uvicorn api.main:app --reload --port 8000
```
You should see: `Uvicorn running on http://127.0.0.1:8000`

### Step 5 — Start the chat UI (Terminal 2)
```bash
streamlit run frontend/app.py
```
Your browser will open automatically at `http://localhost:8501`.

### Step 6 — Test it
Try asking: *"At what height is fall protection required?"*
You should get a cited answer within a few seconds.

---

## What's Inside the Repo

```
ai-agent-construction/
│
├── agent/
│   ├── rag_pipeline.py       ← Core AI logic (retrieval + Claude API)
│   ├── ingest.py             ← Tool to add new PDFs to the knowledge base
│   └── system_prompt.txt     ← Rules that control how the AI behaves
│
├── api/
│   └── main.py               ← Backend server (security, rate limiting)
│
├── frontend/
│   └── app.py                ← The chat interface
│
├── evaluation/
│   ├── ground_truth.csv      ← 75 test questions with expected answers
│   ├── eval_results.csv      ← Full scored evaluation results
│   └── unanswered_questions.csv  ← Questions the agent couldn't answer
│
├── chroma_db/                ← The knowledge base (vector database)
├── data/procedures/          ← The 3 source OSHA PDF documents
│
├── docs/
│   ├── handover.md           ← This document
│   ├── technical_guide.md    ← Detailed technical setup guide
│   ├── model_limitations.md  ← Known gaps and limitations
│   ├── tuning_log.md         ← Experiments done and decisions made
│   ├── retrospective.md      ← What went well and lessons learned
│   └── creation_process.md   ← Full phase-by-phase decision log
│
├── .env.example              ← Template for your .env file
├── requirements.txt          ← Python packages needed
└── README.md                 ← Project overview
```

---

## The 3 Source Documents

The agent only knows what's in these PDFs (in `data/procedures/`):

1. **Cal/OSHA Pocket Guide for the Construction Industry** (2022) — covers fall protection, heat illness, scaffolding, PPE, electrical, confined spaces
2. **OSHA Construction Safety Manual** — covers company safety rules, hazard communication, fire prevention, equipment
3. **OSHA Trenching & Excavation Safety Guide** — covers excavation hazards, soil classification, protective systems

If someone asks about a topic not in these documents, the agent will say it can't find the information and log the question for review.

---

## Known Limitations

These 12 questions cannot be answered because the content is not in any source document. This is by design — the agent will not guess.

| Topic | Specific Gaps |
|---|---|
| Heat illness | Water quantity requirements, written prevention plan details |
| California excavation | Permit requirements, pre-opening steps, atmospheric testing, support system rules, emergency rescue equipment |
| Operational | Toolbox talk format, mobile equipment checks, emergency action plan, PPE program components |

To close these gaps in the future, add relevant PDFs to `data/procedures/` and re-ingest (see Adding New Documents below).

---

## Security Features Built In

- **Rate limiting** — max 10 requests per minute per user (prevents API cost abuse)
- **Input validation** — questions must be between 1–500 characters
- **Prompt injection protection** — detects and blocks attempts to manipulate the AI (e.g. "ignore previous instructions")

---

## Ongoing Costs

Every question asked to the agent uses the Claude API, which costs money.

| Usage | Estimated Cost |
|---|---|
| 1 question | ~$0.01–0.03 |
| 100 questions/day | ~$1–3/day |
| Demo session (20 questions) | ~$0.20–0.60 |

Costs depend on response length. Monitor usage at [console.anthropic.com](https://console.anthropic.com).

---

## Adding New Documents (Future Expansion)

To add new PDFs to the knowledge base:

1. Drop the PDF into `data/procedures/`
2. Run:
```bash
python agent/ingest.py \
  --pdf-dir data/procedures \
  --collection construction_procedures \
  --chunk-size 1800 \
  --chunk-overlap 200 \
  --append
```
3. Re-run the evaluation to check if coverage improved:
```bash
python evaluate_quick.py
```

> ⚠️ Do not change `--chunk-size` below 1000. Smaller chunks significantly reduce answer quality (tested — 500-char chunks dropped coverage from 84% to 24%).

---

## Running the Evaluation

To check how well the agent is performing against the 75-question test set:
```bash
python evaluate_quick.py
```
Results print to the terminal and save to `evaluation/quick_results.json`.

---

## Who to Contact

For questions about the project, the design decisions behind it, or the evaluation methodology — refer to:
- `docs/creation_process.md` — full decision log
- `docs/retrospective.md` — lessons learned
- `docs/tuning_log.md` — experiment results

All design decisions are documented so future teams can understand the reasoning, not just the outcome.
