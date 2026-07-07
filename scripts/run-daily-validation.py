#!/usr/bin/env python3
"""Run product-scoped analytics validation and post the raw output to Slack."""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from shlex import join as shell_join

SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATOR_PATH = SCRIPT_DIR / "validate-analytics-docs.py"


@dataclass
class ValidationResult:
    product: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "analytics_docs_validator",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load validator from {VALIDATOR_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def discover_products():
    module = load_validator_module()
    products = module._discovered_products()
    if not products:
        raise RuntimeError("No analytics products discovered; refusing to post an empty digest")
    return products


def run_validator(product):
    command = [
        sys.executable,
        str(VALIDATOR_PATH),
        "--product",
        product,
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    return ValidationResult(
        product=product,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def github_run_url():
    server_url = os.environ.get("GITHUB_SERVER_URL")
    repository = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if not all((server_url, repository, run_id)):
        return None
    return f"{server_url}/{repository}/actions/runs/{run_id}"


def code_block(label, value):
    body = value.rstrip()
    if not body:
        body = "(empty)"
    return f"{label}:\n```text\n{body}\n```"


def build_message(results):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"Daily Analytics Validation - {timestamp}"]

    run_url = github_run_url()
    if run_url:
        lines.append(f"Run: {run_url}")

    for result in results:
        lines.extend(
            [
                "",
                f"## {result.product}",
                f"Command: `{shell_join(result.command)}`",
                f"Exit code: `{result.returncode}`",
                "",
                code_block("stdout", result.stdout),
            ]
        )
        if result.stderr:
            lines.extend(["", code_block("stderr", result.stderr)])

    return "\n".join(lines)


def post_to_slack(webhook_url, payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"Slack webhook returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Slack webhook returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Slack webhook request failed: {exc.reason}") from exc


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run analytics validation for every product and post raw output to Slack.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the Slack JSON payload and skip posting.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not args.dry_run and not webhook_url:
        raise RuntimeError("SLACK_WEBHOOK_URL is required unless --dry-run is set")

    products = discover_products()
    results = [run_validator(product) for product in products]
    payload = {"text": build_message(results)}

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    post_to_slack(webhook_url, payload)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
