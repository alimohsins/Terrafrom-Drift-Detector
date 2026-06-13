from terraform_drift_detector.comparator import compare_resources
from terraform_drift_detector.models import DriftKind, NormalizedResource


def test_compare_detects_missing_unmanaged_modified_and_tag_drift():
    expected = [
        NormalizedResource(
            provider="azure",
            resource_id="/subscriptions/1/resourceGroups/rg1",
            resource_type="Microsoft.Resources/resourceGroups",
            name="rg1",
            tags={"env": "prod"},
            properties={"location": "eastus"},
        ),
        NormalizedResource(
            provider="azure",
            resource_id="/subscriptions/1/resourceGroups/missing",
            resource_type="Microsoft.Resources/resourceGroups",
            name="missing",
        ),
    ]
    actual = [
        NormalizedResource(
            provider="azure",
            resource_id="/subscriptions/1/resourcegroups/rg1/",
            resource_type="Microsoft.Resources/resourceGroups",
            name="rg1",
            tags={"env": "dev"},
            properties={"location": "westus"},
        ),
        NormalizedResource(
            provider="azure",
            resource_id="/subscriptions/1/resourceGroups/unmanaged",
            resource_type="Microsoft.Resources/resourceGroups",
            name="unmanaged",
        ),
    ]

    summary, findings = compare_resources(expected, actual)

    assert summary.missing == 1
    assert summary.unmanaged == 1
    assert summary.modified == 1
    assert summary.tag_drift == 1
    assert {finding.kind for finding in findings} == {
        DriftKind.MISSING,
        DriftKind.UNMANAGED,
        DriftKind.MODIFIED,
        DriftKind.TAG_DRIFT,
    }
