"""Enrichment evaluation invariants, anti-overfitting guards, and 4-bucket attribution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set

VALID_BUCKETS = (
    "RECALL_MISS",
    "PRECISION_ERROR",
    "RETRIEVAL_LINK_MISS",
    "CONSUMER_ERROR",
)


@dataclass(frozen=True)
class EnrichedEntry:
    entry_id: str
    entity: str
    body: str
    status: str = "APPROVED"  # APPROVED | DRAFT | REJECTED | SUPERSEDED
    revision: int = 1


def check_entity_isolation(
    entries: Sequence[EnrichedEntry],
    exclusive_markers: Dict[str, Sequence[str]],
) -> List[str]:
    """PROP-01: Entity A's exclusive rules/numbers must never leak into Entity B's entry."""
    violations: List[str] = []
    for entry in entries:
        for owner_entity, markers in exclusive_markers.items():
            if owner_entity == entry.entity:
                continue
            for marker in markers:
                if marker and marker in entry.body:
                    violations.append(
                        f"entity_leak: entry={entry.entry_id} entity={entry.entity} "
                        f"leaked marker={marker!r} from {owner_entity}"
                    )
    return violations


def check_constraint_preservation(
    entries: Sequence[EnrichedEntry],
    required_constraints: Dict[str, Sequence[str]],
) -> List[str]:
    """PROP-02: Critical qualification filters and negative constraints must survive enrichment."""
    violations: List[str] = []
    by_entity: Dict[str, str] = {}
    for entry in entries:
        if entry.status == "APPROVED":
            by_entity[entry.entity] = by_entity.get(entry.entity, "") + "\n" + entry.body

    for entity, constraints in required_constraints.items():
        corpus = by_entity.get(entity, "")
        for clause in constraints:
            if clause not in corpus:
                violations.append(
                    f"constraint_lost: entity={entity} missing clause={clause!r}"
                )
    return violations


def check_revision_fidelity(
    entries: Sequence[EnrichedEntry],
    forbidden_stale_or_rejected: Sequence[str],
) -> List[str]:
    """PROP-03: Approved active entries must not carry superseded v1 or rejected/draft rules."""
    violations: List[str] = []
    for entry in entries:
        if entry.status != "APPROVED":
            continue
        for stale in forbidden_stale_or_rejected:
            if stale and stale in entry.body:
                violations.append(
                    f"stale_rule_active: entry={entry.entry_id} rev={entry.revision} "
                    f"contains forbidden={stale!r}"
                )
    return violations


def check_holdout_isolation(
    tuning_task_ids: Iterable[str],
    holdout_task_ids: Iterable[str],
) -> List[str]:
    """PROP-04: Optimization workers must never receive holdout task IDs or answers."""
    overlap: Set[str] = set(tuning_task_ids) & set(holdout_task_ids)
    return [f"holdout_leak: task={tid}" for tid in sorted(overlap)]


def aggregate_failure_attribution(
    failed_records: Sequence[Dict[str, str]],
) -> Dict[str, int]:
    """PROP-05: Every failed trial must map to one of the 4 root-cause buckets."""
    counts = {bucket: 0 for bucket in VALID_BUCKETS}
    for idx, rec in enumerate(failed_records):
        bucket = rec.get("bucket", "")
        if bucket not in counts:
            raise ValueError(
                f"record[{idx}] has invalid attribution bucket {bucket!r}; "
                f"expected one of {VALID_BUCKETS}"
            )
        counts[bucket] += 1
    if sum(counts.values()) != len(failed_records):
        raise AssertionError("attribution conservation violated")
    return counts


def evaluate_merge_gate(
    *,
    dev_pass_before: int,
    dev_pass_after: int,
    holdout_pass_before: int,
    holdout_pass_after: int,
    new_regressions: int,
    token_ratio: float,
    max_token_ratio: float = 1.5,
) -> Dict[str, object]:
    """Decide whether an enrichment optimization round is eligible to merge."""
    reasons: List[str] = []
    if dev_pass_after <= dev_pass_before:
        reasons.append("dev_not_improved")
    if holdout_pass_after < holdout_pass_before:
        reasons.append("holdout_regressed")
    if new_regressions > 0:
        reasons.append(f"new_regressions={new_regressions}")
    if token_ratio > max_token_ratio:
        reasons.append(f"token_ratio={token_ratio:.2f}>{max_token_ratio:.2f}")
    return {"approved": len(reasons) == 0, "reasons": reasons}
