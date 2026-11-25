"""Seeded property/invariant tests for Enrichment evaluation guards."""

from __future__ import annotations

import random
import unittest

from evaluators.invariants import (
    VALID_BUCKETS,
    EnrichedEntry,
    aggregate_failure_attribution,
    check_constraint_preservation,
    check_entity_isolation,
    check_holdout_isolation,
    check_revision_fidelity,
    evaluate_merge_gate,
)


class EnrichmentInvariantPropertyTests(unittest.TestCase):
    def test_prop01_entity_isolation_randomized(self) -> None:
        rng = random.Random(20261125)
        entities = ["AsterDesk", "BorealDocs", "CedarTransport", "DeltaBilling"]
        for trial in range(50):
            markers = {
                ent: [f"{ent}-RULE-{rng.randint(10, 99)}", f"{rng.randint(1, 30)}天-{ent}"]
                for ent in entities
            }
            clean_entries = [
                EnrichedEntry(
                    entry_id=f"e-{trial}-{i}",
                    entity=ent,
                    body=f"生效规范：{', '.join(markers[ent])}",
                )
                for i, ent in enumerate(entities)
            ]
            self.assertEqual(check_entity_isolation(clean_entries, markers), [])

            # Inject a cross-entity misbinding and verify the checker always catches it.
            src, dst = rng.sample(entities, 2)
            leaked_marker = rng.choice(markers[src])
            polluted = list(clean_entries)
            polluted.append(
                EnrichedEntry(
                    entry_id=f"e-leak-{trial}",
                    entity=dst,
                    body=f"错误合并：{leaked_marker}",
                )
            )
            violations = check_entity_isolation(polluted, markers)
            self.assertTrue(
                any(dst in v and src in v for v in violations),
                f"failed to catch leak {src}->{dst}: {violations}",
            )

    def test_prop02_constraint_preservation_randomized(self) -> None:
        rng = random.Random(20261126)
        clauses = [
            "排除测试账号",
            "仅统计已履约订单",
            "禁止对 POST 重试",
            "不得关闭调用方流",
            "seek(initial_offset)",
        ]
        for trial in range(40):
            required = rng.sample(clauses, 3)
            full_entry = EnrichedEntry(
                entry_id=f"c-{trial}",
                entity="D2Analytics",
                body="；".join(required),
            )
            self.assertEqual(
                check_constraint_preservation([full_entry], {"D2Analytics": required}),
                [],
            )

            dropped = rng.choice(required)
            partial_entry = EnrichedEntry(
                entry_id=f"c-drop-{trial}",
                entity="D2Analytics",
                body="；".join(c for c in required if c != dropped),
            )
            violations = check_constraint_preservation(
                [partial_entry], {"D2Analytics": required}
            )
            self.assertTrue(any(dropped in v for v in violations))

    def test_prop03_revision_fidelity_blocks_stale_in_approved_only(self) -> None:
        forbidden = ["退款时效为 7 天", "允许对所有请求盲目重试"]
        entries = [
            EnrichedEntry("e-active", "Policy", "退款时效为 15 天", status="APPROVED", revision=2),
            EnrichedEntry("e-old", "Policy", "退款时效为 7 天", status="SUPERSEDED", revision=1),
            EnrichedEntry("e-rej", "Cedar", "允许对所有请求盲目重试", status="REJECTED", revision=1),
        ]
        self.assertEqual(check_revision_fidelity(entries, forbidden), [])

        bad = entries + [
            EnrichedEntry("e-bad", "Policy", "当前退款时效为 7 天", status="APPROVED", revision=2)
        ]
        violations = check_revision_fidelity(bad, forbidden)
        self.assertEqual(len(violations), 1)
        self.assertIn("e-bad", violations[0])

    def test_prop04_holdout_isolation(self) -> None:
        holdout = {"ANA-09", "ANA-10", "QA-09", "DEV-09"}
        self.assertEqual(check_holdout_isolation(["ANA-01", "QA-02", "DEV-03"], holdout), [])
        leaks = check_holdout_isolation(["ANA-01", "QA-09"], holdout)
        self.assertEqual(leaks, ["holdout_leak: task=QA-09"])

    def test_prop05_attribution_conservation_and_rejection(self) -> None:
        rng = random.Random(20261127)
        for _ in range(30):
            n = rng.randint(1, 25)
            records = [{"task": f"T-{i}", "bucket": rng.choice(VALID_BUCKETS)} for i in range(n)]
            counts = aggregate_failure_attribution(records)
            self.assertEqual(sum(counts.values()), n)

        with self.assertRaises(ValueError):
            aggregate_failure_attribution([{"task": "T-1", "bucket": "UNKNOWN"}])

    def test_merge_gate_enforces_net_gain_and_cost(self) -> None:
        ok = evaluate_merge_gate(
            dev_pass_before=12,
            dev_pass_after=18,
            holdout_pass_before=8,
            holdout_pass_after=9,
            new_regressions=0,
            token_ratio=1.15,
        )
        self.assertTrue(ok["approved"])

        regressed = evaluate_merge_gate(
            dev_pass_before=12,
            dev_pass_after=20,
            holdout_pass_before=8,
            holdout_pass_after=7,
            new_regressions=1,
            token_ratio=1.8,
        )
        self.assertFalse(regressed["approved"])
        self.assertIn("holdout_regressed", regressed["reasons"])
        self.assertIn("new_regressions=1", regressed["reasons"])


if __name__ == "__main__":
    unittest.main()
