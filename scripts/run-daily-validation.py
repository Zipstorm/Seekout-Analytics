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
MAX_BLOCKS = 50
MAX_RULE_GROUPS = 3
MAX_EXAMPLES_PER_GROUP = 2
MAX_EXAMPLE_CHARS = 240
REQUIRED_SUMMARY_KEYS = {
    "product",
    "exit_code",
    "rule_count",
    "error_count",
    "warning_count",
    "suppressed_warning_count",
    "errors",
    "warnings",
}


@dataclass
class ValidationResult:
    product: str
    command: list[str]
    returncode: int
    summary: dict
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
        "--json-summary",
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.stderr:
        emit_validator_log(product, command, completed.returncode, completed.stderr)
    summary = parse_summary(product, completed.stdout)
    if summary["exit_code"] != completed.returncode:
        raise RuntimeError(
            f"{product} validator summary exit_code {summary['exit_code']} "
            f"did not match subprocess return code {completed.returncode}"
        )
    return ValidationResult(
        product=product,
        command=command,
        returncode=completed.returncode,
        summary=summary,
        stderr=completed.stderr,
    )


def automation_error_summary(product, message):
    return {
        "product": product,
        "exit_code": 2,
        "rule_count": 0,
        "error_count": 1,
        "warning_count": 0,
        "suppressed_warning_count": 0,
        "errors": [
            {
                "rule_id": "automation",
                "rule_name": "Validator automation",
                "count": 1,
                "items": [message],
            }
        ],
        "warnings": [],
    }


def run_validator_with_fallback(product):
    try:
        return run_validator(product).summary
    except Exception as exc:
        print(f"::error::{product} validator failed before producing a usable summary: {exc}", file=sys.stderr)
        return automation_error_summary(product, str(exc))


def github_run_url():
    server_url = os.environ.get("GITHUB_SERVER_URL")
    repository = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if not all((server_url, repository, run_id)):
        return None
    return f"{server_url}/{repository}/actions/runs/{run_id}"


def emit_validator_log(product, command, returncode, stderr):
    print(f"::group::{product} validator output", file=sys.stderr)
    print(f"Command: {shell_join(command)}", file=sys.stderr)
    print(f"Exit code: {returncode}", file=sys.stderr)
    print(stderr.rstrip(), file=sys.stderr)
    print("::endgroup::", file=sys.stderr)


def parse_summary(product, stdout):
    try:
        summary = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{product} validator stdout was not valid JSON: {exc}") from exc

    missing = sorted(REQUIRED_SUMMARY_KEYS - set(summary))
    if missing:
        raise RuntimeError(
            f"{product} validator summary missing required keys: {', '.join(missing)}"
        )
    return summary


def slack_escape(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def truncate(value, limit=MAX_EXAMPLE_CHARS):
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def display_product(product):
    return str(product).replace("-", " ").title()


def product_status(summary):
    if summary["exit_code"] == 2:
        return ":octagonal_sign: config issue"
    if summary["error_count"] > 0:
        return ":x: needs attention"
    if summary["warning_count"] > 0:
        return ":warning: warnings"
    return ":white_check_mark: clean"


def overall_status(summaries):
    if any(summary["exit_code"] == 2 for summary in summaries):
        return ":octagonal_sign: config issue"
    if any(summary["error_count"] > 0 for summary in summaries):
        return ":x: needs attention"
    if any(summary["warning_count"] > 0 for summary in summaries):
        return ":warning: warnings"
    return ":white_check_mark: clean"


def section(text, fields=None):
    block = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": text},
    }
    if fields:
        block["fields"] = [{"type": "mrkdwn", "text": field} for field in fields]
    return block


def render_group_section(title, groups):
    if not groups:
        return []

    lines = [f"*{title}:*"]
    sorted_groups = sorted(
        groups,
        key=lambda group: (-group["count"], str(group["rule_id"])),
    )
    for group in sorted_groups[:MAX_RULE_GROUPS]:
        label = f"Rule {group['rule_id']}: {group['rule_name']}"
        lines.append(f"- *{slack_escape(label)}* ({group['count']})")
        for item in group["items"][:MAX_EXAMPLES_PER_GROUP]:
            lines.append(f"  - {slack_escape(truncate(item))}")
    return lines


def findings_text(summary):
    if not summary["errors"] and not summary["warnings"]:
        return f"All {summary['rule_count']} validation rules passed."

    lines = []
    lines.extend(render_group_section("Top errors", summary["errors"]))
    if summary["errors"] and summary["warnings"]:
        lines.append("")
    lines.extend(render_group_section("Top warnings", summary["warnings"]))
    return "\n".join(lines)


def fallback_text(summaries):
    parts = [
        f"{summary['product']}: {product_status(summary)} "
        f"({summary['error_count']} errors, {summary['warning_count']} warnings)"
        for summary in summaries
    ]
    return f"Daily Analytics Validation - {overall_status(summaries)} - " + "; ".join(parts)


def build_blocks(summaries):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Daily Analytics Validation",
                "emoji": True,
            },
        }
    ]

    run_url = github_run_url()
    context = f"*Run time:* {timestamp}"
    if run_url:
        context += f" | <{run_url}|View GitHub run>"
    blocks.append(
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": context}],
        }
    )
    blocks.append(
        section(
            f"*Overall:* {overall_status(summaries)}\n"
            f"*Products checked:* {len(summaries)}"
        )
    )
    blocks.append({"type": "divider"})

    for index, summary in enumerate(summaries):
        if len(blocks) > MAX_BLOCKS - 4:
            remaining = len(summaries) - index
            blocks.append(
                section(
                    f"*{remaining} additional product"
                    f"{'s' if remaining != 1 else ''} omitted from Slack.*\n"
                    "Open the GitHub run for full validator output."
                )
            )
            break

        fields = [
            f"*Status*\n{product_status(summary)}",
            f"*Errors*\n{summary['error_count']}",
            f"*Warnings*\n{summary['warning_count']}",
            f"*Exit code*\n{summary['exit_code']}",
        ]
        blocks.append(section(f"*{display_product(summary['product'])}*", fields=fields))
        blocks.append(section(findings_text(summary)))
        if index != len(summaries) - 1 and len(blocks) < MAX_BLOCKS:
            blocks.append({"type": "divider"})

    return blocks[:MAX_BLOCKS]


def build_payload(summaries):
    return {
        "text": fallback_text(summaries),
        "blocks": build_blocks(summaries),
    }


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
    summaries = [run_validator_with_fallback(product) for product in products]
    payload = build_payload(summaries)

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
