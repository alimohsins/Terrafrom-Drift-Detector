from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .comparator import compare_resources
from .models import ScanReport
from .normalizers import normalize_terraform_instance
from .providers import CloudProvider
from .state_parser import iter_state_instances, load_state


def run_scan(state_path: Path, provider: CloudProvider, ignore_paths: set[str] | None = None) -> ScanReport:
    started_at = datetime.now(timezone.utc)
    state = load_state(state_path)
    expected = [normalize_terraform_instance(item) for item in iter_state_instances(state)]
    actual = provider.list_resources()
    summary, findings = compare_resources(expected, actual, ignore_paths)
    return ScanReport(
        scan_id=str(uuid4()),
        provider=provider.name,
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        summary=summary,
        findings=findings,
    )
