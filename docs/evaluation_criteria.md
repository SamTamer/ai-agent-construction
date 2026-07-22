# Evaluation Criteria for Construction Safety RAG Agent

**Project:** Building AI Agents for Construction Field Procedures  
**Role:** Agent Developer (Riya)  
**Document Version:** 1.0  
**Date:** April 2026

---

## 1. Overview

This document defines the evaluation criteria, metrics, methods, and thresholds used to assess the performance of the RAG-based AI agent that answers construction safety questions from the Cal/OSHA Pocket Guide for the Construction Industry (2022 Edition) and related safety documents.

The evaluation framework balances **accuracy**, **safety**, **usability**, and **retrieval quality** to ensure the agent provides reliable, actionable answers to construction technicians without requiring escalation to team leaders.

---

## 2. Evaluation Metrics

### 2.1 Core Performance Metrics

| Metric | Definition | Target Threshold | Critical? |
|--------|------------|------------------|-----------|
| **Answer Accuracy** | Percentage of answers that are factually correct and aligned with source documents | ≥ 85% | Yes |
| **Retrieval Precision** | Percentage of retrieved chunks that are relevant to the query | ≥ 80% | Yes |
| **Hallucination Rate** | Percentage of responses containing fabricated or unsupported information | ≤ 5% | Yes |
| **Citation Accuracy** | Percentage of responses that correctly cite source documents/sections | ≥ 90% | Yes |
| **Response Completeness** | Percentage of answers that fully address the question without requiring follow-up | ≥ 75% | No |
| **Out-of-Scope Detection** | Percentage of correctly identified out-of-scope questions | ≥ 80% | Yes |

### 2.2 Secondary Quality Metrics

| Metric | Definition | Target Threshold |
|--------|------------|------------------|
| **Response Clarity** | Readability and understandability of answers (human-rated 1-5 scale) | ≥ 4.0 avg |
| **Response Time** | Average time from query to response delivery | ≤ 3 seconds |
| **Retrieval Recall** | Percentage of relevant documents retrieved from total relevant documents | ≥ 70% |
| **Safety Disclaimer Coverage** | Percentage of safety-critical responses that include appropriate disclaimers | 100% |

---

## 3. Evaluation Methods

### 3.1 Automated Evaluation

**When:** Continuous evaluation during development and tuning phases

**Process:**
1. Load ground truth Q&A dataset (CSV format)
2. Run each question through the RAG pipeline
3. Compare agent responses against expected answers using:
   - **Semantic similarity scoring** (e.g., cosine similarity of embeddings)
   - **Keyword matching** for critical terms (PEL, T8 CCR, DOSH, etc.)
   - **Citation verification** (does the response reference correct document sections?)
4. Log results to evaluation output CSV with scores per metric
5. Flag responses below threshold for human review

**Tools:**
- Python evaluation script (owned by Riya)
- Embedding model for semantic similarity (same as retrieval: OpenAI text-embedding-3-small)
- ChromaDB query logs for retrieval analysis

---

### 3.2 Human Review Evaluation

**When:** Final validation phase; periodic spot-checks during development

**Process:**
1. Riya and 1-2 team members independently rate a sample of responses (minimum 20 questions)
2. Use standardized rubric (see Section 4)
3. Calculate inter-rater reliability (target: Cohen's Kappa ≥ 0.70)
4. Reconcile disagreements through discussion
5. Document edge cases and failure patterns

**Rating Dimensions:**
- Accuracy (correct vs. incorrect vs. partially correct)
- Completeness (fully addressed vs. needs follow-up)
- Clarity (1-5 scale)
- Safety appropriateness (safe vs. unsafe vs. needs disclaimer)

---

### 3.3 Error Analysis

**Categories of Errors to Track:**

| Error Type | Definition | Example |
|------------|------------|---------|
| **Hallucination** | Agent fabricates information not in source documents | "OSHA requires hard hats on all sites" (when document says "on sites with overhead hazards") |
| **Retrieval Failure** | Relevant document exists but not retrieved | Question about fall protection retrieves trenching safety instead |
| **Misinterpretation** | Correct document retrieved but answer misinterprets content | Confuses PEL (Permissible Exposure Limit) with REL (Recommended Exposure Limit) |
| **Citation Error** | Answer is correct but cites wrong section/document | Correct answer but attributes to Section 5 instead of Section 3 |
| **Out-of-Scope Miss** | Fails to detect question is outside agent's domain | Answers "How do I file workers' comp?" (legal/HR question, not safety procedure) |
| **Over-Refusal** | Incorrectly refuses to answer in-scope question | Refuses to answer "What is a competent person?" (valid safety term) |

---

## 4. Scoring Rubrics

### 4.1 Answer Accuracy Rubric

| Score | Criteria |
|-------|----------|
| **1.0 (Correct)** | Answer is factually accurate, aligned with source documents, and addresses the full question |
| **0.5 (Partially Correct)** | Answer is mostly correct but missing key details, or contains minor inaccuracies that don't create safety risk |
| **0.0 (Incorrect)** | Answer is factually wrong, contradicts source documents, or could create safety risk |

**Safety-Critical Override:** Any answer that could lead to unsafe practices automatically scores 0.0 regardless of partial correctness.

---

### 4.2 Retrieval Precision Rubric

For each retrieved chunk (Top K results):

| Score | Criteria |
|-------|----------|
| **1.0 (Relevant)** | Chunk directly addresses the query topic and contains useful information for answering |
| **0.5 (Tangentially Relevant)** | Chunk mentions query topic but doesn't help answer the question |
| **0.0 (Irrelevant)** | Chunk has no meaningful connection to the query |

**Retrieval Precision = (Sum of relevance scores) / (Total chunks retrieved)**

---

### 4.3 Hallucination Detection Rubric

| Hallucination Present? | Criteria |
|------------------------|----------|
| **Yes (1)** | Response includes specific facts, numbers, regulations, or procedures NOT found in any source document |
| **No (0)** | All claims in response can be traced back to source documents (even if paraphrased) |

**Examples of Hallucinations:**
- Inventing OSHA regulation numbers
- Fabricating specific measurements or thresholds
- Adding procedural steps not in source documents
- Attributing requirements to wrong agencies (e.g., saying NIOSH when it's OSHA)

---

### 4.4 Out-of-Scope Detection Rubric

| Score | Criteria |
|-------|----------|
| **1.0 (Correct Detection)** | Agent correctly identifies question as out-of-scope AND provides appropriate response (e.g., "This question is about [legal/HR/equipment purchasing], which is outside my scope. I can help with safety procedures from the Cal/OSHA guide.") |
| **0.5 (Partial Detection)** | Agent hedges or expresses uncertainty but still attempts to answer |
| **0.0 (Missed Detection)** | Agent attempts to answer out-of-scope question as if it's in-scope |

**In-Scope Topics:**
- Safety procedures, protocols, requirements
- Hazard identification and controls
- PPE requirements and usage
- Regulatory compliance (OSHA, Cal/OSHA standards)
- Definitions of safety-related terms

**Out-of-Scope Topics:**
- Legal advice, workers' compensation, liability
- HR policies, hiring, discipline
- Equipment purchasing, vendor selection
- Project management, scheduling, budgeting
- Medical diagnosis or treatment

---

## 5. Ground Truth Dataset Structure

### 5.1 CSV Format

The ground truth Q&A dataset will be stored as `ground_truth_qa.csv` with the following columns:

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `question_id` | Integer | Unique identifier | 1 |
| `question` | Text | The question posed to the agent | "What is the maximum height for scaffold platforms without guardrails?" |
| `expected_answer` | Text | Gold-standard answer (can be brief summary or key points) | "10 feet. Platforms more than 10 feet above ground require guardrails per 29 CFR 1926.451(g)(1)." |
| `source_document` | Text | Document filename(s) containing the answer | "Cal_OSHA_Pocket_Guide_2022.pdf" |
| `source_section` | Text | Specific section/page reference | "Section: Scaffolds, Page 87" |
| `topic_category` | Text | Safety topic area | "Fall Protection" |
| `difficulty` | Text | Question complexity: Easy/Medium/Hard | "Medium" |
| `safety_critical` | Boolean | Whether incorrect answer poses safety risk | TRUE |
| `requires_calculation` | Boolean | Whether answer involves numerical calculation | FALSE |
| `keywords` | Text | Domain-specific terms expected in answer | "scaffold, guardrail, fall protection, 10 feet" |

---

### 5.2 Dataset Composition (Target: 50-100 Questions)

| Category | Count | % of Total |
|----------|-------|------------|
| **Easy** (direct lookup, single-fact) | 20-30 | 30-40% |
| **Medium** (requires synthesis across 2-3 paragraphs) | 25-40 | 40-50% |
| **Hard** (requires cross-document reasoning or calculation) | 10-15 | 15-20% |
| **Out-of-Scope** (test rejection capability) | 5-10 | 5-10% |

**Topic Distribution (should match document coverage):**
- Fall Protection: 15-20%
- Hazard Communication: 10-15%
- Electrical Safety: 10-15%
- Trenching/Excavation: 10-15%
- PPE Requirements: 10-15%
- Scaffolding: 10-15%
- Other (cranes, ladders, tools, etc.): 20-30%

---

## 6. Pass/Fail Thresholds

### 6.1 Phase 3 Acceptance Criteria (Initial RAG Implementation)

The agent must meet ALL of the following to proceed to Phase 4:

| Metric | Minimum Threshold |
|--------|-------------------|
| Answer Accuracy | ≥ 70% |
| Hallucination Rate | ≤ 10% |
| Out-of-Scope Detection | ≥ 75% |
| Retrieval Precision | ≥ 75% |

**Rationale:** Phase 3 focuses on baseline functionality. We expect imperfections but need proof the architecture works.

---

### 6.2 Phase 4 Tuning Targets (Pre-Deployment)

After tuning (Phase 4), the agent must meet these stricter thresholds:

| Metric | Target Threshold |
|--------|------------------|
| Answer Accuracy | ≥ 85% |
| Hallucination Rate | ≤ 5% |
| Out-of-Scope Detection | ≥ 80% |
| Retrieval Precision | ≥ 80% |
| Citation Accuracy | ≥ 90% |
| Safety Disclaimer Coverage | 100% (for safety-critical queries) |

**Additional Requirements:**
- Zero safety-critical errors (answers that could cause harm)
- Human review approval on all "Hard" difficulty questions
- Inter-rater reliability ≥ 0.70 on evaluation sample

---

## 7. Evaluation Tools & Outputs

### 7.1 Evaluation Script (Python)

**Location:** `scripts/evaluate_agent.py`

**Inputs:**
- `ground_truth_qa.csv` (ground truth dataset)
- RAG agent endpoint or callable function
- Configuration file with thresholds

**Outputs:**
- `evaluation_results.csv` (detailed per-question results)
- `evaluation_summary.json` (aggregate metrics)
- `failed_questions.csv` (questions below threshold, for tuning)
- Console report with metrics visualization

---

### 7.2 Evaluation Results CSV Format

| Column | Description |
|--------|-------------|
| `question_id` | Links to ground truth |
| `question` | The question |
| `agent_answer` | What the agent responded |
| `expected_answer` | From ground truth |
| `accuracy_score` | 0.0, 0.5, or 1.0 |
| `hallucination_detected` | TRUE/FALSE |
| `retrieval_precision` | 0.0-1.0 |
| `response_time_sec` | Latency |
| `retrieved_chunks` | Serialized list of chunk IDs |
| `error_type` | If failed: Hallucination/Retrieval Failure/Misinterpretation/etc. |
| `notes` | Free-text observations |

---

## 8. Continuous Improvement Process

### 8.1 Iteration Cycle

1. **Run evaluation** → Generate `evaluation_results.csv`
2. **Analyze failures** → Group by error type, identify patterns
3. **Tune parameters** → Adjust chunk size, Top K, score threshold, prompt, etc.
4. **Re-evaluate** → Run same ground truth set again
5. **Document changes** → Log what was changed and why in `tuning_log.md`
6. **Repeat** until Phase 4 thresholds met

---

### 8.2 Edge Case Documentation

As edge cases are discovered during evaluation, document them in `docs/edge_cases.md`:

- **Case description:** What question or scenario failed?
- **Current behavior:** What did the agent do?
- **Expected behavior:** What should it have done?
- **Root cause:** Retrieval failure? Prompt issue? Document gap?
- **Resolution:** How was it fixed (or is it an open issue)?

---

## 9. Safety-Critical Error Handling Policy

**[OPEN DECISION from Pre-Execution Gaps Analysis - TO BE RESOLVED]**

For questions where incorrect answers could lead to injury or regulatory violations:

**Option A: Conservative Disclaimers**
- Always include "Consult site supervisor before proceeding" for safety-critical topics
- Flag high-risk queries (fall protection, electrical, confined spaces) with extra warnings

**Option B: Confidence Scoring**
- Only provide answer if retrieval score > 0.85 (higher threshold than general questions)
- Otherwise respond: "This is a safety-critical topic. Please verify with your supervisor or refer to [specific document section]."

**Option C: Hybrid**
- Provide answer + disclaimer + source citation for verification

**Decision Required Before Phase 3.**

---

## 10. Open Questions & Decisions Needed

From the Pre-Execution Gaps Analysis, the following evaluation-related decisions are still pending:

1. **Out-of-Scope Handling Mode** (affects Out-of-Scope Detection metric)
   - Should agent refuse, redirect, or provide limited answer?

2. **Evaluation Scoring Protocol**
   - Who performs human review? (Riya only, or all 3 team members?)
   - What is minimum sample size for human review?

3. **Safety-Critical Error Handling** (affects Safety Disclaimer Coverage metric)
   - See Section 9 — which option?

4. **API Budget Constraints**
   - Does Claude API budget limit number of evaluation runs?
   - Should we cache embeddings to reduce costs?

**Action:** Schedule team meeting to resolve these before starting Phase 2.

---

## 11. Summary

This evaluation framework provides:

✅ **Clear metrics** with quantitative thresholds  
✅ **Automated and human evaluation methods**  
✅ **Scoring rubrics** for consistency  
✅ **Ground truth dataset structure** for Phase 2  
✅ **Pass/fail criteria** for each phase  
✅ **Error taxonomy** for systematic improvement  

**Next Steps:**
1. Review and approve this document with team
2. Resolve open decisions (Section 10)
3. Proceed to Phase 2: Document ingestion and ground truth Q&A creation

---

**Document Owner:** Riya (Agent Developer)  
**Last Updated:** April 2026  
**Status:** Draft v1.0 — Pending Team Review
