"""Render paired mechanical scores and gated attribution from local evidence."""
import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import mean, median

from evaluators.attribution import trials
from evaluators.fixtures import SCENES, SPLITS, cases, read_json
from evaluators.invariants import VALID_BUCKETS, aggregate_failure_attribution

LABELS = {"d2_analysis": "D2 数据分析", "policy_qa": "企业知识问答", "dev_context": "研发上下文"}


def metrics(records):
    complete = [trial for trial in records if trial["status"] == "complete"]
    passed = sum(trial["score"]["mechanical_passed"] for trial in records)
    first = [trial for trial in records if trial["repeat"] == 1]
    tokens = [trial["total_tokens"] for trial in records if trial["total_tokens"] is not None]
    regressions = sum(trial["score"].get("new_regression", False) for trial in records)
    return {"passed": passed, "planned": len(records),
            "pass_at_1": [sum(trial["score"]["mechanical_passed"] for trial in first), len(first)],
            "status": dict(Counter(trial["status"] for trial in records)),
            "source_traceable": sum(trial["score"].get("traceable", False) for trial in complete),
            "source_traceable_and_passed": sum(trial["score"].get("traceable", False)
                                               and trial["score"]["mechanical_passed"] for trial in complete),
            "regressions": regressions, "mean_tokens": round(mean(tokens)) if tokens else None,
            "token_coverage": len(tokens), "p50_ms": round(median(trial["elapsed_ms"] for trial in records))}


def compare(before, after):
    wins, losses = 0, 0
    for old, new in zip(before, after, strict=True):
        if (old["id"], old["repeat"]) != (new["id"], new["repeat"]):
            raise ValueError("unpaired trial")
        old_pass = old["score"]["mechanical_passed"]
        new_pass = new["score"]["mechanical_passed"]
        wins += new_pass and not old_pass
        losses += old_pass and not new_pass
    return {"wins": wins, "losses": losses, "net_gain": wins - losses}


def load_scene(directory, arm, scene):
    return {split: [row for task, oracle in cases(scene, split)
                    for row in trials(directory, arm, scene, split, task, oracle)] for split in SPLITS}


def all_trials(by_split):
    return [row for split in SPLITS for row in by_split[split]]


def bundle(round_dir, raw_round, previous_round=None):
    result = {"scenes": {}}
    result["candidate_engine"] = read_json(round_dir / "enrichment" / "engine.json")
    result["experiment"] = read_json(round_dir / "consumption" / "plan.json")
    review = []
    for scene in SCENES:
        raw = load_scene(raw_round, "raw", scene)
        enriched = load_scene(round_dir, "enriched", scene)
        worker_receipt = read_json(round_dir / "enrichment" / scene / "worker.json")
        worker = worker_receipt["worker"]
        details = {"worker_ms": worker_receipt["elapsed_ms"], "worker_usage": worker["Usage"].get("Tokens"),
                   "worker_stages": [stage["Name"] for stage in worker["Stages"] if stage["Status"] == "SUCCEEDED"],
                   "proposals": len(worker.get("Proposals") or []), "raw": metrics(all_trials(raw)),
                   "enriched": metrics(all_trials(enriched)), "delta": compare(all_trials(raw), all_trials(enriched)),
                   "splits": {split: {"raw": metrics(raw[split]), "enriched": metrics(enriched[split]),
                                      "delta": compare(raw[split], enriched[split])} for split in SPLITS}}
        if previous_round:
            previous = load_scene(previous_round, "enriched", scene)
            details["previous"] = metrics(all_trials(previous))
            details["change_vs_previous"] = compare(all_trials(previous), all_trials(enriched))
            for split in SPLITS:
                details["splits"][split]["change_vs_previous"] = compare(previous[split], enriched[split])
        rows = []
        for split in SPLITS:
            files = (round_dir / "attribution" / scene / split).glob("*.json")
            rows.extend(row for file in files for row in read_json(file))
        failure_keys = {(trial["id"], trial["repeat"]) for trial in all_trials(enriched)
                        if not trial["score"]["mechanical_passed"]}
        attributed_keys = {(row["id"], row["repeat"]) for row in rows}
        if len(attributed_keys) != len(rows) or not attributed_keys <= failure_keys:
            raise ValueError(f"duplicate or inconsistent attribution rows in {scene}")
        details["failed_trials"] = len(failure_keys)
        details["attribution"] = aggregate_failure_attribution(rows)
        details["unattributed"] = len(failure_keys - attributed_keys)
        details["unconfirmed"] = sum(not row.get("confirmed") for row in rows)
        review.extend(rows)
        result["scenes"][scene] = details
    result["attribution"] = aggregate_failure_attribution(review)
    result["confirmed_attribution"] = aggregate_failure_attribution([row for row in review if row.get("confirmed")])
    result["dev_attribution"] = sorted((row for row in review if row["split"] == "dev"),
                                       key=lambda row: (row["id"], row["repeat"]))
    return result


def md(data, heading):
    previous = any("previous" in scene for scene in data["scenes"].values())
    lines = [f"# {heading}", "",
             f"- Worker 代码 `{data['candidate_engine']['commit']}`",
             f"- 消费模型 `{data['experiment']['model']}`，每题 3 次",
             f"- 冻结输入 SHA256 `{data['experiment']['fixture_digest']}`", "",
             "| 场景 | 原文通过 | 当前富化通过 | pass@1 原文 → 富化 | Dev 原文 → 富化 | Holdout 原文 → 富化 | 配对进步 / 退化 | 新回归 原文 / 富化 |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, scene in data["scenes"].items():
        raw, enriched = scene["raw"], scene["enriched"]
        raw_first, enriched_first = raw["pass_at_1"], enriched["pass_at_1"]
        split_rate = []
        for split in SPLITS:
            detail = scene["splits"][split]
            split_rate.append(f"{detail['raw']['passed']} → {detail['enriched']['passed']} / {detail['raw']['planned']}")
        lines.append(f"| {LABELS[name]} | {raw['passed']}/{raw['planned']} | {enriched['passed']}/{enriched['planned']} | "
                     f"{raw_first[0]} → {enriched_first[0]} / {raw_first[1]} | {' | '.join(split_rate)} | "
                     f"{scene['delta']['wins']} / {scene['delta']['losses']} | {raw['regressions']} / {enriched['regressions']} |")
    lines.extend(["", "| 场景 | 消费平均 Token 原文 → 富化 | 消费耗时中位数 原文 → 富化 | 富化加工耗时 | 机械通过且可回源 原文 → 富化 |",
                  "|---|---:|---:|---:|---:|"])
    for name, scene in data["scenes"].items():
        raw, enriched = scene["raw"], scene["enriched"]
        lines.append(f"| {LABELS[name]} | {raw['mean_tokens']} → {enriched['mean_tokens']} | "
                     f"{raw['p50_ms']/1000:.1f} s → {enriched['p50_ms']/1000:.1f} s | {scene['worker_ms']/1000:.1f} s | "
                     f"{raw['source_traceable_and_passed']}/{raw['passed']} → {enriched['source_traceable_and_passed']}/{enriched['passed']} |")
    if previous:
        lines.extend(["", "| 场景 | 优化前 → 后 | Dev 净变化 | Holdout 净变化 | 配对进步 / 退化 |",
                      "|---|---:|---:|---:|---:|"])
        for name, scene in data["scenes"].items():
            delta = scene["change_vs_previous"]
            lines.append(f"| {LABELS[name]} | {scene['previous']['passed']} → {scene['enriched']['passed']} / 36 | "
                         f"{scene['splits']['dev']['change_vs_previous']['net_gain']:+d} | "
                         f"{scene['splits']['holdout']['change_vs_previous']['net_gain']:+d} | {delta['wins']} / {delta['losses']} |")
    lines.extend(["", "## 富化臂四归因账单", "", "| 归因 | 审计归类 | 已核对 |",
                  "|---|---:|---:|"])
    for bucket in VALID_BUCKETS:
        lines.append(f"| `{bucket}` | {data['attribution'][bucket]} | {data['confirmed_attribution'][bucket]} |")
    missing = sum(scene["unattributed"] for scene in data["scenes"].values())
    unconfirmed = sum(scene["unconfirmed"] for scene in data["scenes"].values())
    lines.extend(["", f"未归类 {missing} 次，已有候选归因待核对 {unconfirmed} 次。", "",
                  "### Dev 逐次证据", "", "| 题号 | 重复 | 归因 | 核对 | 观察 |", "|---|---:|---|---|---|"])
    for row in data["dev_attribution"]:
        mark = "完成" if row.get("confirmed") else "待核对"
        note = row["defect"].replace("|", "｜").replace("\n", " ")
        lines.append(f"| {row['id']} | {row['repeat']} | `{row['bucket']}` | {mark} | {note} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("round_dir", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--raw-round", type=Path)
    parser.add_argument("--previous-round", type=Path)
    parser.add_argument("--heading", default="AgentKit Enrichment 第一轮实测")
    args = parser.parse_args()
    data = bundle(args.round_dir, args.raw_round or args.round_dir, args.previous_round)
    args.report.write_text(md(data, args.heading))
    (args.round_dir / "metrics.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
