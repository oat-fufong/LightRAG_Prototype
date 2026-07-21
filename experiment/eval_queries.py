"""
eval_queries.py — Run evaluation queries against the running LightRAG server,
extract retrieved file references, and compute retrieval P/R/F1.

Must be run WHILE the LightRAG container is still running (before make stop).

Usage:
    python3 experiment/eval_queries.py \
        --server http://localhost:9621 \
        --qa-file experiment/qa_dataset.json \
        --condition separated \
        --output experiment/results/separated_retrieval.json

Q/A dataset format (qa_dataset.json):
    [
        {
            "question": "...",
            "answer": "...",
            "source_nodes": ["law_name-1", "law_name-3"]
        },
        ...
    ]

source_nodes must use the same id_ values as in the original JSON dataset.

Outputs:
    - Per-question: retrieved nodes, P/R/F1 at node level AND law level
    - Aggregate: mean P/R/F1 across all questions
    - Saved to the --output JSON file
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter, Retry


# ── Helpers ──────────────────────────────────────────────────────────────────

def law_name_from_id(id_: str) -> str:
    return re.sub(r"-\d+$", "", id_)


def make_session(retries: int = 5) -> requests.Session:
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retry))
    return session


def check_health(server: str, session: requests.Session) -> None:
    try:
        r = session.get(f"{server}/health", timeout=10)
        r.raise_for_status()
        cfg = r.json().get("configuration", {})
        print(f"Server healthy | LLM: {cfg.get('llm_model')} | Embed: {cfg.get('embedding_model')}")
    except Exception as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        sys.exit(1)


def query_data(server: str, session: requests.Session, question: str, mode: str = "mix") -> dict:
    """Call POST /query/data — retrieval without LLM answer generation."""
    payload = {"query": question, "mode": mode}
    r = session.post(f"{server}/query/data", json=payload, timeout=120)
    r.raise_for_status()
    return r.json()


def extract_file_stems(references: list[dict]) -> list[str]:
    """Extract filename stems from reference file_paths.
    '/app/data/inputs/law_name-1.txt' → 'law_name-1'
    """
    stems = []
    for ref in references:
        fp = ref.get("file_path", "")
        if fp:
            stems.append(Path(fp).stem)
    return stems


# ── P/R/F1 ───────────────────────────────────────────────────────────────────

def prf1(retrieved: set, relevant: set) -> dict:
    if not retrieved and not relevant:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not retrieved:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    if not relevant:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    tp = len(retrieved & relevant)
    precision = tp / len(retrieved)
    recall = tp / len(relevant)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


# ── Main ─────────────────────────────────────────────────────────────────────

def run(server: str, qa_path: str, condition: str, mode: str, output_path: str) -> None:
    session = make_session()
    check_health(server, session)

    qa_items = json.loads(Path(qa_path).read_text(encoding="utf-8"))
    print(f"Loaded {len(qa_items)} Q/A pairs | condition={condition} | mode={mode}")
    print()

    results = []

    for i, item in enumerate(qa_items, 1):
        question = item["question"]
        source_nodes = item.get("source_nodes", [])

        # Ground truth sets
        gt_nodes = set(source_nodes)
        gt_laws = {law_name_from_id(n) for n in source_nodes}

        print(f"[{i}/{len(qa_items)}] {question[:80]}")
        t0 = time.monotonic()

        try:
            resp = query_data(server, session, question, mode=mode)
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"question": question, "error": str(e)})
            continue

        elapsed = time.monotonic() - t0
        references = resp.get("data", {}).get("references", [])
        retrieved_stems = extract_file_stems(references)

        # Node-level (only meaningful for 'separated' condition)
        retrieved_nodes = set(retrieved_stems)
        node_metrics = prf1(retrieved_nodes, gt_nodes)

        # Law-level (comparable across both conditions)
        retrieved_laws = {law_name_from_id(s) for s in retrieved_stems}
        law_metrics = prf1(retrieved_laws, gt_laws)

        result = {
            "question": question,
            "source_nodes": source_nodes,
            "retrieved_stems": sorted(retrieved_stems),
            "node_level": node_metrics,
            "law_level": law_metrics,
            "elapsed_s": round(elapsed, 2),
            "meta": resp.get("metadata", {}),
        }
        results.append(result)

        print(
            f"  node P/R/F1: {node_metrics['precision']:.3f} / {node_metrics['recall']:.3f} / {node_metrics['f1']:.3f}"
            f"  |  law P/R/F1: {law_metrics['precision']:.3f} / {law_metrics['recall']:.3f} / {law_metrics['f1']:.3f}"
            f"  ({elapsed:.1f}s)"
        )

    # ── Aggregate metrics ────────────────────────────────────────────────────
    valid = [r for r in results if "error" not in r]

    def mean(key: str, sub: str) -> float:
        vals = [r[key][sub] for r in valid]
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    aggregate = {
        "n_queries": len(qa_items),
        "n_successful": len(valid),
        "node_level": {
            "mean_precision": mean("node_level", "precision"),
            "mean_recall":    mean("node_level", "recall"),
            "mean_f1":        mean("node_level", "f1"),
        },
        "law_level": {
            "mean_precision": mean("law_level", "precision"),
            "mean_recall":    mean("law_level", "recall"),
            "mean_f1":        mean("law_level", "f1"),
        },
    }

    output = {
        "condition": condition,
        "mode": mode,
        "server": server,
        "aggregate": aggregate,
        "per_question": results,
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("=" * 60)
    print(f"Condition : {condition}")
    print(f"Queries   : {aggregate['n_successful']}/{aggregate['n_queries']} succeeded")
    print(f"Node P/R/F1 : {aggregate['node_level']['mean_precision']} / {aggregate['node_level']['mean_recall']} / {aggregate['node_level']['mean_f1']}")
    print(f"Law  P/R/F1 : {aggregate['law_level']['mean_precision']} / {aggregate['law_level']['mean_recall']} / {aggregate['law_level']['mean_f1']}")
    print(f"Saved to  : {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate retrieval performance against the LightRAG server")
    parser.add_argument("--server", default="http://localhost:9621", help="LightRAG server base URL")
    parser.add_argument("--qa-file", required=True, help="Path to Q/A JSON file with source_nodes annotations")
    parser.add_argument("--condition", required=True, choices=["separated", "combined"], help="Experiment condition name")
    parser.add_argument("--mode", default="mix", choices=["local", "global", "hybrid", "naive", "mix"], help="LightRAG query mode")
    parser.add_argument("--output", required=True, help="Output JSON file path for results")
    args = parser.parse_args()

    run(args.server, args.qa_file, args.condition, args.mode, args.output)
