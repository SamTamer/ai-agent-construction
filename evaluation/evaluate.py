import csv
import json
import os
import time
from datetime import datetime
import requests

# ── Config ────────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000/ask"
GROUND_TRUTH = "evaluation/ground_truth.csv"
RESULTS_FILE = "evaluation/eval_results.csv"
METRICS_FILE = "evaluation/eval_metrics.json"
REQUEST_DELAY = 1.5  # seconds between requests (avoid rate limiting)
# ──────────────────────────────────────────────────────────────────────────────


def load_ground_truth(filepath):
    """Load all questions from ground_truth.csv."""
    questions = []
    with open(filepath, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row)
    return questions


def ask_agent(question):
    """Send a question to the FastAPI /ask endpoint and return the result."""
    try:
        response = requests.post(API_URL, json={"question": question}, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "question": question,
                "response": f"API error: {response.status_code}",
                "sources": [],
                "answered": False,
            }
    except Exception as e:
        return {
            "question": question,
            "response": f"Connection error: {str(e)}",
            "sources": [],
            "answered": False,
        }


def run_evaluation(ground_truth):
    """Run all questions through the agent and save results."""

    os.makedirs("evaluation", exist_ok=True)

    fieldnames = [
        "question",
        "expected_answer",
        "source_document",
        "difficulty",
        "agent_response",
        "sources_cited",
        "answered",
        "correctness",  # To be filled manually: 0, 1, 2, 3
        "completeness",  # To be filled manually: 0, 1, 2, 3
        "hallucination",  # To be filled manually: yes / no
        "notes",  # To be filled manually
    ]

    total = len(ground_truth)
    answered = 0
    failed = 0

    print(f"\n{'=' * 60}")
    print(f"  Construction Safety Agent — Evaluation Run")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total questions: {total}")
    print(f"{'=' * 60}\n")

    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, row in enumerate(ground_truth, 1):
            question = row["question"]
            difficulty = row.get("difficulty", "")
            source_doc = row.get("source_document", "")
            expected = row.get("expected_answer", "")

            print(f"[{i:02d}/{total}] {question[:70]}...")

            result = ask_agent(question)

            is_answered = result.get("answered", False)
            if is_answered:
                answered += 1
            else:
                failed += 1

            status = "✅ Answered" if is_answered else "❌ Unanswered"
            print(f"         {status}\n")

            writer.writerow(
                {
                    "question": question,
                    "expected_answer": expected,
                    "source_document": source_doc,
                    "difficulty": difficulty,
                    "agent_response": result.get("response", ""),
                    "sources_cited": " | ".join(result.get("sources", [])),
                    "answered": "yes" if is_answered else "no",
                    "correctness": "",  # fill in manually
                    "completeness": "",  # fill in manually
                    "hallucination": "",  # fill in manually
                    "notes": "",  # fill in manually
                }
            )

            # Avoid hitting rate limit
            time.sleep(REQUEST_DELAY)

    print(f"{'=' * 60}")
    print(f"  Run complete.")
    print(f"  Answered  : {answered}/{total} ({answered / total * 100:.1f}%)")
    print(f"  Unanswered: {failed}/{total} ({failed / total * 100:.1f}%)")
    print(f"  Results saved to: {RESULTS_FILE}")
    print(f"{'=' * 60}\n")

    return answered, failed, total


def compute_metrics(results_file):
    """
    Compute aggregate metrics from the manually scored results CSV.
    Run this AFTER you have filled in correctness / completeness / hallucination columns.
    """
    rows = []
    with open(filepath, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    total = len(rows)
    answered = sum(1 for r in rows if r["answered"] == "yes")
    unanswered = total - answered

    # Only score rows that have been manually filled in
    scored = [r for r in rows if r["correctness"].strip() != ""]

    if not scored:
        print("\n⚠️  No manually scored rows found.")
        print("   Open eval_results.csv and fill in the correctness, completeness,")
        print("   and hallucination columns first, then re-run with --metrics.\n")
        return

    correctness_scores = [int(r["correctness"]) for r in scored]
    completeness_scores = [int(r["completeness"]) for r in scored]
    hallucinations = [r["hallucination"].strip().lower() for r in scored]

    avg_correctness = sum(correctness_scores) / (len(correctness_scores) * 3) * 100
    avg_completeness = sum(completeness_scores) / (len(completeness_scores) * 3) * 100
    hallucination_rate = hallucinations.count("yes") / len(hallucinations) * 100

    # Breakdown by difficulty
    difficulties = set(r["difficulty"] for r in rows)
    diff_breakdown = {}
    for d in difficulties:
        d_rows = [r for r in scored if r["difficulty"] == d]
        d_answered = sum(
            1 for r in rows if r["difficulty"] == d and r["answered"] == "yes"
        )
        d_total = sum(1 for r in rows if r["difficulty"] == d)
        diff_breakdown[d] = {
            "total": d_total,
            "answered": d_answered,
            "coverage": f"{d_answered / d_total * 100:.1f}%" if d_total else "N/A",
        }

    metrics = {
        "run_date": datetime.now().isoformat(),
        "total_questions": total,
        "answered": answered,
        "unanswered": unanswered,
        "coverage_pct": round(answered / total * 100, 1),
        "scored_questions": len(scored),
        "avg_correctness_pct": round(avg_correctness, 1),
        "avg_completeness_pct": round(avg_completeness, 1),
        "hallucination_rate_pct": round(hallucination_rate, 1),
        "targets_met": {
            "correctness_above_80": avg_correctness >= 80,
            "hallucination_below_5pct": hallucination_rate <= 5,
        },
        "by_difficulty": diff_breakdown,
    }

    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  Evaluation Metrics")
    print(f"{'=' * 60}")
    print(
        f"  Coverage          : {metrics['coverage_pct']}%  ({answered}/{total} answered)"
    )
    print(f"  Correctness       : {metrics['avg_correctness_pct']}%  (target: >80%)")
    print(f"  Completeness      : {metrics['avg_completeness_pct']}%")
    print(f"  Hallucination rate: {metrics['hallucination_rate_pct']}%  (target: <5%)")
    print(f"\n  Targets met:")
    print(
        f"    Correctness >80%   : {'✅' if metrics['targets_met']['correctness_above_80'] else '❌'}"
    )
    print(
        f"    Hallucination <5%  : {'✅' if metrics['targets_met']['hallucination_below_5pct'] else '❌'}"
    )
    print(f"\n  By difficulty:")
    for d, stats in diff_breakdown.items():
        print(
            f"    {d:<12}: {stats['answered']}/{stats['total']} answered ({stats['coverage']})"
        )
    print(f"\n  Full metrics saved to: {METRICS_FILE}")
    print(f"{'=' * 60}\n")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("\nUsage:")
        print(
            "  python evaluation/evaluate.py --run       # run all questions through agent"
        )
        print(
            "  python evaluation/evaluate.py --metrics   # compute scores after manual scoring\n"
        )
        sys.exit(0)

    if sys.argv[1] == "--run":
        ground_truth = load_ground_truth(GROUND_TRUTH)
        run_evaluation(ground_truth)
        print("Next step: open evaluation/eval_results.csv and fill in the")
        print(
            "correctness (0-3), completeness (0-3), and hallucination (yes/no) columns."
        )
        print("Then run:  python evaluation/evaluate.py --metrics\n")

    elif sys.argv[1] == "--metrics":
        compute_metrics(RESULTS_FILE)

    else:
        print(f"Unknown argument: {sys.argv[1]}")
        print("Use --run or --metrics")
