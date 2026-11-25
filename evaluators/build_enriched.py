"""Run the checked-out AgentKit worker against only synthetic source inputs."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess

from evaluators.fixtures import ROOT, SCENES, load_sources


def run(checkout, output, scene, model):
    stage = output / scene
    stage.mkdir(exist_ok=True)
    checkout = checkout.resolve()
    replacement = {"Replace": {
        str(checkout / "internal/midgardworker/enrichment/external_eval_test.go"):
        str(ROOT / "evaluators/agentkit_worker_test.go.in")
    }}
    (stage / "overlay.json").write_text(json.dumps(replacement))
    sources = load_sources(scene)
    (stage / "sources.json").write_text(json.dumps(list(sources.values()), ensure_ascii=False))
    env = {**os.environ, "ENRICH_EVAL_INPUT": str(stage / "sources.json"),
           "ENRICH_EVAL_OUTPUT": str(stage / "worker.json"), "ENRICH_EVAL_MODEL": model}
    with (stage / "worker.log").open("w") as log:
        result = subprocess.run(
            ["go", "test", "-overlay", str(stage / "overlay.json"), "-count=1", "-v",
             "-timeout", "37m", "-run", "^TestExternalEnrichmentEvaluation$",
             "./internal/midgardworker/enrichment"],
            cwd=checkout, env=env, stdout=log, stderr=subprocess.STDOUT, check=False,
        )
    print(f"{scene}: worker exit {result.returncode}", flush=True)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", default="doubao-seed-2-0-pro-260215")
    parser.add_argument("--scene", choices=SCENES, action="append")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    git = ["git", "-C", str(args.checkout)]
    commit = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    patch = subprocess.check_output([*git, "diff", "HEAD", "--", "internal/midgardworker/enrichment"])
    (output / "engine.json").write_text(json.dumps(
        {"commit": commit, "diff_sha256": hashlib.sha256(patch).hexdigest(), "model": args.model}, indent=2
    ))
    scenes = args.scene or list(SCENES)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(scenes)) as pool:
        futures = [pool.submit(run, args.checkout, output, scene, args.model) for scene in scenes]
    return max(f.result() for f in futures)


if __name__ == "__main__":
    raise SystemExit(main())
