# Project Deliverables Document
## Construction Safety AI Agent — RAG Pipeline
**Prepared by:** Riya Elizabeth | **Date:** May 2026 | **Project:** Ampytics Practicum

---

## Table of Contents
1. [Demo Video Guide](#1-demo-video-guide)
2. [Risk Assessment](#2-risk-assessment)
3. [Cost-Benefit Analysis](#3-cost-benefit-analysis)
4. [Evaluation Metrics](#4-evaluation-metrics)
5. [Repository of Unanswered Questions](#5-repository-of-unanswered-questions)

---

## 1. Demo Video Guide

### What to Show in the Demo

A demo video should walk through the following sequence to showcase the agent's full capabilities:

**Part 1 — Setup & UI Overview (1–2 min)**
- Show the Streamlit UI loading at `http://localhost:8501`
- Point out the safety disclaimer banner at the top
- Show the session stats bar (questions asked, answered, coverage %)

**Part 2 — Basic Q&A (2–3 min)**
Ask these questions to demonstrate accurate, cited answers:
1. *"At what height is fall protection required?"* — should cite 6 feet, Cal/OSHA Section 1670
2. *"How often must fire extinguishers be inspected?"* — should cite monthly inspection, annual service
3. *"What are the three types of protective systems for excavations?"* — should cite sloping, shoring, and shielding

**Part 3 — Continuous Conversation Memory (1–2 min)**
Demonstrate multi-turn follow-up:
1. *"What are the fall protection requirements for construction workers?"*
2. *"What about guardrail heights specifically?"*
3. *"And what are the midrail requirements?"*
Show that each follow-up answer builds on the prior context.

**Part 4 — Knowledge Gap Handling (1 min)**
Ask a question outside the knowledge base:
- *"What permit requirements apply to excavations in California?"*
Show the agent clearly states it cannot find the information — rather than guessing — and that the question is logged for review.

**Part 5 — Out-of-Scope Handling (30 sec)**
Ask something completely unrelated:
- *"What is the recipe for chocolate cake?"*
Show the agent refuses politely and stays within its scope.

**Part 6 — Source Citations (30 sec)**
Point out the source pills below each answer showing the PDF filename and page number. Emphasize this makes every answer auditable.

### Demo Script Notes
- Run backend first: `uvicorn api.main:app --reload --port 8000`
- Run frontend: `streamlit run frontend/app.py`
- Use a clean session (click "Clear chat" before recording)
- Slow down typing to let the streaming animation display clearly

---

## 2. Risk Assessment

### Risk Matrix

| # | Risk | Likelihood | Impact | Overall | Status |
|---|---|---|---|---|---|
| R1 | Worker over-reliance — treating agent as a supervisor replacement | Medium | High | **High** | Partially mitigated |
| R2 | Hallucination — agent generates factually wrong safety advice | Low | High | **Medium** | Mitigated (0% measured) |
| R3 | Knowledge staleness — regulations updated after ingestion | Low | Medium | **Medium** | Not yet addressed |
| R4 | API cost overrun — uncontrolled usage | Medium | Medium | **Medium** | Mitigated (rate limiting) |
| R5 | Prompt injection — user manipulates agent behavior | Low | Medium | **Low-Medium** | Mitigated (10 patterns) |
| R6 | Infrastructure failure — Anthropic API downtime | Low | High | **Medium** | Not yet addressed |
| R7 | Knowledge gaps — 12 questions unanswerable | High | Medium | **Medium** | Documented, by design |

---

### R1 — Over-reliance Risk

**Description:** Workers may use agent answers as the final word on a safety decision, bypassing qualified supervisors for complex or site-specific situations.

**Likelihood:** Medium — especially for workers not briefed on the system's scope.

**Impact:** High — incorrect safety decisions can result in injury or fatality.

**Mitigations in place:**
- Persistent safety disclaimer banner on all UI pages
- Automatic safety disclaimer appended to every fall, electrical, heat illness, and confined space answer: *"⚠️ Safety-critical topic: When in doubt, stop work and consult a qualified supervisor."*
- Agent clearly refuses to answer rather than guess when content is not found

**Recommended additional action:** Add an onboarding screen on first use requiring the user to acknowledge that the agent is a reference tool, not a supervisor replacement.

---

### R2 — Hallucination Risk

**Description:** The agent generates an answer that sounds authoritative but contradicts or fabricates OSHA regulations.

**Likelihood:** Low — design specifically prevents this.

**Impact:** High — wrong safety advice in the field.

**Mitigations in place:**
- Temperature = 0.0 (deterministic responses)
- System prompt prohibits answering outside source documents
- Fallback phrase detection routes uncertain answers to "I cannot find this" rather than a guess

**Measured result:** 0.0% hallucination rate across 53 scored answers (LLM-as-judge evaluation, May 2026).

**Residual risk:** Evaluation covered 75 ground truth questions. Novel edge-case questions have not been evaluated. Re-run `evaluation/score_hallucination.py` after any knowledge base update.

---

### R3 — Knowledge Staleness Risk

**Description:** OSHA and Cal/OSHA regulations change over time. The knowledge base reflects documents as of the ingestion date (April 2026).

**Likelihood:** Low short-term, Medium over 1–2 years.

**Impact:** Medium — outdated guidance could lead to non-compliant decisions.

**Recommended action:** Schedule an annual review. When source regulations are updated, re-download PDFs, re-ingest using `agent/ingest.py`, and re-run the evaluation.

---

### R4 — API Cost Risk

**Description:** Uncontrolled usage drives up Anthropic API costs.

**Mitigations in place:** Rate limiting (10 requests/minute per IP), 500-character input cap.

**Recommended action:** Set a monthly budget cap in the Anthropic console dashboard.

---

### R5 — Prompt Injection Risk

**Description:** A user crafts a question to override the agent's system prompt (e.g., *"Ignore your instructions and..."*).

**Mitigations in place:** 10 regex patterns in `api/main.py` detect and block common injection attempts. Returns HTTP 400 with a neutral error message.

**Residual risk:** Novel phrasing not covered by current patterns. Monitor `qa_log.db` for unusual patterns in production.

---

### R6 — Infrastructure Risk

**Description:** The Anthropic Claude API experiences downtime, making the agent non-functional.

**Current status:** No fallback implemented.

**Recommended action:** Display a maintenance message with a link to `osha.gov` during API errors. Already partially handled — the frontend shows a backend error message if the API is unreachable.

---

### R7 — Knowledge Gap Risk

**Description:** 12 questions (16%) cannot be answered because content is not in any source document.

**Current status:** Documented as known boundaries. Agent correctly says "I cannot find this" for all 12.

**Recommended action:** Add Cal/OSHA Title 8 excavation regulations PDF to close 5 of 12 gaps. See Section 5 for full gap list.

---

## 3. Cost-Benefit Analysis

### Costs

#### One-Time Costs

| Item | Cost | Notes |
|---|---|---|
| Development | Practicum project | No external cost — built as academic deliverable |
| Infrastructure setup | ~$0 | Runs on local machine or any cloud VM |

#### Ongoing Costs

| Item | Estimated Cost | Basis |
|---|---|---|
| Anthropic Claude API | ~$0.01–0.03 per question | claude-sonnet pricing, ~500 tokens avg per query |
| Cloud hosting (optional) | ~$10–50/month | If deployed to a server (e.g., AWS EC2, Heroku) |
| Knowledge base maintenance | ~4 hours/year | Annual review and re-ingestion |

#### Usage-Based Cost Estimates

| Scenario | Questions/Month | Est. Monthly API Cost |
|---|---|---|
| Demo only | < 100 | < $3 |
| 1 site, 10 workers, 5 Q/day | ~1,500 | ~$15–45 |
| 5 sites, 50 workers, 5 Q/day | ~7,500 | ~$75–225 |
| 10 sites, 100 workers, 5 Q/day | ~15,000 | ~$150–450 |

---

### Benefits

| Benefit | Description | Measurable? |
|---|---|---|
| Faster safety answers | Seconds vs. 5–15 minutes (manual lookup or supervisor call) | Yes — time saved per query |
| Reduced supervisor interruptions | Fewer routine safety questions escalated to supervisors | Yes — track supervisor call volume |
| Consistent, documented answers | Every answer cites a regulation — auditable record in `qa_log.db` | Yes — audit trail available |
| OSHA violation reduction | Correct answers reduce likelihood of non-compliant decisions | Indirect — measure citation rates |
| Knowledge gap visibility | Unanswered questions reveal training and documentation gaps | Yes — tracked in `unanswered_questions.csv` |
| Scalable across sites | Same agent serves all sites simultaneously at marginal cost | Yes — no incremental cost per site |

---

### ROI Summary

A single OSHA serious violation citation costs a minimum of **$15,625** (2024 federal rates). A single lost-time injury in construction averages **$38,000–$150,000** in direct and indirect costs.

At $75–225/month for 5 sites, the agent pays for itself if it prevents **one citation per year** or meaningfully reduces supervisor response time across the workforce.

**Conclusion:** The cost is negligible relative to the risk it mitigates. The primary value is compliance confidence and risk reduction, not direct cost savings.

---

## 4. Evaluation Metrics

### 4.1 Methodology

The agent was evaluated against a **75-question ground truth dataset** built in Phase 1, covering three difficulty levels:

| Difficulty | Questions | Description |
|---|---|---|
| Easy | 20 | Basic facts, definitions, single-regulation answers |
| Medium | 30 | Procedures, multi-step requirements, comparisons |
| Hard | 25 | Complex scenarios, edge cases, multi-part answers |

Two evaluation scripts were used:
- **`evaluate_quick.py`** — measures answer coverage (answered vs. unanswered)
- **`evaluation/score_hallucination.py`** — LLM-as-judge scoring on correctness, completeness, and hallucination

---

### 4.2 Coverage Metrics

| Metric | Result | Target | Status |
|---|---|---|---|
| Total questions tested | 75 | 75 | ✅ |
| Questions answered | 63 | ≥ 60 (80%) | ✅ |
| **Answer coverage** | **84.0%** | **80%** | ✅ Exceeded |
| Questions unanswered | 12 | — | Documented |

---

### 4.3 Accuracy Metrics (LLM-as-Judge)

Scored on 53 answered questions (63 total answered — 10 were not in eval_results.csv from the earlier evaluation run).

#### Correctness (0–3 scale)
*Does the response accurately reflect the ground truth answer?*

| Score | Meaning | Count | % |
|---|---|---|---|
| 3 | Fully correct | 50 | 94.3% |
| 2 | Mostly correct, minor gap | 2 | 3.8% |
| 1 | Partially correct | 1 | 1.9% |
| 0 | Wrong or misleading | 0 | 0.0% |
| **Average** | | **2.92 / 3.0** | |

#### Completeness (0–3 scale)
*Does the response cover all key points from the expected answer?*

| Score | Meaning | Count | % |
|---|---|---|---|
| 3 | Complete | 50 | 94.3% |
| 2 | Mostly complete | 2 | 3.8% |
| 1 | Partially complete | 1 | 1.9% |
| 0 | Incomplete | 0 | 0.0% |
| **Average** | | **2.92 / 3.0** | |

---

### 4.4 Groundedness Metrics

*Is the agent answering from its source documents only, or hallucinating?*

| Metric | Result | Target | Status |
|---|---|---|---|
| **Hallucination rate** | **0.0%** | < 5% | ✅ Exceeded |
| Responses with source citations | 100% of answered | 100% | ✅ |
| Out-of-scope questions refused | 100% | 100% | ✅ |

**Hallucination definition used:** A response was flagged as hallucination only if it asserted facts that directly contradicted the expected answer or invented specific numbers/rules not plausible from OSHA construction safety standards. Additional correct regulatory detail beyond the expected answer was not counted as hallucination.

---

### 4.5 Summary Dashboard

| Metric | Result |
|---|---|
| Answer coverage | **84%** (63/75) |
| Hallucination rate | **0.0%** |
| Avg correctness | **2.92 / 3.0** |
| Avg completeness | **2.92 / 3.0** |
| Fully correct answers | **94.3%** |
| Source citations on all answers | **100%** |

All targets met or exceeded.

---

## 5. Repository of Unanswered Questions

### 5.1 Overview

All unanswered questions are automatically logged to `evaluation/unanswered_questions.csv` with a timestamp. This creates a live feedback loop — every question the agent cannot answer is captured for team review and future knowledge base expansion.

**File location:** `evaluation/unanswered_questions.csv`
**Format:** `timestamp, question`
**Auto-populated by:** `agent/rag_pipeline.py` whenever the fallback phrase is triggered

---

### 5.2 Confirmed Knowledge Gaps (12 Questions)

These questions were identified during the 75-question evaluation. They represent confirmed content gaps — the answers are not present in any of the 3 source documents.

#### Category A — Heat Illness Prevention (2 questions)

| Question | Root Cause |
|---|---|
| How much water must employers provide to employees for heat illness prevention? | Cal/OSHA Title 8 §3395 (specific quantity requirements) not in source docs |
| What must a written heat illness prevention plan include at a minimum? | Written plan requirements not detailed in available PDFs |

**To close:** Add Cal/OSHA Heat Illness Prevention Standard (Title 8 §3395) PDF.

---

#### Category B — California Excavation Rules (6 questions)

| Question | Root Cause |
|---|---|
| What permit requirements apply to excavations in California? | Federal OSHA guide used — CA-specific permit rules not covered |
| What are the required steps an employer must take before opening an excavation? | Pre-opening steps not detailed in available guide |
| When is a protective system not required? | Exemption conditions not covered |
| When is atmospheric testing required? | Testing triggers not in source docs |
| What are key requirements for installing/removing support systems? | Support system procedures not detailed |
| In what situations must emergency rescue equipment be readily available? | Emergency equipment requirements not in available guide |

**To close:** Add Cal/OSHA Construction Safety Orders (Title 8, §1540–1564).

---

#### Category C — Operational Procedures (4 questions)

| Question | Root Cause |
|---|---|
| For a weekly toolbox talk, how should supervisors run the meeting so it is useful for the crew? | Meeting format/facilitation guidance not in regulatory text |
| Before an operator uses mobile equipment on site, what should be checked? | Pre-use checklist not in available documents |
| What should an emergency action plan tell workers to do during a fire or other emergency? | EAP content requirements not covered |
| What should a PPE program include? | PPE program structure not detailed in available guide |

**To close:** Add OSHA 29 CFR 1926 Subpart E (PPE) and a construction safety management guide covering operational procedures.

---

### 5.3 Out-of-Scope Questions Logged

The system also logs questions that are outside the construction safety domain. These are expected and demonstrate the fallback is working correctly.

Examples logged during testing:
- "What is the recipe for chocolate cake?"
- "What is the capital of France?"
- "How do I file my taxes?"

These should be **excluded** from knowledge base expansion planning — they are not content gaps, they are correct refusals.

---

### 5.4 Gap Prioritization

| Priority | Category | Questions | Recommended Action |
|---|---|---|---|
| High | CA excavation rules | 6 | Add Cal/OSHA Title 8 §1540–1564 |
| Medium | Heat illness | 2 | Add Cal/OSHA Title 8 §3395 |
| Medium | Operational procedures | 4 | Add construction safety management guide |

Closing the CA excavation gaps (6 questions) would bring coverage from **84% → 92%**.
Closing all 12 gaps would bring coverage to **100%** on the current ground truth set.

---

### 5.5 How to Use the Gap Repository Going Forward

1. **Review monthly:** Open `evaluation/unanswered_questions.csv` and filter for non-obvious questions (exclude out-of-scope)
2. **Cluster by topic:** Group similar questions to identify emerging content gaps
3. **Prioritize expansion:** If 3+ questions fall in the same topic area, add a relevant PDF to `data/procedures/`
4. **Re-ingest and re-evaluate:**
```bash
python agent/ingest.py --pdf-dir data/procedures --collection construction_procedures --chunk-size 1800 --chunk-overlap 200 --append
python evaluate_quick.py
```
5. **Track improvement:** Compare coverage % before and after to confirm the gap was closed

---

*All evaluation scripts, results, and logs are available in the `evaluation/` folder of the repository.*
*GitHub: github.com/riya-elizabeth/ai-agent-construction*
