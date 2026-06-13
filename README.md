# Terraform Drift Detector

Azure-first Terraform drift detection that compares Terraform state against live cloud metadata without running `terraform plan` or `terraform apply`.

## Features

- Parse local Terraform state files.
- Normalize Terraform and Azure resources into a common model.
- Detect missing, unmanaged, modified, and tag drift.
- Emit CLI summaries and JSON reports.
- Store scan history in SQLite.
- Serve a simple dashboard API.
- Use a provider abstraction so AWS/GCP can be added later.

## Install

```powershell
pip install -e .[azure]
```

For local development without Azure SDK calls:

```powershell
pip install -e .[dev,dashboard]
```

## Usage

Run a scan against Azure:

```powershell
driftdetect scan --state .\terraform.tfstate --provider azure --subscription-id <subscription-id>
```

Write a JSON report:

```powershell
driftdetect scan --state .\terraform.tfstate --output .\report.json
```

Compare against a captured Azure inventory instead of calling Azure APIs:

```powershell
driftdetect scan --state .\terraform.tfstate --actual .\azure-resources.json
```

Serve the dashboard:

```powershell
driftdetect serve --db .\drift.db
```

The dashboard command requires the optional dashboard dependencies:

```powershell
pip install -e .[dashboard]
```

Schedule scans in-process:

```powershell
driftdetect schedule --state .\terraform.tfstate --every 30m
```

## Azure Authentication

The Azure provider uses Azure SDK `DefaultAzureCredential`, so it supports Azure CLI login, service principals, managed identity, and other standard credential sources.

For service principal auth, set:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_SUBSCRIPTION_ID`
