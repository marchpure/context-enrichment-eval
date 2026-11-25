"""Export confirmed Dev failures for one optimization worker."""
import argparse
import json
from pathlib import Path
import re

from evaluators.fixtures import SCENES, cases, read_json
from evaluators.invariants import VALID_BUCKETS, check_holdout_isolation


def build_dev_packet(round_dir, bucket):
    records = []
    holdout = {}
    for scene in SCENES:
        holdout.update({task["id"]: task["question"] for task, _ in cases(scene, "holdout")})
        for path in sorted((round_dir / "attribution" / scene / "dev").glob("*.json")):
            records.extend(row for row in read_json(path) if row["bucket"] == bucket and row["confirmed"])
    if check_holdout_isolation([row["id"] for row in records], holdout):
        raise ValueError("tuning packet contains Holdout task IDs")
    output = []
    for row in records:
        if row["split"] != "dev":
            raise ValueError("tuning packet contains a non-Dev attribution")
        output.append({key: row[key] for key in ("id", "repeat", "scene", "defect", "source", "entry")})
    text = json.dumps({"bucket": bucket, "dev_evidence": output}, ensure_ascii=False, indent=2) + "\n"
    if any(re.search(r"\b" + re.escape(task_id) + r"\b", text) or question in text
           for task_id, question in holdout.items()):
        raise ValueError("tuning packet contains a Holdout question or ID")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("round_dir", type=Path)
    parser.add_argument("bucket", choices=VALID_BUCKETS)
    args = parser.parse_args()
    print(build_dev_packet(args.round_dir, args.bucket), end="")


if __name__ == "__main__":
    main()
