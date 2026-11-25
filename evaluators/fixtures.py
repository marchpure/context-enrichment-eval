"""Frozen source inventory and split-scoped evaluation inputs."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SCENES = {"d2_analysis": "ANA", "policy_qa": "QA", "dev_context": "DEV"}
SPLITS = ("dev", "holdout")


def scene_root(scene):
    return ROOT / "scenarios" / scene


def read_json(path):
    return json.loads(path.read_text())


def load_sources(scene):
    directory = scene_root(scene) / ("repository" if scene == "dev_context" else "sources")
    sources = {}
    for file in sorted(directory.rglob("*")):
        if not file.is_file() or file.suffix not in (".py", ".md"):
            continue
        path = file.relative_to(directory).as_posix()
        text = file.read_text()
        revision = re.search(r"(?i)^#.*?\bv(\d+)\b", text)
        sha = hashlib.sha256(text.encode()).hexdigest()
        sources[path] = {"Path": path, "Text": text, "Revision": f"v{revision[1]}:{sha[:16]}" if revision else sha[:16]}
    return sources


def cases(scene, split):
    root = scene_root(scene)
    tasks = read_json(root / split / "tasks.json")
    scoring = read_json(root / "scoring" / f"{split}.json")
    start = 1 if split == "dev" else 9
    ids = [f"{SCENES[scene]}-{i:02d}" for i in range(start, 9 if split == "dev" else 13)]
    if [task["id"] for task in tasks] != ids or set(scoring) != set(ids):
        raise ValueError(f"invalid frozen split for {scene}/{split}")
    return [(task, scoring[task["id"]]) for task in tasks]


def freeze():
    files = {}
    for scene in SCENES:
        for path in sorted(scene_root(scene).rglob("*")):
            if path.suffix in (".md", ".py", ".json") and path != scene_root(scene) / "README.md":
                files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        for split in SPLITS:
            cases(scene, split)
    return files


if __name__ == "__main__":
    print(json.dumps(freeze(), indent=2))
