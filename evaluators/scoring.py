"""Mechanical SQL, policy decisions, source citations and patch acceptance."""
from contextlib import closing
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import subprocess
import tempfile
import os
import uuid

from evaluators.fixtures import ROOT, read_json, scene_root

TABLES = {
    "gpu": ("gpu", "p_date TEXT, account_id TEXT, customer_short_name TEXT, pay_type TEXT, "
            "account_tag TEXT, income_type TEXT, p_hour TEXT, instance_gpu_model TEXT, product TEXT, instance_gpu_num REAL"),
    "snapshot": ("snapshot", "p_date TEXT, product TEXT, customer_short_name TEXT, account_total_mom REAL, product_total_mom REAL"),
    "period": ("period_usage", "period TEXT, day INTEGER, account_id TEXT, pay_type TEXT, usage REAL"),
    "revenue": ("revenue", "p_date TEXT, billing_month TEXT, income_type TEXT, secondary_product_line_bp TEXT, subproduct TEXT, revenue_amount NUMERIC"),
}
COLUMNS = {
    "active": ("active_accounts",),
    "top5": ("topn_usage", "topn_percent"),
    "top20": ("topn_usage", "topn_percent"),
    "delta": ("account_id", "pay_type", "previous_avg", "current_avg", "delta"),
    "tos": ("revenue_amount",),
    "gpu_income": ("revenue_amount",),
}
READ_ONLY_OPS = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}


def run_sql(sql, fixture, mode):
    with closing(sqlite3.connect(":memory:")) as connection:
        for key, (table, schema) in TABLES.items():
            payload = fixture[key]
            if mode == "normal":
                rows = payload["normal"]
            elif key == "snapshot":
                rows = payload[mode]
            else:
                rows = payload["normal"] + payload[mode]
            connection.execute(f"CREATE TABLE {table} ({schema})")
            placeholders = ",".join("?" for _ in rows[0])
            connection.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
        connection.commit()
        connection.execute("PRAGMA query_only = ON")
        connection.set_authorizer(lambda action, *args: sqlite3.SQLITE_OK if action in READ_ONLY_OPS else sqlite3.SQLITE_DENY)
        calls = 0

        def progress():
            nonlocal calls
            calls += 1
            return int(calls >= 2000)

        connection.set_progress_handler(progress, 1000)
        try:
            cursor = connection.execute(sql)
            rows = cursor.fetchmany(201)
            return {"columns": [field[0] for field in cursor.description], "rows": rows[:200], "truncated": len(rows) > 200}
        except sqlite3.Error as error:
            return {"error": str(error)}


def value_matches(expected, actual):
    if isinstance(expected, bool) or expected is None:
        return actual is expected
    if isinstance(expected, (int, float)):
        return type(actual) in (int, float) and math.isclose(expected, actual, rel_tol=0, abs_tol=1e-7)
    if isinstance(expected, list):
        return isinstance(actual, list) and sorted(map(json.dumps, expected)) == sorted(map(json.dumps, actual))
    return type(actual) is type(expected) and actual == expected


def sql_rows_match(expected, actual):
    if len(expected) != len(actual):
        return False
    for expected_row, actual_row in zip(expected, actual):
        if len(expected_row) != len(actual_row):
            return False
        for want, got in zip(expected_row, actual_row):
            if type(got) in (int, float):
                try:
                    if not math.isclose(float(want), got, rel_tol=0, abs_tol=1e-7):
                        return False
                except (TypeError, ValueError):
                    return False
            elif want != got:
                return False
    return True


def check_decision(expected, decision):
    return {key: key in decision and value_matches(value, decision[key]) for key, value in expected.items()}


def check_citations(answer, visible, oracle, fields):
    """Count literal, delivered and source-revision-bound citations separately from decision accuracy."""
    declared = answer.get("evidence")
    citations = declared if isinstance(declared, list) else []
    allowed = set(oracle.get("source_paths", visible))
    rows = []
    covered = set()
    for citation in citations:
        if not isinstance(citation, dict):
            continue
        path, quote, anchors = citation.get("path"), citation.get("quote"), citation.get("fields")
        if not isinstance(path, str) or not isinstance(quote, str):
            continue
        source = visible.get(path, {})
        is_literal = path in allowed and len(quote.strip()) >= 12 and quote in source.get("Text", "")
        anchor_list = [a for a in anchors if isinstance(a, str)] if isinstance(anchors, list) else []
        if is_literal:
            covered.update(anchor_list)
        rows.append({"path": path, "revision": source.get("Revision"), "literal": is_literal, "fields": anchor_list})
    return {"citations": rows, "covered_fields": sorted(covered & fields), "required_fields": sorted(fields),
            "traceable": bool(rows) and all(row["literal"] for row in rows) and fields <= covered}


def assess_sql(oracle, decision):
    operation = oracle["operation"]
    if not operation:
        marks = check_decision(oracle["expected_decision"], decision)
        return {"target_passed": all(marks.values()), "fields": marks}
    sql = decision.get("sql")
    if not isinstance(sql, str):
        return {"target_passed": False, "error": "missing SQL"}
    fixture = read_json(scene_root("d2_analysis") / f"fixture_{oracle['variant']}.json")
    results = {}
    for mode, expected in oracle["expected_by_fixture"].items():
        actual = run_sql(sql, fixture, mode)
        actual["passed"] = (
            not actual.get("truncated", True)
            and tuple(actual.get("columns", ())) == COLUMNS[operation]
            and sql_rows_match(expected, actual["rows"])
        )
        results[mode] = actual
    return {"target_passed": all(result["passed"] for result in results.values()), "executions": results}


def run_tests(directory, *args):
    docker = ["docker"]
    context = os.environ.get("ENRICH_EVAL_DOCKER_CONTEXT")
    if context:
        docker.extend(["--context", context])
    container = "enrich-eval-" + uuid.uuid4().hex
    image = os.environ.get("ENRICH_EVAL_PYTHON_IMAGE", "python:3.12-slim")
    command = [
        *docker, "run", "--name", container, "--rm", "--pull=never", "--network=none",
        "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
        "--memory=128m", "--cpus=1", "--pids-limit=32", "--user=65534:65534",
        "--mount", f"type=bind,src={directory.resolve()},dst=/repo,readonly",
        "--workdir=/repo", "--entrypoint=python3", image, "-B", "-s", "-m", "unittest", *args,
    ]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=25, check=False)
        if proc.returncode == 125:
            raise RuntimeError("isolated patch runtime unavailable; run evaluator preflight")
        return {"exit": proc.returncode, "log": (proc.stdout + proc.stderr)[-8000:]}
    except subprocess.TimeoutExpired:
        subprocess.run([*docker, "rm", "-f", container], capture_output=True, timeout=10, check=False)
        return {"exit": -1, "log": "unit test timeout"}


def assess_patch(oracle, files, fixture=None, allow_empty=False):
    fixture = fixture or scene_root("dev_context") / "repository"
    if not isinstance(files, dict) or len(files) > 8:
        return {"target_passed": False, "error": "invalid source file mapping"}
    changes = {}
    for name, body in files.items():
        path = PurePosixPath(name)
        if len(path.parts) != 2 or path.parts[0] != "cedar" or not re.fullmatch(r"[a-z_]+\.py", path.name):
            return {"target_passed": False, "error": "patch must target existing cedar modules"}
        original = fixture / path
        if not original.is_file() or type(body) is not str or len(body) > 24_000:
            return {"target_passed": False, "error": "invalid source replacement"}
        if original.read_text() != body:
            changes[name] = body
    if not changes and not allow_empty:
        return {"target_passed": False, "error": "no source changes"}
    scratch = ROOT / "runs"
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="enrichment-patch-", dir=scratch) as temp:
        directory = Path(temp) / "repo"
        shutil.copytree(fixture, directory, ignore=shutil.ignore_patterns("__pycache__"))
        for name, body in changes.items():
            (directory / name).write_text(body)
        (directory / "test_acceptance.py").write_text(oracle["acceptance_code"])
        shutil.copyfile(scene_root("dev_context") / "scoring" / "test_regressions.py",
                        directory / "tests" / "test_regressions.py")
        Path(temp).chmod(0o755)
        target = run_tests(directory, "-v", "test_acceptance")
        regression = run_tests(directory, "discover", "-s", "tests", "-v")
    return {"target_passed": target["exit"] == 0, "new_regression": regression["exit"] != 0,
            "target": target, "regression": regression, "changed_files": sorted(changes)}


def score(scene, task, oracle, answer, visible):
    decision = answer.get("decision")
    decision = decision if isinstance(decision, dict) else {}
    if scene == "d2_analysis":
        result = assess_sql(oracle, decision)
        fields = set(oracle["expected_decision"] or {"sql"})
    elif scene == "policy_qa":
        marks = check_decision(oracle["expected"], decision)
        result = {"target_passed": all(marks.values()), "fields": marks}
        fields = set(task["answer_fields"])
    else:
        result = assess_patch(oracle, answer.get("files"))
        fields = set()
    evidence = check_citations(answer, visible, oracle, fields)
    result.update(evidence)
    result["mechanical_passed"] = result["target_passed"] and not result.get("new_regression", False)
    return result
