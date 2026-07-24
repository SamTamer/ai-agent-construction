"""
Quick evaluation script — runs all 75 ground truth questions through the RAG pipeline.

Usage:
    python evaluate_quick.py                                      # uses default collection
    python evaluate_quick.py --collection construction_procedures_v2
    python evaluate_quick.py --collection construction_procedures --out evaluation/quick_results_v1.json
"""

import argparse
import csv
import json

from agent.rag_pipeline import RAGPipeline

parser = argparse.ArgumentParser(description="Quick evaluation against ground truth")
parser.add_argument(
    "--collection",
    default="construction_procedures",
    help="ChromaDB collection name to evaluate",
)
parser.add_argument(
    "--out",
    default=None,
    help="Output JSON file (default: evaluation/quick_results_<collection>.json)",
)
args = parser.parse_args()

out_file = args.out or f"evaluation/quick_results_{args.collection}.json"

pipeline = RAGPipeline(collection_name=args.collection)

# Load ground truth
questions = []
with open(
    "evaluation/ground_truth.csv", "r", encoding="utf-8-sig", errors="replace"
) as f:
    reader = csv.DictReader(f)
    for row in reader:
        questions.append(row)

print(f"Collection : {args.collection}")
print(f"Loaded     : {len(questions)} questions")
print(f"Output     : {out_file}")
print("=" * 60)

results = []
for i, q in enumerate(questions):
    print(f"\n[{i + 1}/{len(questions)}] {q['question'][:70]}...")
    result = pipeline.ask(q["question"])

    results.append(
        {
            "question": q["question"],
            "expected": q["expected_answer"],
            "got": result["response"],
            "answered": result["answered"],
            "sources": result["sources"],
        }
    )

    print(f"Answered: {result['answered']}")
    print(f"Sources:  {result['sources']}")

# Save results
with open(out_file, "w") as f:
    json.dump(results, f, indent=2)

# Summary
answered = sum(1 for r in results if r["answered"])
unanswered = len(results) - answered
print("\n" + "=" * 60)
print(f"RESULTS SUMMARY — {args.collection}")
print(f"Total questions:  {len(results)}")
print(f"Answered:         {answered} ({answered / len(results) * 100:.1f}%)")
print(f"Unanswered:       {unanswered} ({unanswered / len(results) * 100:.1f}%)")
print(f"\nFull results saved to {out_file}")
