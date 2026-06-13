from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DriftKind(str, Enum):
    MISSING = "missing"
    UNMANAGED = "unmanaged"
    MODIFIED = "modified"
    TAG_DRIFT = "tag_drift"


@dataclass
class NormalizedResource:
    provider: str
    resource_id: str
    resource_type: str
    name: str
    location: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)
    terraform_address: str | None = None
    terraform_type: str | None = None

    @property
    def key(self) -> str:
        return canonical_resource_id(self.resource_id)


@dataclass
class AttributeDiff:
    path: str
    expected: Any = None
    actual: Any = None


@dataclass
class DriftFinding:
    kind: DriftKind
    resource_id: str
    resource_type: str | None = None
    name: str | None = None
    terraform_address: str | None = None
    diffs: list[AttributeDiff] = field(default_factory=list)


@dataclass
class ScanSummary:
    total_expected: int = 0
    total_actual: int = 0
    missing: int = 0
    unmanaged: int = 0
    modified: int = 0
    tag_drift: int = 0


@dataclass
class ScanReport:
    scan_id: str
    provider: str
    started_at: datetime
    completed_at: datetime
    summary: ScanSummary
    findings: list[DriftFinding]

    @classmethod
    def empty(cls, scan_id: str, provider: str) -> "ScanReport":
        now = datetime.now(timezone.utc)
        return cls(
            scan_id=scan_id,
            provider=provider,
            started_at=now,
            completed_at=now,
            summary=ScanSummary(),
            findings=[],
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["started_at"] = self.started_at.isoformat()
        payload["completed_at"] = self.completed_at.isoformat()
        for finding in payload["findings"]:
            finding["kind"] = finding["kind"].value
        return payload

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict())


def canonical_resource_id(resource_id: str) -> str:
    return resource_id.strip().rstrip("/").lower()
