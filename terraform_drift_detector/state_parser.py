from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TerraformStateError(ValueError):
    pass


def load_state(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TerraformStateError(f"State file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TerraformStateError(f"Invalid Terraform state JSON: {exc}") from exc


def iter_state_instances(state: dict[str, Any]) -> list[dict[str, Any]]:
    resources = state.get("resources", [])
    if not isinstance(resources, list):
        raise TerraformStateError("Terraform state has no valid resources list")

    instances: list[dict[str, Any]] = []
    for resource in resources:
        if resource.get("mode") != "managed":
            continue

        provider_name = _provider_name(resource.get("provider", ""))
        if provider_name != "azurerm":
            continue

        resource_type = resource.get("type")
        resource_name = resource.get("name")
        for index, instance in enumerate(resource.get("instances", [])):
            attributes = instance.get("attributes") or {}
            resource_id = attributes.get("id")
            if not resource_id:
                continue

            address = f"{resource_type}.{resource_name}"
            if len(resource.get("instances", [])) > 1:
                address = f"{address}[{index}]"

            instances.append(
                {
                    "address": address,
                    "provider": provider_name,
                    "type": resource_type,
                    "name": resource_name,
                    "id": resource_id,
                    "attributes": attributes,
                }
            )
    return instances


def _provider_name(provider_ref: str) -> str:
    if not provider_ref:
        return ""
    if "hashicorp/azurerm" in provider_ref:
        return "azurerm"
    return provider_ref.split("/")[-1].strip(']"')
