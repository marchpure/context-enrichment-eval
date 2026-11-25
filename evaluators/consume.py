"""Paired consumption of frozen original sources and real AgentKit worker output."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from evaluators.fixtures import SCENES, SPLITS, cases, freeze, load_sources, read_json, scene_root
from evaluators.scoring import assess_patch, run_sql, score

MODEL = "doubao-seed-2-0-pro-260215"
MAX_STEPS = 8
SOURCE_CHARS = 50_000
MAX_OUTPUT_TOKENS = 7_000
SYSTEM = """你是在合成环境中完成任务的消费 Agent。依据冻结资料行动，严格区分实体、版本、生效状态和适用条件。
每轮输出一个 JSON 对象，使用如下动作之一。
{"action":"search","query":"查询词"} 返回可读路径。{"action":"list"} 返回目录。
{"action":"read","paths":["精确路径"]} 一次读取最多 6 个完整文档。阅读富化条目后可按 source_links 回查。
{"action":"execute_sql","sql":"SQLite query"} 只适用于分析题，在当前题的正常夹具执行只读 SQL。
{"action":"finish","answer":{...}} 提交题目要求的 decision 或 files，以及 evidence 和 explanation。
引用实际读取的原文连续片段，evidence 中每项的 fields 列出其支持的字段。SQL 可用字段名 sql。目录不是正文。
研发题最终 files 仅放发生变化的 cedar/*.py，值为完整源码。不得改测试。
已提供首条入口证据。允许搜索或读取同一来源库的其他路径。最后一轮必须 finish。"""


def tokens(text):
    return set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]{2}", text.lower()))


def search(query, docs, limit=10):
    query_tokens = tokens(query)
    weighted = []
    for path, doc in docs.items():
        title = doc.get("Title", "") + " " + path
        body = doc["Text"]
        title_terms, body_terms = tokens(title), tokens(body)
        score = (3 * len(title_terms & query_tokens)
                 + len(body_terms & query_tokens) / max(1, math.log(len(body_terms) + 2) / 5))
        if score:
            weighted.append((score, path))
    return [path for _, path in sorted(weighted, key=lambda row: (-row[0], row[1]))[:limit]]


def load_enriched(directory, scene, raw):
    data = read_json(directory / scene / "worker.json")
    if data.get("error") or data["worker"]["ExecutionMode"] != "MULTI_AGENT_V2":
        raise ValueError(f"no successful real enrichment artifact for {scene}")
    if any(raw[value["Path"]] != value for value in data["source_by_evidence"].values()):
        raise ValueError("enrichment source provenance does not match frozen fixture")
    if {value["Path"] for value in data["source_by_evidence"].values()} != raw.keys():
        raise ValueError("enrichment input source inventory is incomplete")
    worker = data["worker"]
    tree = worker.get("IndexTree") or {}
    domain = data["source_manifest"]["domain_id"]
    paths = tree.get("DirPathByID") or {}
    by_evidence = data["source_by_evidence"]
    by_entry = data["source_by_entry"]
    documents = {}

    def output_id(kind, key):
        return kind + "_" + hashlib.sha256((domain + "\x00" + key).encode()).hexdigest()[:32]

    def source_links(citations, entry_ids=()):
        found = {}
        for citation in citations:
            source = by_evidence.get(citation["EvidenceId"])
            if source and citation["Quote"] in source["Text"]:
                found[source["Path"]] = source
        for entry_id in entry_ids:
            if entry_id in by_entry:
                source = by_entry[entry_id]
                found[source["Path"]] = source
        return [{"path": p, "revision": source["Revision"]} for p, source in found.items()]

    def add(entry_id, title, body, links, kind="leaf", fallback=None):
        path = "enriched/" + paths.get(entry_id, fallback or entry_id)
        if path in documents:
            path += "/" + entry_id
        documents[path] = {"Path": path, "Title": title, "Text": body, "source_links": links, "kind": kind}

    for proposal in worker.get("Proposals") or []:
        if proposal["Status"] != "PENDING_REVIEW":
            continue
        candidate = proposal["Candidate"]
        entry_id = candidate["TargetEntryId"] or output_id("page", candidate["ConceptKey"])
        links = source_links(candidate.get("Citations") or [], [
            link["TargetSourceEntryId"] for link in candidate.get("Links") or []
        ])
        add(entry_id, candidate["Title"], proposal["Compiled"]["Markdown"], links)
    for draft in worker.get("TableDrafts") or []:
        table = draft["TableEntryId"]
        claims = draft.get("Claims") or []
        cited = [ref for claim in claims for ref in claim.get("Citations", [])]
        title = by_entry.get(table, {}).get("Path", table)
        body = "\n".join([claim["Text"] for claim in claims] + (draft.get("Unknowns") or []))
        add(output_id("table_context", table), title, body, source_links(cited, [table]))
    for concept in worker.get("ConceptDrafts") or []:
        definitions = concept.get("Definitions") or []
        cited = [ref for definition in definitions for ref in definition.get("Citations", [])]
        add(output_id("concept", concept["Name"].strip()), concept["Name"], "\n".join(
            definition["Quote"] for definition in definitions
        ), source_links(cited))
    for node in tree.get("Nodes") or []:
        add(node["id"], node["title"], node["markdown"], source_links([], [
            ref["id"] for ref in node.get("source_refs") or []
        ]), kind="index", fallback=node["directory_path"])

    if not documents:
        raise ValueError(f"enrichment produced no readable entries for {scene}")
    return documents


def request_model(messages, model):
    payload = {"model": model, "temperature": 0, "thinking": {"type": "disabled"},
               "response_format": {"type": "json_object"}, "max_tokens": MAX_OUTPUT_TOKENS, "messages": messages}
    endpoint = os.environ["OPENAI_BASE_URL"].rstrip("/") + "/chat/completions"
    request = Request(endpoint, data=json.dumps(payload).encode(),
                      headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"], "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=150) as response:
                data = json.load(response)
                return data, response.headers.get("X-Request-Id") or response.headers.get("X-Tt-Logid")
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(f"HTTP {error.code}") from None
        except (URLError, TimeoutError):
            if attempt == 2:
                raise RuntimeError("model transport failure") from None
        time.sleep(2 ** attempt)


def simulate(scene, task, oracle, repeat, arm, raw, enriched, model):
    docs = {**raw, **enriched}
    fixture = read_json(scene_root(scene) / f"fixture_{oracle['variant']}.json") if oracle.get("variant") else None
    trace, visible, receipts = [], {}, []
    read_chars = 0

    def read(paths):
        nonlocal read_chars
        if not isinstance(paths, list) or not 1 <= len(paths) <= 6 or not all(isinstance(p, str) for p in paths):
            return {"error": "provide 1 to 6 exact paths"}
        response = {}
        for path in paths:
            if path not in docs:
                response[path] = {"error": "unknown path"}
                continue
            doc = docs[path]
            if read_chars + len(doc["Text"]) > SOURCE_CHARS:
                response[path] = {"error": "source budget exceeded"}
                continue
            visible[path] = doc
            read_chars += len(doc["Text"])
            response[path] = doc
        return response

    def execute(action):
        name = action.get("action")
        if name == "search" and isinstance(action.get("query"), str):
            return {"paths": search(action["query"], docs)}
        if name == "list":
            return {"paths": list(docs)}
        if name == "read":
            return read(action.get("paths"))
        if name == "execute_sql" and fixture and isinstance(action.get("sql"), str):
            return run_sql(action["sql"], fixture, "normal")
        return {"error": "invalid action"}

    start = time.monotonic()
    question = task["question"] + "\n" + task["response_contract"]
    if task.get("answer_fields"):
        question += "\n字段 " + ", ".join(task["answer_fields"])
    if scene == "d2_analysis":
        question += "\n物理表登记在 schema.md；分析计算时请先执行候选 SQL 检查。"
    if scene == "dev_context":
        question += "\n使用 read 获取源码，最终补丁会执行目标验收与公开回归测试。"
    entry_docs = {path: doc for path, doc in enriched.items() if doc.get("kind") == "leaf"} or raw
    entries = search(task["question"], entry_docs) or list(entry_docs)
    initial = {"action": "read", "paths": entries[:1]}
    initial_data = execute(initial)
    trace.append({"request": initial, "result": initial_data, "automatic": True})
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question + "\n首轮检索可用路径 " + json.dumps(entries, ensure_ascii=False)
         + "\n首条证据 " + json.dumps(initial_data, ensure_ascii=False)},
    ]
    answer, status = {}, "turn_limit"
    for step in range(MAX_STEPS):
        if step == MAX_STEPS - 1:
            messages.append({"role": "user", "content": "已到最后一轮，请输出 finish。"})
        try:
            response, request_id = request_model(messages, model)
            choice = response["choices"][0]
            content = choice["message"]["content"] or ""
            receipts.append({"id": request_id, "completion_id": response.get("id"),
                             "usage": response.get("usage"), "finish_reason": choice.get("finish_reason"),
                             "message": content})
        except (RuntimeError, ValueError, KeyError, IndexError) as error:
            status = "inference_error"
            receipts.append({"error": str(error) if isinstance(error, RuntimeError) else type(error).__name__})
            break
        messages.append({"role": "assistant", "content": content})
        try:
            action = json.loads(content)
        except ValueError:
            action = {}
        if not isinstance(action, dict):
            action = {}
        if action.get("action") == "finish" and isinstance(action.get("answer"), dict):
            answer, status = action["answer"], "complete"
            break
        result = execute(action)
        trace.append({"request": action, "result": result})
        messages.append({"role": "user", "content": "动作结果 " + json.dumps(result, ensure_ascii=False)})
    elapsed = round((time.monotonic() - start) * 1000)
    sources_seen = {p: v for p, v in visible.items() if p in raw}
    grade = score(scene, task, oracle, answer, sources_seen) if status == "complete" else {"mechanical_passed": False}
    usages = [receipt.get("usage") for receipt in receipts]
    total_tokens = sum(usage["total_tokens"] for usage in usages) if all(
        isinstance(usage, dict) and "total_tokens" in usage for usage in usages
    ) else None
    return {"id": task["id"], "scene": scene, "arm": arm, "repeat": repeat, "status": status,
            "answer": answer, "score": grade, "trace": trace, "receipts": receipts,
            "elapsed_ms": elapsed, "total_tokens": total_tokens, "knowledge_chars": read_chars}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--enrichment", type=Path)
    parser.add_argument("--arm", choices=("raw", "enriched"), required=True)
    parser.add_argument("--scene", choices=SCENES, action="append")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--split", choices=SPLITS, action="append")
    parser.add_argument("--repeat", type=int, default=3)
    args = parser.parse_args()
    plan = {"model": args.model, "steps": MAX_STEPS, "output_tokens": MAX_OUTPUT_TOKENS, "source_chars": SOURCE_CHARS,
            "repeat": args.repeat, "fixture_digest": hashlib.sha256(json.dumps(freeze(), sort_keys=True).encode()).hexdigest()}
    args.output.mkdir(parents=True, exist_ok=True)
    plan_path = args.output / "plan.json"
    if plan_path.exists() and read_json(plan_path) != plan:
        parser.error("run already exists with different frozen inputs or budgets")
    plan_path.write_text(json.dumps(plan, indent=2) + "\n")

    jobs = []
    for scene in args.scene or SCENES:
        raw = load_sources(scene)
        enriched = load_enriched(args.enrichment, scene, raw) if args.arm == "enriched" else {}
        for split in args.split or SPLITS:
            for task, oracle in cases(scene, split):
                for repeat in range(1, args.repeat + 1):
                    path = args.output / args.arm / scene / split / f"{task['id']}-{repeat}.json"
                    if not path.exists():
                        jobs.append((path, scene, task, oracle, repeat, args.arm, raw, enriched, args.model))
    random.Random(20261125).shuffle(jobs)

    def run(job):
        path, *inputs = job
        result = simulate(*inputs)
        path.parent.mkdir(parents=True, exist_ok=True)
        pending = path.with_suffix(".pending")
        pending.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        pending.replace(path)
        print(f"{result['arm']} {result['id']}/{result['repeat']} {result['status']} "
              f"passed={result['score']['mechanical_passed']} tokens={result['total_tokens']}", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(run, jobs))


if __name__ == "__main__":
    main()
