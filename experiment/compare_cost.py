"""
compare_cost.py — Compare LLM ingestion cost between two experiment conditions.

Usage (after both Jenkins runs complete):
    python3 experiment/compare_cost.py \
        --separated /mnt/filestore/lightrag/separated/results/cost.json \
        --combined  /mnt/filestore/lightrag/combined/results/cost.json
"""

import argparse
import json
from pathlib import Path


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compare(sep_path: str, com_path: str) -> None:
    sep = load(sep_path)
    com = load(com_path)

    all_types = sorted(set(sep["by_type"]) | set(com["by_type"]))

    header = f"{'Type':<12} {'Sep calls':>10} {'Com calls':>10}  {'Sep cost USD':>13} {'Com cost USD':>13}  {'Diff USD':>11}"
    print(header)
    print("-" * len(header))

    for ct in all_types:
        s = sep["by_type"].get(ct, {})
        c = com["by_type"].get(ct, {})
        s_calls = s.get("calls", 0)
        c_calls = c.get("calls", 0)
        s_cost  = s.get("estimated_cost_usd", 0.0)
        c_cost  = c.get("estimated_cost_usd", 0.0)
        diff    = c_cost - s_cost
        print(f"{ct:<12} {s_calls:>10,} {c_calls:>10,}  ${s_cost:>12.6f} ${c_cost:>12.6f}  ${diff:>10.6f}")

    print("-" * len(header))
    s_total = sep["total_estimated_cost_usd"]
    c_total = com["total_estimated_cost_usd"]
    s_calls = sep["total_calls"]
    c_calls = com["total_calls"]
    diff    = c_total - s_total
    print(f"{'TOTAL':<12} {s_calls:>10,} {c_calls:>10,}  ${s_total:>12.6f} ${c_total:>12.6f}  ${diff:>10.6f}")
    print()
    pct = ((c_total - s_total) / s_total * 100) if s_total else float("inf")
    cheaper = "combined" if diff < 0 else "separated"
    print(f"combined is {'cheaper' if diff < 0 else 'more expensive'} by ${abs(diff):.6f} ({abs(pct):.1f}%)  →  {cheaper} wins on cost")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare ingestion cost between separated and combined conditions")
    parser.add_argument("--separated", required=True, help="cost.json for separated condition")
    parser.add_argument("--combined",  required=True, help="cost.json for combined condition")
    args = parser.parse_args()
    compare(args.separated, args.combined)
