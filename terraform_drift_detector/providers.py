from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .models import NormalizedResource
from .normalizers import normalize_azure_resource


class ProviderError(RuntimeError):
    pass


class CloudProvider(ABC):
    name: str

    @abstractmethod
    def list_resources(self) -> list[NormalizedResource]:
        raise NotImplementedError


class FixtureAzureProvider(CloudProvider):
    name = "azure"

    def __init__(self, path: Path):
        self.path = path

    def list_resources(self) -> list[NormalizedResource]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ProviderError(f"Actual inventory file not found: {self.path}") from exc
        except json.JSONDecodeError as exc:
            raise ProviderError(f"Invalid actual inventory JSON: {exc}") from exc

        resources = raw.get("resources", raw) if isinstance(raw, dict) else raw
        if not isinstance(resources, list):
            raise ProviderError("Actual inventory must be a list or an object with a resources list")
        return [normalize_azure_resource(item) for item in resources if isinstance(item, dict)]


class AzureProvider(CloudProvider):
    name = "azure"

    def __init__(self, subscription_id: str | None = None):
        self.subscription_id = subscription_id

    def list_resources(self) -> list[NormalizedResource]:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.resource import ResourceManagementClient
        except ImportError as exc:
            raise ProviderError(
                "Azure SDK packages are not installed. Run: pip install -e .[azure]"
            ) from exc

        subscription_id = self.subscription_id or _env_subscription_id()
        if not subscription_id:
            raise ProviderError("Azure subscription id is required via --subscription-id or AZURE_SUBSCRIPTION_ID")

        credential = DefaultAzureCredential()
        client = ResourceManagementClient(credential, subscription_id)
        resources: list[dict[str, Any]] = []

        for item in client.resources.list():
            resources.append(
                {
                    "id": item.id,
                    "name": item.name,
                    "type": item.type,
                    "location": item.location,
                    "tags": item.tags or {},
                    "properties": getattr(item, "properties", None) or {},
                }
            )

        for group in client.resource_groups.list():
            resources.append(
                {
                    "id": group.id,
                    "name": group.name,
                    "type": "Microsoft.Resources/resourceGroups",
                    "location": group.location,
                    "tags": group.tags or {},
                    "properties": {},
                }
            )

        return [normalize_azure_resource(item) for item in resources]


def _env_subscription_id() -> str | None:
    import os

    return os.getenv("AZURE_SUBSCRIPTION_ID")
