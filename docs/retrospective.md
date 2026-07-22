# Project Retrospective
## Construction Safety AI Agent — Phases 1–4

*Completed: May 2026*

---

## What We Built

A RAG (Retrieval-Augmented Generation) AI agent that answers OSHA construction safety questions grounded in verified source documents. Workers on construction sites can ask natural language questions and receive cited, regulation-grounded answers — or a clear fallback if the answer isn't in the knowledge base.

**Final metrics:**
- 84% answer coverage (63/75 ground truth questions)
- 0.0% hallucination rate
- 2.92/3.0 avg correctness
- 12 confirmed knowledge gaps (documented)

---

## What Went Well

**1. Grounding strategy worked**
The decision to strictly prohibit the agent from answering outside its source documents was correct. The 0% hallucination rate validates this — Claude will fabricate answers if given the opportunity, but the system prompt and fallback detection eliminated that risk entirely.

**2. Evaluation framework built early**
Creating the 75-question ground truth dataset in Phase 1 made every subsequent decision measurable. We could immediately quantify the impact of chunking changes, KB expansion, and threshold tuning — rather than relying on qualitative impressions.

**3. Systematic chunking analysis**
Testing three chunking strategies (288 page-based, 1,101 at 500 chars, 497 at 1,200 chars) against the same ground truth gave a clear, defensible answer: the original page/section-based chunks are optimal for dense regulatory text. This finding is non-obvious and saved future teams from re-learning it.

**4. LLM-as-judge for hallucination scoring**
Using Claude to score its own outputs was efficient and scalable — 53 questions scored in minutes vs. hours of manual review. The calibration issue (first run showing 67.9% hallucination) was a useful lesson in how judge prompt wording dramatically affects results.

**5. Security measures were built in, not bolted on**
Rate limiting, input validation, and prompt injection protection were added before the project was finalized — not as an afterthought. This is the right order of operations for any production AI system.

---

## What Was Harder Than Expected

**1. ChromaDB distance metric mismatch**
When the knowledge base was temporarily expanded and then reverted, the ChromaDB collection was silently recreated with L2 distance instead of cosine distance. All similarity scores dropped to ~0.36, causing 100% unanswered questions in production — with no obvious error message. The fix was straightforward, but diagnosing it required reading raw distance values out of ChromaDB directly. Lesson: always specify `hnsw:space: cosine` explicitly when creating collections.

**2. Hallucination judge calibration**
The first hallucination scoring run returned 67.9% — which looked alarming but was entirely a prompt engineering problem. The judge prompt defined hallucination too strictly (any fact beyond the expected answer). A well-calibrated judge prompt is as important as the evaluation metric itself.

**3. The 16% coverage gap is a content problem, not an engineering problem**
Multiple approaches were tried to close the gap (chunking changes, KB expansion). None fully solved it because the root cause is absent content — the answers to 12 questions simply don't exist in any of the 3 source documents. This was the right diagnosis, but it took experimentation to confirm it conclusively.

---

## Key Decisions & Why

| Decision | Rationale |
|---|---|
| Keep original 288 chunks | Page/section chunking outperformed algorithmic splitting 84% vs 24% on same corpus |
| Don't expand KB with 3 new PDFs | +4% coverage (84→88%) didn't justify external dependency and maintenance burden |
| 0% hallucination over higher coverage | A construction safety agent that occasionally fabricates is more dangerous than one that says "I don't know" |
| Full session history (no turn cap) | Construction safety conversations are short and focused; 200K context window is not a constraint |
| Reject prompt injection with HTTP 400 | Neutral error message — doesn't reveal what was detected or how to bypass |

---

## What We Would Do Differently

1. **Specify ChromaDB distance metric explicitly from the start.** `hnsw:space: cosine` should be in the initial collection creation call, not discovered as a bug later.

2. **Build `ingest.py` in Phase 2, not Phase 4.** The ingestion script was a placeholder until Phase 4. Having a proper, parameterized ingest script earlier would have made KB experiments faster.

3. **Calibrate the hallucination judge before running at scale.** A 5-question pilot run with manual review would have caught the prompt calibration issue before scoring all 53 questions.

4. **Test pronoun resolution in follow-up questions earlier.** Conversation memory was added in Phase 4, but retrieval still requires explicit question wording — pronouns like "that" or "it" fail at the ChromaDB retrieval step. A query rewriting step (rephrasing follow-ups using history before retrieval) would improve the user experience for implicit follow-ups.

---

## Lessons Learned

- **RAG retrieval quality depends more on chunk coherence than chunk count.** 288 well-formed chunks beat 1,101 fragmented ones.
- **LLM-as-judge is powerful but sensitive to prompt wording.** Always pilot and calibrate before running at scale.
- **The fallback mechanism is as important as the answer mechanism.** A reliable "I don't know" is a safety feature, not a limitation.
- **Evaluate early and often.** The 75-question ground truth set was the project's most valuable asset — every decision was grounded in data.
