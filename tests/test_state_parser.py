from terraform_drift_detector.state_parser import iter_state_instances


def test_iter_state_instances_extracts_azure_managed_resources():
    state = {
        "resources": [
            {
                "mode": "managed",
                "type": "azurerm_resource_group",
                "name": "main",
                "provider": 'provider["registry.terraform.io/hashicorp/azurerm"]',
                "instances": [
                    {
                        "attributes": {
                            "id": "/subscriptions/1/resourceGroups/rg1",
                            "name": "rg1",
                            "tags": {"env": "prod"},
                        }
                    }
                ],
            },
            {
                "mode": "data",
                "type": "azurerm_client_config",
                "name": "current",
                "instances": [{"attributes": {"id": "ignored"}}],
            },
        ]
    }

    instances = iter_state_instances(state)

    assert len(instances) == 1
    assert instances[0]["address"] == "azurerm_resource_group.main"
    assert instances[0]["id"] == "/subscriptions/1/resourceGroups/rg1"
