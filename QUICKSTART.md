# Quickstart
## Construction Safety AI Agent

**What this is:** A RAG chatbot that answers OSHA construction safety questions, grounded in verified documents. It never guesses — if the answer isn't in the knowledge base, it says so.

**Performance:** 84% question coverage | 0% hallucination rate | 2.92/3.0 correctness

---

## Prerequisites

- Python 3.10+
- An Anthropic API key — get one free at [console.anthropic.com](https://console.anthropic.com)
- ~500MB disk space

---

## Setup and Run

```bash
# 1. Clone and enter the repo
git clone https://github.com/riya-elizabeth/ai-agent-construction.git
cd ai-agent-construction

# 2. Add your API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# 3. Start everything
./start.sh
```

`start.sh` handles the virtual environment, installs dependencies, starts the backend, and opens the chat UI — all in one step. Browser opens at `http://localhost:8501`. Press Ctrl+C to stop.

> **Windows users:** Run the manual steps below instead — `start.sh` requires bash.

<details>
<summary>Manual setup (Windows or if start.sh fails)</summary>

```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
cp .env.example .env
# Open .env and set: ANTHROPIC_API_KEY=your-key-here
```

Then open two terminals (venv activated in both):

```bash
# Terminal 1 — Backend
uvicorn api.main:app --port 8000

# Terminal 2 — Frontend
streamlit run frontend/app.py
```
</details>

---

## Verify it's working

Ask: *"At what height is fall protection required?"*

You should get a cited answer referencing a specific regulation section within a few seconds.

---

## Common operations

```bash
# Run the 75-question evaluation
python evaluate_quick.py

# Add a new PDF to the knowledge base
# 1. Drop the PDF into data/procedures/
# 2. Run:
python agent/ingest.py --pdf-dir data/procedures --collection construction_procedures \
  --chunk-size 1800 --chunk-overlap 200 --append
# 3. Re-evaluate:
python evaluate_quick.py

# Score for hallucination (LLM-as-judge)
python evaluation/score_hallucination.py
```

---

## Deeper documentation

| Need | File |
|---|---|
| Step-by-step setup with context | `docs/handover.md` |
| Architecture and config parameters | `docs/technical_guide.md` |
| Build this from scratch | `docs/REPLICATION_GUIDE.md` |
| Known limitations and gaps | `model_limitations.md` |
| Experiment results and tuning decisions | `docs/tuning_log.md` |
