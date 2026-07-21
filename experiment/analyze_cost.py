"""
analyze_cost.py — Count LLM calls and estimate tokens from the LightRAG
llm_response_cache JSON file produced after a pipeline run.

Usage:
    python3 experiment/analyze_cost.py \
        --cache /mnt/filestore/lightrag/separated/data/rag_storage/kv_store_llm_response_cache.json \
        --output experiment/results/separated_cost.json

The cache is copied by 'make copy' at the end of the pipeline run.
"""

import argparse
import json
from pathlib import Path


# ── Rough pricing (USD per 1M tokens, adjust to your model) ─────────────────
PRICING = {
    "input":  0.15,   # gpt-4o-mini
    "output": 0.60,
}

# Estimated average INPUT token sizes per call type.
# These are approximations based on LightRAG's prompt templates.
# Output tokens are measured from the actual cached response.
AVG_INPUT_TOKENS = {
    "extract":  4500,   # system (entity extraction) + chunk (~1200 tokens) + format instructions
    "summary":  8000,   # summarize_entity_descriptions: up to summary_context_size
    "keywords":  300,   # keywords_extraction: short query
    "query":    6000,   # rag_response: full context (entities + relations + chunks)
    "unknown":  1000,
}


def count_tokens_approx(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return max(1, len(text) // 4)


def analyze(cache_path: str, output_path: str) -> None:
    data = json.loads(Path(cache_path).read_text(encoding="utf-8"))

    # Bucket entries by cache_type
    buckets: dict[str, list[dict]] = {}
    for entry in data.values():
        ct = entry.get("cache_type", "unknown")
        buckets.setdefault(ct, []).append(entry)

    summary = {}
    total_calls = 0
    total_estimated_cost = 0.0

    for cache_type, entries in sorted(buckets.items()):
        count = len(entries)
        total_calls += count

        # Output tokens: measured from cached response text
        output_tokens = sum(count_tokens_approx(e.get("return", "")) for e in entries)

        # Input tokens: estimated from known average per call type
        avg_in = AVG_INPUT_TOKENS.get(cache_type, AVG_INPUT_TOKENS["unknown"])
        input_tokens_est = avg_in * count

        cost = (
            input_tokens_est  / 1_000_000 * PRICING["input"] +
            output_tokens     / 1_000_000 * PRICING["output"]
        )
        total_estimated_cost += cost

        summary[cache_type] = {
            "calls": count,
            "output_tokens_measured": output_tokens,
            "input_tokens_estimated": input_tokens_est,
            "estimated_cost_usd": round(cost, 6),
        }

    result = {
        "cache_file": str(cache_path),
        "total_calls": total_calls,
        "total_estimated_cost_usd": round(total_estimated_cost, 6),
        "pricing_note": f"Input: ${PRICING['input']}/1M tokens, Output: ${PRICING['output']}/1M tokens (gpt-4o-mini). Input tokens are estimated from known average prompt sizes.",
        "by_type": summary,
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Cache file : {cache_path}")
    print(f"Total LLM calls : {total_calls}")
    print()
    print(f"{'Type':<12} {'Calls':>6}  {'Out tokens':>12}  {'Est. cost USD':>14}")
    print("-" * 52)
    for ct, s in sorted(summary.items(), key=lambda x: -x[1]["calls"]):
        print(f"{ct:<12} {s['calls']:>6}  {s['output_tokens_measured']:>12,}  ${s['estimated_cost_usd']:>13.6f}")
    print("-" * 52)
    print(f"{'TOTAL':<12} {total_calls:>6}  {'':>12}  ${total_estimated_cost:>13.6f}")
    print()
    print(f"Saved to : {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze LightRAG LLM call cost from cache file")
    parser.add_argument("--cache", required=True, help="Path to kv_store_llm_response_cache.json")
    parser.add_argument("--output", required=True, help="Output JSON file for cost report")
    args = parser.parse_args()

    analyze(args.cache, args.output)
