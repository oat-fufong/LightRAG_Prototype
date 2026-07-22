"""
prepare_data.py — Convert JSON node dataset into txt files for each experiment condition.

Usage:
    python experiment/prepare_data.py --input data.json --output-dir experiment/data

Outputs:
    experiment/data/separated/  — one .txt file per node  (id_ is the filename stem)
    experiment/data/combined/   — one .txt file per law   (all articles concatenated)

Upload the contents of the desired directory to HOST_INPUT_DIR before running Jenkins.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def safe_stem(id_: str) -> str:
    """Make id_ safe as a filename.
    Thai law sections can be '24/1', '82/3' — the '/' becomes a path separator on Linux.
    Replace with '_' so the filesystem doesn't interpret it as a directory.
    Also truncates to 251 bytes so the full name + '.txt' stays within Linux's 255-byte limit.
    """
    stem = id_.replace("/", "_")
    encoded = stem.encode("utf-8")
    if len(encoded) > 251:
        stem = encoded[:251].decode("utf-8", errors="ignore")
    return stem


def law_name_from_id(id_: str) -> str:
    """Strip the trailing article number to get the parent law name.
    Handles plain (-1, -24) and sub-article (-24/1, -24_1) suffixes.
    e.g. 'พรบ.พลังงาน พ.ศ. 2535-24/1' → 'พรบ.พลังงาน พ.ศ. 2535'
    """
    return re.sub(r"-[\d/_]+$", "", id_)


def prepare(input_path: str, output_dir: str, limit: int | None = None) -> None:
    raw = Path(input_path).read_text(encoding="utf-8")
    nodes = json.loads(raw)
    if limit is not None:
        nodes = nodes[:limit]

    sep_dir = Path(output_dir) / "separated"
    com_dir = Path(output_dir) / "combined"
    sep_dir.mkdir(parents=True, exist_ok=True)
    com_dir.mkdir(parents=True, exist_ok=True)

    # ── Condition A: one file per node ──────────────────────────────────────
    for node in nodes:
        id_ = node["id_"]
        text = node["text"]
        (sep_dir / f"{safe_stem(id_)}.txt").write_text(text, encoding="utf-8")

    # ── Condition B: one file per law ────────────────────────────────────────
    laws: dict[str, list[str]] = {}
    for node in nodes:
        law = law_name_from_id(node["id_"])
        laws.setdefault(law, []).append(node["text"])

    for law_name, texts in laws.items():
        (com_dir / f"{law_name}.txt").write_text("\n\n".join(texts), encoding="utf-8")

    print(f"Separated : {len(nodes)} files → {sep_dir}")
    print(f"Combined  : {len(laws)} files  → {com_dir}")
    print()
    print("Next steps:")
    print(f"  1. Copy the chosen condition's directory contents to HOST_INPUT_DIR on the agent.")
    print(f"  2. Set IMAGE_TAG to 'separated' or 'combined' in the Jenkins parameter.")
    print(f"  3. Run the pipeline.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare experiment data files")
    parser.add_argument("--input", required=True, help="Path to the JSON dataset file")
    parser.add_argument(
        "--output-dir",
        default="experiment/data",
        help="Root output directory (default: experiment/data)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap the number of nodes to process (default: all)",
    )
    args = parser.parse_args()

    prepare(args.input, args.output_dir, args.limit)
