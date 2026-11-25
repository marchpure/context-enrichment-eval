"""Check frozen inputs and show each oracle can reject the intended failure."""
from concurrent.futures import ThreadPoolExecutor
import json
import re

from evaluators.fixtures import ROOT, SPLITS, cases, freeze, load_sources, read_json, scene_root
from evaluators.scoring import assess_patch, check_citations, check_decision, run_sql, sql_rows_match

MUTANTS = {
    "active": {
        "pay_type": r" AND pay_type IN \([^)]*\)",
        "eligibility": r" AND \(account_tag=.*?account_id='9993'\)",
        "snapshot_hour": r" AND p_hour='23'",
        "model": r" AND instance_gpu_model IN \([^)]*\)",
        "product": r" AND product IN \([^)]*\)",
        "dedup": r"DISTINCT ",
    },
    "gpu_income": {
        "partition": r"p_date=\(SELECT MAX\(p_date\) FROM revenue\) AND ",
        "billing_month": r"billing_month='[^']+' AND ",
        "income_type": r"income_type IN \([^)]*\) AND ",
        "product_line": r"secondary_product_line_bp IN \(.*?\)\s+AND ",
        "product": r" AND subproduct IN \([^)]*\)",
    },
    "tos": {
        "partition": r"p_date=\(SELECT MAX\(p_date\) FROM revenue\) AND ",
        "billing_month": r"billing_month='[^']+' AND ",
        "income_type": r"income_type IN \([^)]*\) AND ",
        "product_line": r"secondary_product_line_bp='[^']+' AND ",
        "product": r" AND subproduct IN \([^)]*\)",
    },
    "top5": {
        "snapshot_date": r"p_date='[^']+' AND ",
        "product": r" AND product='GPU'",
    },
    "delta": {
        "retain_current_only_keys": r" UNION SELECT account_id,pay_type FROM c",
    },
}


def check_analysis(task, oracle):
    if not oracle["operation"]:
        wanted = oracle["expected_decision"]
        assert all(check_decision(wanted, wanted).values()), task["id"]
        assert not any(check_decision(wanted, {}).values()), task["id"]
        return 0, 0
    fixture = read_json(scene_root("d2_analysis") / f"fixture_{oracle['variant']}.json")
    reference = oracle["reference_sql"]
    for mode, query in reference.items():
        output = run_sql(query, fixture, mode)
        assert sql_rows_match(oracle["expected_by_fixture"][mode], output["rows"]), (task["id"], mode)
    assert "error" in run_sql("DELETE FROM gpu", fixture, "normal")
    assert "error" in run_sql("ATTACH DATABASE ':memory:' AS other", fixture, "normal")
    mutation_count = 0
    for name, pattern in MUTANTS.get(oracle["operation"], {}).items():
        baseline = reference["adversarial"]
        mutant, changed = re.subn(pattern, "", baseline)
        assert changed, (task["id"], name, "mutation did not edit the reference")
        output = run_sql(mutant, fixture, "adversarial")
        assert "rows" in output, (task["id"], name, output)
        assert not sql_rows_match(oracle["expected_by_fixture"]["adversarial"], output["rows"]), (task["id"], name)
        mutation_count += 1
    if oracle["operation"] in ("active", "gpu_income", "tos"):
        columns = ("instance_gpu_model", "product") if oracle["operation"] == "active" else ("subproduct",)
        for column in columns:
            baseline = reference["adversarial"]
            match = re.search(r"\b" + column + r" IN \(([^)]+)\)", baseline)
            items = match[1].split(",")
            for index in range(len(items)):
                reduced = ",".join(value for i, value in enumerate(items) if i != index)
                mutant = baseline[:match.start(1)] + reduced + baseline[match.end(1):]
                output = run_sql(mutant, fixture, "adversarial")
                assert "rows" in output, (task["id"], column, output)
                assert not sql_rows_match(oracle["expected_by_fixture"]["adversarial"], output["rows"]), (
                    task["id"], column, items[index]
                )
                mutation_count += 1
    return len(reference), mutation_count


def check_qa(task, oracle):
    sources = load_sources("policy_qa")
    assert set(oracle["source_paths"]) <= sources.keys()
    expected = oracle["expected"]
    assert set(task["answer_fields"]) == expected.keys()
    assert all(check_decision(expected, expected).values())
    for key in expected:
        other = {**expected}
        del other[key]
        assert not all(check_decision(expected, other).values())
    path = oracle["source_paths"][0]
    quote = sources[path]["Text"].splitlines()[0]
    answer = {"evidence": [{"path": path, "quote": quote, "fields": list(expected)}]}
    assert check_citations(answer, sources, oracle, set(expected))["traceable"]
    assert not check_citations(answer, {}, oracle, set(expected))["traceable"]


def check_patch_case(case, fixes):
    task, oracle = case
    before = assess_patch(oracle, {}, allow_empty=True)
    after = assess_patch(oracle, fixes)
    assert not before["target_passed"] and not before["new_regression"], task["id"]
    assert after["target_passed"] and not after["new_regression"], (task["id"], after)


def main():
    assert read_json(ROOT / "scenarios" / "FROZEN.json") == freeze(), "fixture hash mismatch"
    counts = {"sql_reference_executions": 0, "sql_filter_mutations_rejected": 0, "qa_oracles": 0, "patch_oracles": 0}
    fixes = read_json(scene_root("dev_context") / "scoring" / "reference_repairs.json")
    for split in SPLITS:
        for task, oracle in cases("d2_analysis", split):
            executions, mutants = check_analysis(task, oracle)
            counts["sql_reference_executions"] += executions
            counts["sql_filter_mutations_rejected"] += mutants
        for task, oracle in cases("policy_qa", split):
            check_qa(task, oracle)
            counts["qa_oracles"] += 1
        dev_cases = cases("dev_context", split)
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda case: check_patch_case(case, fixes), dev_cases))
        counts["patch_oracles"] += len(dev_cases)
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
