# Tuning Log
## Construction Safety AI Agent — Phase 4 Experiments

*Documented: May 2026*

---

## Experiment 1 — Chunking Strategy Comparison

**Objective:** Determine whether the original 288 page/section-based chunks should be replaced with algorithmically smaller chunks for improved retrieval precision.

**Hypothesis:** Smaller chunks (~500 chars) with overlap produce stronger, more focused embeddings and improve answer coverage.

**Setup:**
- Same 3 source PDFs across all experiments
- Same 75-question ground truth evaluation set
- Same RAG pipeline, similarity threshold (0.50), and top_k (5)
- Metric: answer coverage % (questions answered / 75)

### Results

| Version | Strategy | Chunk Size (avg) | Overlap | Total Chunks | Coverage |
|---|---|---|---|---|---|
| v1 (original) | Page/section-based | ~1,880 chars | None | 288 | **84%** |
| v2 | Recursive text splitter | 500 chars | 100 chars | 1,101 | 24% |
| v3 | Recursive text splitter | 1,200 chars | 200 chars | 497 | 13% |

**Finding:** v1 dramatically outperforms algorithmic chunking. v3 performed worse than v2 despite larger chunks — suggesting the recursive splitter cuts mid-section regardless of size, producing incoherent fragments.

**Root cause analysis:** Dense regulatory text (OSHA procedures, Cal/OSHA sections) benefits from chunks that map to complete semantic units (pages, sections). Algorithmic splitting at character boundaries breaks regulatory language mid-rule, weakening embeddings. A chunk like *"must provide water at"* embeds poorly; a full section on heat illness prevention embeds strongly.

**Decision:** Retain v1 (288 chunks). v2 and v3 ChromaDB collections deleted.

---

## Experiment 2 — Knowledge Base Expansion

**Objective:** Close the 16% coverage gap (12 unanswered questions) by adding targeted PDFs covering missing topics.

**Documents added (temporarily):**
- Cal/OSHA Heat Illness Prevention Regulation Amendments (15 pages, 28 chunks)
- OSHA PPE Guide OSHA3151 (46 pages, 58 chunks)
- OSHA Confined Spaces Workbook (105 pages, 147 chunks)

**Method:** Appended to existing v1 collection using `--append` flag in `ingest.py`. Total chunks: 521.

**Results:**

| | Before | After |
|---|---|---|
| Coverage | 84% (63/75) | 88% (66/75) |
| Unanswered | 12 | 9 |

**Remaining 9 unanswered after expansion:**
- California excavation permit requirements (5 questions) — not in any added PDF
- Operational procedures (toolbox talks, mobile equipment, EAP, PPE program) — 4 questions

**Decision:** Reverted. +4% coverage did not justify adding 3 external PDFs that introduce scope creep and maintenance burden. The 12 gaps are documented as confirmed knowledge boundaries in `model_limitations.md`. The original 288-chunk collection was restored.

**Note:** During restoration, the collection was inadvertently recreated with L2 distance instead of cosine distance, causing all similarity scores to drop below the 0.50 threshold. Fixed by explicitly specifying `hnsw:space: cosine` on collection creation.

---

## Experiment 3 — Similarity Threshold

**Baseline threshold:** 0.50 (cosine similarity)

**Observation:** During alpha testing, top-5 retrieved chunks averaged 0.65–0.72 similarity for answered questions. The 0.50 threshold was not actively filtering any chunks for typical questions — it only triggered on questions with no relevant content in the KB.

**Decision:** Threshold kept at 0.50. Raising it (e.g. to 0.60) would not improve answer quality since relevant chunks already score well above threshold. It would only reduce coverage on borderline questions without a quality benefit.

---

## Similarity Threshold vs. Confidence Threshold

Two separate thresholds exist in the system:

| Threshold | Location | Value | Purpose |
|---|---|---|---|
| Similarity threshold | `rag_pipeline.py` | 0.50 | Filters retrieved chunks before sending to Claude |
| Confidence display | `frontend/app.py` | 0.55 / 0.70 | UI indicator only — does not affect pipeline |

The confidence display in the frontend is cosmetic (hardcoded to 0.65 or 0.72 based on whether sources were returned). It does not reflect actual similarity scores.

---

## Hallucination Scoring — LLM-as-Judge Setup

**Method:** Claude-as-judge prompt scoring each answered question on three dimensions:
- Correctness (0–3): factual accuracy vs. ground truth
- Completeness (0–3): coverage of key points
- Hallucination (yes/no): contradicts expected answer or invents facts

**Calibration issue:** First run flagged 67.9% hallucination rate. Root cause: judge prompt defined hallucination as "any fact not in the expected answer" — which incorrectly penalized the agent for adding correct supporting regulatory details (section numbers, measurement values) beyond the brief ground truth.

**Fix:** Redefined hallucination as: *"asserts facts that CONTRADICT the expected answer, or invents specific numbers/rules not plausible from OSHA standards."* Additional correct detail is not hallucination.

**Final results after calibration:**
- Hallucination rate: **0.0%**
- Avg correctness: **2.92 / 3.0**
- Fully correct (score 3): **94.3%**
