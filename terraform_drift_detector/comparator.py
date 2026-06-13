from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .models import AttributeDiff, DriftFinding, DriftKind, NormalizedResource, ScanSummary, canonical_resource_id


DEFAULT_IGNORE_PATHS = {
    "properties.id",
    "properties.etag",
    "properties.provisioningState",
    "properties.provisioning_state",
}


def compare_resources(
    expected: Iterable[NormalizedResource],
    actual: Iterable[NormalizedResource],
    ignore_paths: set[str] | None = None,
) -> tuple[ScanSummary, list[DriftFinding]]:
    ignored = DEFAULT_IGNORE_PATHS | (ignore_paths or set())
    expected_by_id = {item.key: item for item in expected}
    actual_by_id = {item.key: item for item in actual}
    findings: list[DriftFinding] = []

    for key, expected_resource in expected_by_id.items():
        actual_resource = actual_by_id.get(key)
        if actual_resource is None:
            findings.append(_finding(DriftKind.MISSING, expected_resource))
            continue

        tag_diffs = _diff_dict("tags", expected_resource.tags, actual_resource.tags, ignored)
        property_diffs = _diff_dict("properties", expected_resource.properties, actual_resource.properties, ignored)
        if tag_diffs:
            findings.append(_finding(DriftKind.TAG_DRIFT, expected_resource, tag_diffs))
        if property_diffs:
            findings.append(_finding(DriftKind.MODIFIED, expected_resource, property_diffs))

    for key, actual_resource in actual_by_id.items():
        if key not in expected_by_id:
            findings.append(_finding(DriftKind.UNMANAGED, actual_resource))

    summary = ScanSummary(
        total_expected=len(expected_by_id),
        total_actual=len(actual_by_id),
        missing=sum(1 for item in findings if item.kind == DriftKind.MISSING),
        unmanaged=sum(1 for item in findings if item.kind == DriftKind.UNMANAGED),
        modified=sum(1 for item in findings if item.kind == DriftKind.MODIFIED),
        tag_drift=sum(1 for item in findings if item.kind == DriftKind.TAG_DRIFT),
    )
    return summary, findings


def _finding(
    kind: DriftKind,
    resource: NormalizedResource,
    diffs: list[AttributeDiff] | None = None,
) -> DriftFinding:
    return DriftFinding(
        kind=kind,
        resource_id=resource.resource_id,
        resource_type=resource.resource_type,
        name=resource.name,
        terraform_address=resource.terraform_address,
        diffs=diffs or [],
    )


def _diff_dict(path: str, expected: dict[str, Any], actual: dict[str, Any], ignored: set[str]) -> list[AttributeDiff]:
    diffs: list[AttributeDiff] = []
    keys = set(expected) | set(actual)
    for key in sorted(keys):
        child_path = f"{path}.{key}"
        if child_path in ignored:
            continue

        expected_value = expected.get(key)
        actual_value = actual.get(key)
        if isinstance(expected_value, dict) and isinstance(actual_value, dict):
            diffs.extend(_diff_dict(child_path, expected_value, actual_value, ignored))
        elif expected_value != actual_value:
            diffs.append(AttributeDiff(path=child_path, expected=expected_value, actual=actual_value))
    return diffs
