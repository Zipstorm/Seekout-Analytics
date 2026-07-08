import importlib.util
import io
import json
import unittest
from contextlib import redirect_stderr
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run-daily-validation.py"

spec = importlib.util.spec_from_file_location("run_daily_validation", SCRIPT_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def summary(
    product="helix",
    exit_code=0,
    error_count=0,
    warning_count=0,
    errors=None,
    warnings=None,
):
    return {
        "product": product,
        "exit_code": exit_code,
        "rule_count": 17,
        "error_count": error_count,
        "warning_count": warning_count,
        "suppressed_warning_count": 0,
        "errors": errors or [],
        "warnings": warnings or [],
    }


class DailyValidationPayloadTests(unittest.TestCase):
    def test_payload_has_fallback_and_distinct_product_sections(self):
        payload = runner.build_payload(
            [
                summary(
                    product="helix",
                    exit_code=1,
                    error_count=2,
                    errors=[
                        {
                            "rule_id": 16,
                            "rule_name": "Result terminal form",
                            "count": 2,
                            "items": ["Auth Failed must end with Rejected"],
                        }
                    ],
                ),
                summary(product="recruit"),
            ]
        )

        self.assertIn("text", payload)
        self.assertIn("blocks", payload)
        self.assertLessEqual(len(payload["blocks"]), runner.MAX_BLOCKS)
        encoded = json.dumps(payload)
        self.assertIn("Helix", encoded)
        self.assertIn("Recruit", encoded)
        self.assertIn(":x: needs attention", encoded)
        self.assertIn(":white_check_mark: clean", encoded)
        self.assertNotIn("stdout", encoded)

    def test_exit_two_summary_renders_as_config_issue(self):
        config_summary = summary(
            exit_code=2,
            error_count=1,
            errors=[
                {
                    "rule_id": "config",
                    "rule_name": "Configuration",
                    "count": 1,
                    "items": ["File not found: docs/helix/event-catalog.md"],
                }
            ],
        )
        payload = runner.build_payload([config_summary])
        encoded = json.dumps(payload)

        self.assertIn(":octagonal_sign: config issue", encoded)
        self.assertIn("Configuration", encoded)
        self.assertIn("File not found", encoded)

    def test_findings_are_capped_and_examples_are_truncated(self):
        groups = []
        for rule_id in range(1, 5):
            groups.append(
                {
                    "rule_id": rule_id,
                    "rule_name": f"Rule {rule_id}",
                    "count": 10 - rule_id,
                    "items": [
                        "x" * (runner.MAX_EXAMPLE_CHARS + 20),
                        "second example",
                        "third example",
                    ],
                }
            )
        text = runner.findings_text(
            summary(exit_code=1, error_count=30, errors=groups)
        )

        self.assertIn("Top errors", text)
        self.assertIn("Rule 1", text)
        self.assertIn("Rule 2", text)
        self.assertIn("Rule 3", text)
        self.assertNotIn("Rule 4", text)
        self.assertIn("...", text)
        self.assertEqual(text.count("third example"), 0)

    def test_warnings_render_when_errors_also_exist(self):
        text = runner.findings_text(
            summary(
                exit_code=1,
                error_count=1,
                warning_count=1,
                errors=[
                    {
                        "rule_id": 1,
                        "rule_name": "Error rule",
                        "count": 1,
                        "items": ["error example"],
                    }
                ],
                warnings=[
                    {
                        "rule_id": 2,
                        "rule_name": "Warning rule",
                        "count": 1,
                        "items": ["warning example"],
                    }
                ],
            )
        )

        self.assertIn("Top errors", text)
        self.assertIn("error example", text)
        self.assertIn("Top warnings", text)
        self.assertIn("warning example", text)

    def test_parse_summary_rejects_malformed_json_and_missing_keys(self):
        with self.assertRaisesRegex(RuntimeError, "not valid JSON"):
            runner.parse_summary("helix", "Validating product: helix")

        missing = json.dumps({"product": "helix"})
        with self.assertRaisesRegex(RuntimeError, "missing required keys"):
            runner.parse_summary("helix", missing)

    def test_run_validator_fallback_synthesizes_product_summary(self):
        original = runner.run_validator

        def fail(_product):
            raise RuntimeError("bad json")

        runner.run_validator = fail
        try:
            with redirect_stderr(io.StringIO()):
                summary = runner.run_validator_with_fallback("helix")
        finally:
            runner.run_validator = original

        self.assertEqual(summary["product"], "helix")
        self.assertEqual(summary["exit_code"], 2)
        self.assertEqual(summary["errors"][0]["rule_id"], "automation")
        self.assertIn("bad json", summary["errors"][0]["items"][0])


if __name__ == "__main__":
    unittest.main()
