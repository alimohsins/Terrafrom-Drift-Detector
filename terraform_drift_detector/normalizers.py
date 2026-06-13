from __future__ import annotations

from typing import Any

from .models import NormalizedResource

IGNORED_PROPERTY_KEYS = {
    "id",
    "location",
    "name",
    "type",
    "tags",
    "timeouts",
    "etag",
    "provisioning_state",
    "provisioningState",
}


def normalize_terraform_instance(instance: dict[str, Any]) -> NormalizedResource:
    attrs = instance.get("attributes", {})
    resource_id = instance["id"]
    return NormalizedResource(
        provider="azure",
        resource_id=resource_id,
        resource_type=terraform_type_to_arm_type(instance.get("type", ""), resource_id),
        name=str(attrs.get("name") or instance.get("name") or _name_from_id(resource_id)),
        location=attrs.get("location"),
        tags=_string_map(attrs.get("tags")),
        properties=_clean_properties(attrs),
        terraform_address=instance.get("address"),
        terraform_type=instance.get("type"),
    )


def normalize_azure_resource(resource: dict[str, Any]) -> NormalizedResource:
    resource_id = str(resource.get("id") or resource.get("resource_id") or "")
    resource_type = str(resource.get("type") or resource.get("resource_type") or "")
    properties = resource.get("properties") or {}

    return NormalizedResource(
        provider="azure",
        resource_id=resource_id,
        resource_type=resource_type,
        name=str(resource.get("name") or _name_from_id(resource_id)),
        location=resource.get("location"),
        tags=_string_map(resource.get("tags")),
        properties=_clean_properties(properties),
    )


def terraform_type_to_arm_type(terraform_type: str, resource_id: str) -> str:
    if "/providers/" in resource_id.lower():
        after_provider = resource_id.lower().split("/providers/", 1)[1]
        parts = after_provider.split("/")
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
    if terraform_type == "azurerm_resource_group":
        return "Microsoft.Resources/resourceGroups"
    return terraform_type


def _clean_properties(raw: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in raw.items():
        if key in IGNORED_PROPERTY_KEYS or value is None:
            continue
        if isinstance(value, dict):
            nested = _clean_properties(value)
            if nested:
                cleaned[key] = nested
        elif isinstance(value, list):
            cleaned[key] = [_clean_list_item(item) for item in value]
        else:
            cleaned[key] = value
    return cleaned


def _clean_list_item(value: Any) -> Any:
    if isinstance(value, dict):
        return _clean_properties(value)
    return value


def _string_map(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): "" if item is None else str(item) for key, item in value.items()}


def _name_from_id(resource_id: str) -> str:
    return resource_id.rstrip("/").split("/")[-1] if resource_id else ""
