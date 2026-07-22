"""
Hallucination scoring script — uses Claude as an LLM judge to score each
answered question in eval_results.csv for correctness, completeness, and
hallucination.

Scoring rubric:
  correctness  (0-3): 0=wrong/misleading, 1=partially correct, 2=mostly correct, 3=fully correct
  completeness (0-3): 0=missing key info, 1=covers some points, 2=covers most, 3=covers all
  hallucination (yes/no): yes = response asserts facts not supported by the expected answer

Usage:
    python evaluation/score_hallucination.py
"""

import csv
import json
import os
import time

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

JUDGE_PROMPT = """You are an expert evaluator for a construction safety AI assistant.

You will be given:
- A QUESTION asked by a user
- The EXPECTED ANSWER (ground truth from OSHA source documents)
- The AGENT RESPONSE (what the AI assistant actually said)

Score the agent response on three dimensions:

**CORRECTNESS (0-3):**
- 3 = Fully correct — matches the expected answer accurately
- 2 = Mostly correct — right overall but minor inaccuracies or missing a small detail
- 1 = Partially correct — gets some facts right but has significant gaps or errors
- 0 = Wrong or misleading — contradicts the expected answer or is factually incorrect

**COMPLETENESS (0-3):**
- 3 = Complete — covers all key points from the expected answer
- 2 = Mostly complete — covers most key points, misses one minor detail
- 1 = Partially complete — covers some points but misses important information
- 0 = Incomplete — barely addresses the question

**HALLUCINATION (yes/no):**
- yes = The response asserts facts that directly CONTRADICT the expected answer, or invents specific numbers/rules that are clearly fabricated and not plausible from OSHA construction safety standards
- no = The response is correct or adds supporting regulatory details beyond the expected answer (additional context, section numbers, examples are NOT hallucination as long as they don't contradict the expected answer)

Note: The expected answer is intentionally brief. An agent response that is MORE detailed than the expected answer is fine — only flag hallucination if something is factually WRONG or contradictory.

Respond ONLY with valid JSON in this exact format:
{
  "correctness": <0-3>,
  "completeness": <0-3>,
  "hallucination": "<yes or no>",
  "notes": "<one sentence explaining your reasoning, especially if hallucination=yes>"
}

---

QUESTION: {question}

EXPECTED ANSWER: {expected_answer}

AGENT RESPONSE: {agent_response}
"""


def score_response(client, question, expected_answer, agent_response):
    prompt = (JUDGE_PROMPT
              .replace("{question}", question)
              .replace("{expected_answer}", expected_answer)
              .replace("{agent_response}", agent_response))
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        temperature=0.0,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()

    # Extract JSON object by tracking brace depth (handles } inside string values)
    start = raw.find('{')
    if start == -1:
        raise ValueError(f"No JSON object found in response: {raw[:200]}")
    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(raw[start:], start):
        if escape:
            escape = False
            continue
        if ch == '\\' and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return json.loads(raw[start:i+1])
    raise ValueError(f"Unmatched braces in response: {raw[:200]}")


def main():
    input_path = "evaluation/eval_results.csv"
    output_path = "evaluation/eval_results.csv"

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    with open(input_path, "r", encoding="utf-8-sig", errors="replace") as f:
        rows = list(csv.DictReader(f))

    fieldnames = rows[0].keys() if rows else []

    answered_rows = [r for r in rows if r.get("answered", "").strip().lower() in ("true", "1", "yes")]
    print(f"Scoring {len(answered_rows)} answered questions...\n")

    scored = 0
    hallucinations = 0

    for i, row in enumerate(rows):
        if row.get("answered", "").strip().lower() not in ("true", "1", "yes"):
            continue

        # Skip if already scored
        if str(row.get("correctness", "")).strip() and str(row.get("hallucination", "")).strip():
            print(f"[{i+1}] Already scored — skipping")
            scored += 1
            continue

        question = row["question"]
        expected = row["expected_answer"]
        agent_resp = row["agent_response"]

        print(f"[{scored+1}/{len(answered_rows)}] {question[:70]}...")

        try:
            result = score_response(client, question, expected, agent_resp)
            row["correctness"] = result["correctness"]
            row["completeness"] = result["completeness"]
            row["hallucination"] = result["hallucination"]
            row["notes"] = result.get("notes", "")

            if result["hallucination"].lower() == "yes":
                hallucinations += 1
                print(f"  ⚠ HALLUCINATION — {result['notes']}")
            else:
                print(f"  correctness={result['correctness']} completeness={result['completeness']} hallucination={result['hallucination']}")

            scored += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            row["notes"] = f"scoring error: {e}"

        time.sleep(0.5)  # gentle rate limiting

    # Write back
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    print(f"\n{'='*60}")
    print(f"HALLUCINATION SCORING COMPLETE")
    print(f"  Questions scored    : {scored}")
    print(f"  Hallucinations found: {hallucinations}")
    print(f"  Hallucination rate  : {hallucinations/scored*100:.1f}%" if scored else "  N/A")

    # Detailed stats
    c_scores = [int(r["correctness"]) for r in rows if str(r.get("correctness", "")).strip()]
    if c_scores:
        print(f"\nCorrectness breakdown:")
        for score in [3, 2, 1, 0]:
            count = c_scores.count(score)
            print(f"  {score}: {count} ({count/len(c_scores)*100:.1f}%)")
        print(f"  Avg correctness: {sum(c_scores)/len(c_scores):.2f}/3.0")

    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
