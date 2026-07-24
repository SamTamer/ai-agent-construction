# Model Limitations
## Construction Safety AI Agent — RAG Pipeline
*Documented: April 21, 2026*

---

## Overview

The agent achieved **84% coverage (63/75 questions)** in evaluation testing. The 16% gap and all known limitations are documented below — categorized by type to support Phase 4 tuning and risk reporting.

**Chunking analysis (Phase 4):** Three chunking strategies were tested against the same 75-question ground truth. The original page/section-based chunks (288 chunks, ~1,880 chars avg) outperformed algorithmic splits at 500 chars (24% coverage) and 1,200 chars (13% coverage). The original chunking is optimal for this dense regulatory corpus and was retained.

---

## 1. Knowledge Scope Limitations

**The agent only knows what is in the source documents.**

The knowledge base consists of three documents:
- Cal/OSHA Pocket Guide for the Construction Industry (2022 Edition)
- OSHA Construction Safety Manual
- OSHA Trenching & Excavation Safety Guide

It has no awareness of:
- California-specific excavation permit requirements (Title 8, §1540-1564)
- Company-specific internal safety rules or site procedures
- Regulations updated after the ingestion date
- Topics not covered in the source documents

---

## 2. Coverage Gap — 16% Unanswered Questions (Known Knowledge Gaps)

From the 75-question evaluation, **12 questions (16%) were flagged as unanswered**. These are confirmed knowledge gaps — the content does not exist in any of the 3 source documents. They fall into three patterns:

### Pattern A — Heat illness specifics
- How much water must employers provide for heat illness prevention?
- What must a written heat illness prevention plan include at a minimum?

### Pattern B — California-specific excavation rules
- What permit requirements apply to excavations in California?
- What are the required steps before opening an excavation?
- When is a protective system not required?
- When is atmospheric testing required?
- What are the key requirements for installing/removing support systems?
- In what situations must emergency rescue equipment be readily available?

### Pattern C — Operational procedures
- How should supervisors run a weekly toolbox talk?
- What makes a space a confined space?
- What should be checked before an operator uses mobile equipment?
- What should a PPE program include?

**Root cause:** Confirmed content gaps — not retrieval or chunking failures. The agent correctly retrieved related chunks but the specific answers were not present in any source document. These questions are intentionally left unanswered rather than risk hallucination.

---

## 3. No Conversation Memory

The agent is **stateless** — each question is processed independently with no memory of prior questions in the same session.

**Impact:** Follow-up questions like *"What about for roofs specifically?"* or *"Can you clarify that last point?"* will not carry context from the previous answer. Users must re-state context in every question.

**Planned fix:** Evaluate stateful conversation memory in Phase 4. May increase API token costs.

---

## 4. No Input Validation / Prompt Injection Protection

There is currently **no protection against adversarial or malicious inputs**. A user could potentially craft a query designed to manipulate the agent's behavior or bypass its instructions.

**Impact:** Risk of prompt injection in a production environment.

**Planned fix:** Add input sanitization and validation layer to the FastAPI backend in Phase 4.

---

## 5. Retrieval Confidence Thresholding is Incomplete

The agent does not fully distinguish between high-confidence retrieval (similarity score ~0.72) and low-confidence retrieval (similarity score ~0.50). Both may produce a response rather than a fallback.

**Impact:** Some answers may be generated from loosely relevant chunks, increasing hallucination risk on borderline queries.

**Planned fix:** Implement a stricter confidence threshold gate — if the top retrieved chunk scores below 0.55, route to the unanswered fallback.

---

## 6. Chunking Boundary Gaps

The 288 chunks were created with overlap, but some answers that span multiple sections of a document may be split across chunk boundaries. When this happens, the agent may only retrieve part of the relevant content.

**Impact:** Incomplete answers on questions that require reading across two consecutive sections.

**Planned fix:** Increase chunk overlap from 800 to 1000 characters and re-evaluate retrieval in Phase 4.

---

## 7. No Rate Limiting on the Backend

The FastAPI `/ask` endpoint has **no rate limiting** in place. During evaluation runs or live demos, excessive queries can drive up Claude API costs unexpectedly.

**Impact:** Cost overrun risk during Phase 4 automated evaluation.

**Planned fix:** Add per-minute rate limiting to the FastAPI backend before running the full automated evaluation.

---

## 8. No Persistent Frontend Safety Disclaimer

Safety-critical disclaimers are hardcoded into the system prompt and appear in responses. However, there is **no persistent visual warning banner** on the Streamlit UI reminding users that the agent does not replace a qualified supervisor.

**Impact:** Users may not see the disclaimer if they skip to the answer text directly.

**Planned fix:** Add a static disclaimer banner to the top of the Streamlit UI (Docs & Demo Lead).

---

## 9. Static Knowledge Base — No Live Updates

The knowledge base reflects the documents ingested at setup. If OSHA publishes regulation updates or the team adds new procedure documents, a **full re-ingestion** is required — there is no live update mechanism.

**Impact:** The agent will become outdated as regulations change over time.

**Planned fix:** Document the re-ingestion process in the technical guide (Phase 5) so future teams can update the knowledge base.

---

## 10. Hallucination Rate Not Yet Formally Measured

Coverage (84%) has been measured from the evaluation run. However, **hallucination rate has not yet been formally scored** — this requires manual review of each of the 63 answered responses against the ground truth.

**Target:** < 5% hallucination rate (Phase 4 goal).

**Next step:** Run `evaluation/evaluate.py`, manually score each response for hallucination (yes/no), and compute the aggregate rate.

---

## Summary Table

| # | Limitation | Severity | Status | Fix Phase |
|---|---|---|---|---|
| 1 | Knowledge limited to 2 source docs | Medium | By design | — |
| 2 | 16% unanswered questions | High | Documented & categorized | Phase 4 |
| 3 | No conversation memory | Medium | Known gap | Phase 4 (optional) |
| 4 | No input validation / prompt injection | High | Not implemented | Phase 4 |
| 5 | Incomplete confidence thresholding | Medium | Partial | Phase 4 |
| 6 | Chunking boundary gaps | Medium | Known gap | Phase 4 |
| 7 | No rate limiting on backend | Medium | Not implemented | Phase 4 |
| 8 | No frontend safety disclaimer banner | Low | Not implemented | Phase 4 |
| 9 | Static knowledge base | Low | By design | Phase 5 (docs) |
| 10 | Hallucination rate not yet measured | High | Pending Phase 4 eval | Phase 4 |

---

## What This Means for the Presentation

The 16% gap and limitations above are **known, categorized, and on the roadmap** — not unknown failures. The agent's 84% coverage on a first build is a strong result, and every limitation has a documented fix path in Phase 4.
