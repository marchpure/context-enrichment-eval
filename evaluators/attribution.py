"""Evaluate the missing rule at the source, entry and delivered-context boundaries."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

from evaluators.consume import MODEL, load_enriched, request_model
from evaluators.fixtures import SCENES, SPLITS, cases, load_sources, read_json
from evaluators.invariants import VALID_BUCKETS, aggregate_failure_attribution
from evaluators.scoring import score

REVIEW = """独立评测审计员。每次机械失败只选最早一个有证据且与该失败有关的根因。
RECALL_MISS：当前富化叶条目整体缺少必要规则。已抽到规则主干但丢资格、否定或适用范围归 PRECISION_ERROR。
PRECISION_ERROR：现有叶条目把同一规则写错、串实体、错版本，或写主干时遗漏条件。要求原文与叶条目逐字片段。
RETRIEVAL_LINK_MISS：富化叶条目准确表达关键规则，但是这次未读到；也没有提前从原文获得等价规则。
CONSUMER_ERROR：关键规则已通过原文或富化叶条目准确送达，仍生成错误 SQL、错误答案、错误补丁、格式错误或超步数。
消费端自己推理错误、安全逻辑写错、列别名错误属于消费端。只有与失败直接相关的上游缺口才能归到上游。
区分目录摘要与叶条目正文；原文、当前条目、该次可见路径三者均须核对。检验已送达的规则是否足以解释该失败。
无法判定时置信度 low，原因写清楚需要核实的缺口。不要发明中间状态、引文、规则或把验收期望当成原文。
返回 JSON {"trials":[{"repeat":整数,"bucket":上述枚举,"defect":"一句话，指明实际与应有规则以及证据流失位置",
"source":[{"path":"原文路径","quote":"连续逐字片段"}],
"entry":[{"path":"富化叶条目路径","quote":"连续逐字片段"}],
"confidence":"high|medium|low"}]}。格式类纯消费端错误允许 source/entry 为空。
ROOT_CAUSE 整组判定与任务原始评分独立，严禁修改机械结果。"""


def trial_path(round_dir, arm, scene, split, task, repeat):
    return round_dir / "consumption" / arm / scene / split / f"{task['id']}-{repeat}.json"


def delivered(record):
    visible = {}
    for item in record["trace"]:
        if item["request"].get("action") != "read" or not isinstance(item["result"], dict):
            continue
        visible.update({path: doc for path, doc in item["result"].items() if "Text" in doc})
    return visible


def load_trial(path, scene, task, oracle):
    trial = read_json(path)
    if scene == "d2_analysis" and trial["status"] == "complete":
        texts = {p: doc for p, doc in delivered(trial).items() if not p.startswith("enriched/")}
        trial["score"] = score(scene, task, oracle, trial["answer"], texts)
    return trial


def trials(round_dir, arm, scene, split, task, oracle, repeats=3):
    return [load_trial(trial_path(round_dir, arm, scene, split, task, rep), scene, task, oracle)
            for rep in range(1, repeats + 1)]


def trial_receipt(trial):
    result = trial["score"]
    remarks = {k: result[k] for k in ("fields", "error", "target", "regression", "changed_files") if k in result}
    if "executions" in result:
        remarks["failed_sql_modes"] = {mode: {**test, "rows": test.get("rows", [])[:4]}
                                       for mode, test in result["executions"].items() if not test["passed"]}
    answer = {k: trial["answer"][k] for k in ("decision", "explanation", "files") if k in trial["answer"]}
    return {"repeat": trial["repeat"], "status": trial["status"], "answer": answer, "mechanical_checks": remarks,
            "delivered_paths": list(delivered(trial))}


def checked_refs(references, documents):
    verified = []
    for reference in references or []:
        path, quote = reference.get("path"), reference.get("quote")
        if path in documents and isinstance(quote, str) and len(quote.strip()) >= 12 and quote in documents[path]["Text"]:
            verified.append({"path": path, "quote": quote})
    return verified


def audit_case(round_dir, scene, split, task, oracle, raw, enriched, model):
    output = round_dir / "attribution" / scene / split / (task["id"] + ".json")
    if output.exists():
        return read_json(output)
    case_trials = trials(round_dir, "enriched", scene, split, task, oracle)
    failed = [trial for trial in case_trials if not trial["score"]["mechanical_passed"]]
    if any(trial["status"] == "inference_error" for trial in failed):
        raise ValueError(f"{task['id']} has infrastructure failures requiring separate resolution")
    if not failed:
        return []
    passing_control = [trial for trial in trials(round_dir, "raw", scene, split, task, oracle)
                       if trial["score"]["mechanical_passed"]]
    selected = set(oracle.get("source_paths", raw))
    selected.update(p for trial in failed for p in delivered(trial) if p in raw)
    payload = {
        "question": task["question"], "response_contract": task["response_contract"],
        "mechanical_oracle": {k: v for k, v in oracle.items() if k != "reference_sql"},
        "failed_trials": [trial_receipt(trial) for trial in failed],
        "passing_raw_controls": [trial_receipt(passing_control[0])] if passing_control else [],
        "raw_sources": {path: raw[path]["Text"] for path in sorted(selected)},
        "all_enriched_leaves": {path: doc["Text"] for path, doc in enriched.items() if doc["kind"] == "leaf"},
    }
    messages = [{"role": "system", "content": REVIEW}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]
    expected = sorted(trial["repeat"] for trial in failed)
    messages.append({"role": "user", "content": f"逐条输出，每个重复编号恰好出现一次。输出顺序 {expected}。"})
    for _ in range(3):
        response, request_id = request_model(messages, model)
        content = response["choices"][0]["message"]["content"]
        try:
            rows = json.loads(content)["trials"]
            if sorted(row["repeat"] for row in rows) == expected:
                break
        except (KeyError, TypeError, ValueError):
            pass
        messages.append({"role": "user", "content": f"结构校验失败。只输出这些编号 {expected}，逐条给出独立对象。"})
    else:
        raise ValueError(f"incomplete attribution rows for {task['id']}")
    aggregate_failure_attribution(rows)
    by_repeat = {trial["repeat"]: trial for trial in failed}
    for row in rows:
        trace = delivered(by_repeat[row["repeat"]])
        row["source"] = checked_refs(row["source"], raw)
        row["entry"] = checked_refs(row["entry"], enriched)
        bucket = row["bucket"]
        verified_boundary = (
            (bucket == "RECALL_MISS" and bool(row["source"]))
            or (bucket == "PRECISION_ERROR" and bool(row["source"]) and bool(row["entry"]))
            or (bucket == "RETRIEVAL_LINK_MISS" and bool(row["entry"])
                and all(ref["path"] not in trace for ref in row["entry"]))
            or (bucket == "CONSUMER_ERROR")
        )
        row.update(id=task["id"], scene=scene, split=split, request_id=request_id,
                   checked_boundaries=verified_boundary, confirmed=False,
                   proof_sha256=hashlib.sha256(json.dumps(trace, sort_keys=True).encode()).hexdigest())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("round_dir", type=Path)
    parser.add_argument("--scene", choices=SCENES, action="append")
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()
    jobs = []
    for scene in args.scene or SCENES:
        raw = load_sources(scene)
        enriched = load_enriched(args.round_dir / "enrichment", scene, raw)
        for split in SPLITS:
            jobs.extend((args.round_dir, scene, split, task, oracle, raw, enriched, args.model)
                        for task, oracle in cases(scene, split))
    with ThreadPoolExecutor(max_workers=6) as pool:
        counts = aggregate_failure_attribution([row for rows in pool.map(lambda j: audit_case(*j), jobs) for row in rows])
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
