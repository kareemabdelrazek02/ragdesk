"""Retrieval evaluation: ingest a corpus, run golden questions, report Hit@k and MRR.

Usage:
    python -m eval.run_eval --k 3 --min-hit-rate 0.8 --out eval/results.json

Exits non-zero if Hit@k falls below --min-hit-rate, so CI can use it as a quality gate.
"""

import argparse
import json
import sys
from pathlib import Path

from app.config import Settings
from app.rag import RagPipeline

HERE = Path(__file__).parent


def evaluate(pipeline: RagPipeline, golden: list[dict], k: int) -> dict:
    hits, reciprocal_ranks, rows = 0, [], []
    for item in golden:
        results = pipeline.retrieve(item["question"], top_k=k)
        docs = [r.document for r in results]
        rank = (
            docs.index(item["expected_document"]) + 1 if item["expected_document"] in docs else None
        )
        hits += rank is not None
        reciprocal_ranks.append(1 / rank if rank else 0.0)
        rows.append(
            {
                "question": item["question"],
                "expected": item["expected_document"],
                "retrieved": docs,
                "rank": rank,
            }
        )
    n = len(golden)
    return {"k": k, "n": n, "hit_rate": hits / n, "mrr": sum(reciprocal_ranks) / n, "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=HERE / "corpus")
    parser.add_argument("--golden", type=Path, default=HERE / "golden.jsonl")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--min-hit-rate", type=float, default=0.0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    settings = Settings(qdrant_url=":memory:", collection="eval", chunk_size=60, chunk_overlap=15)
    pipeline = RagPipeline.from_settings(settings)
    for path in sorted(args.corpus.iterdir()):
        pipeline.ingest(path.name, path.read_bytes())

    golden = [json.loads(line) for line in args.golden.read_text().splitlines() if line.strip()]
    report = evaluate(pipeline, golden, args.k)

    for row in report["rows"]:
        mark = "✓" if row["rank"] else "✗"
        print(f"{mark} rank={row['rank']}  {row['question']}")
    print(
        f"\nHit@{args.k}: {report['hit_rate']:.3f}   MRR: {report['mrr']:.3f}   (n={report['n']})"
    )

    if args.out:
        args.out.write_text(json.dumps(report, indent=2))
    if report["hit_rate"] < args.min_hit_rate:
        print(f"FAIL: Hit@{args.k} below threshold {args.min_hit_rate}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
