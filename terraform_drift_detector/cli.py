from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .providers import AzureProvider, FixtureAzureProvider, ProviderError
from .scanner import run_scan
from .state_parser import TerraformStateError
from .storage import ScanStore


def scan(args: argparse.Namespace) -> int:
    if args.provider != "azure":
        print("Only provider=azure is implemented in this MVP", file=sys.stderr)
        return 2

    cloud_provider = FixtureAzureProvider(args.actual) if args.actual else AzureProvider(args.subscription_id)
    try:
        report = run_scan(args.state, cloud_provider)
    except (ProviderError, TerraformStateError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.db:
        ScanStore(args.db).save(report)

    payload = report.to_dict()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    _print_summary(payload)
    return 0


def serve(args: argparse.Namespace) -> int:
    import uvicorn

    from .dashboard import create_app

    uvicorn.run(create_app(args.db), host=args.host, port=args.port)
    return 0


def schedule(args: argparse.Namespace) -> int:
    seconds = _parse_interval(args.every)
    cloud_provider = FixtureAzureProvider(args.actual) if args.actual else AzureProvider(args.subscription_id)
    print(f"Scheduling Azure drift scans every {seconds} seconds. Press Ctrl+C to stop.")
    while True:
        try:
            report = run_scan(args.state, cloud_provider)
            ScanStore(args.db).save(report)
            _print_summary(report.to_dict())
        except (ProviderError, TerraformStateError) as exc:
            print(str(exc), file=sys.stderr)
        time.sleep(seconds)


def _parse_interval(value: str) -> int:
    units = {"s": 1, "m": 60, "h": 3600}
    suffix = value[-1].lower()
    if suffix in units:
        return int(value[:-1]) * units[suffix]
    return int(value)


def _print_summary(payload: dict) -> None:
    summary = payload["summary"]
    print(f"Scan {payload['scan_id']} completed for {payload['provider']}")
    print(
        "Expected={total_expected} Actual={total_actual} Missing={missing} "
        "Modified={modified} TagDrift={tag_drift} Unmanaged={unmanaged}".format(**summary)
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Terraform drift detection for Azure and future cloud providers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Run an on-demand drift scan")
    scan_parser.add_argument("--state", "-s", type=Path, required=True, help="Path to terraform.tfstate")
    scan_parser.add_argument("--provider", default="azure", help="Cloud provider")
    scan_parser.add_argument("--subscription-id", help="Azure subscription id")
    scan_parser.add_argument("--actual", type=Path, help="JSON file with captured actual Azure resources")
    scan_parser.add_argument("--output", "-o", type=Path, help="Write JSON report to this path")
    scan_parser.add_argument("--db", type=Path, default=Path("drift.db"), help="SQLite database for scan history")
    scan_parser.set_defaults(func=scan)

    serve_parser = subparsers.add_parser("serve", help="Serve the local dashboard")
    serve_parser.add_argument("--db", type=Path, default=Path("drift.db"), help="SQLite database path")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.set_defaults(func=serve)

    schedule_parser = subparsers.add_parser("schedule", help="Run scans repeatedly in this process")
    schedule_parser.add_argument("--state", "-s", type=Path, required=True)
    schedule_parser.add_argument("--every", default="30m", help="Interval such as 60s, 30m, or 1h")
    schedule_parser.add_argument("--subscription-id")
    schedule_parser.add_argument("--actual", type=Path)
    schedule_parser.add_argument("--db", type=Path, default=Path("drift.db"))
    schedule_parser.set_defaults(func=schedule)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
