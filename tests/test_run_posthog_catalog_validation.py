import importlib.util
import io
import json
import tempfile
import unittest
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run-posthog-catalog-validation.py"

spec = importlib.util.spec_from_file_location("run_posthog_catalog_validation", SCRIPT_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate-analytics-docs.py"
validator_spec = importlib.util.spec_from_file_location("validate_analytics_docs", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(validator)


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        return False

    def read(self):
        if isinstance(self.payload, bytes):
            return self.payload
        return json.dumps(self.payload).encode("utf-8")


class PropertyQualifierTests(unittest.TestCase):
    def test_parse_properties_cell_preserves_optional_and_scope_qualifiers(self):
        specs, enums = runner.parse_properties_cell(
            validator,
            "`target_job_title` (optional), `is_job_specific` (boolean), "
            "`entry_point` (login page only), `action`: `click` | `submit`",
        )
        by_name = {spec.name: spec for spec in specs}

        self.assertTrue(by_name["target_job_title"].optional)
        self.assertEqual(by_name["target_job_title"].optional_reason, "optional")
        self.assertFalse(by_name["is_job_specific"].optional)
        self.assertTrue(by_name["entry_point"].optional)
        self.assertEqual(by_name["entry_point"].optional_reason, "scope")
        self.assertFalse(by_name["action"].optional)
        self.assertEqual(enums["action"], ["click", "submit"])

    def test_expected_catalog_event_filtering(self):
        events = {
            "Live Event": runner.RuntimeEvent("Live Event", "", "", "", [], {}, "", "Live", ""),
            "Legacy Event": runner.RuntimeEvent("Legacy Event", "", "", "", [], {}, "", "Live (legacy)", ""),
            "Dev Event": runner.RuntimeEvent("Dev Event", "", "", "", [], {}, "", "Dev", ""),
            "Not Started": runner.RuntimeEvent("Not Started", "", "", "", [], {}, "", "Not Started", ""),
        }

        self.assertEqual(
            set(runner.expected_catalog_events(events)),
            {"Live Event", "Legacy Event"},
        )


class RuntimeValidationTests(unittest.TestCase):
    def test_required_key_presence_allows_blank_but_flags_missing(self):
        summary = runner.ProductRuntimeSummary(product="helix")
        event = runner.RuntimeEvent(
            name="Login Started Button Clicked",
            area="Account",
            event_type="Interaction",
            source="Frontend",
            properties=[
                runner.PropertySpec("action"),
                runner.PropertySpec("action_value"),
                runner.PropertySpec("entry_point", "login page only", optional=True, optional_reason="scope"),
            ],
            inline_enums={},
            group="",
            status="Live",
            section="Login",
        )
        prop_dict = {
            "action": [{"type": "enum", "allowed_values": ["click"], "used_in": []}],
            "action_value": [{"type": "string", "allowed_values": [], "used_in": []}],
        }
        schema_event_props = {
            "action": {"when": "All `user_action` events"},
            "action_value": {"when": "All `user_action` events"},
            "component": {"when": "All `user_action` events"},
        }

        runner.validate_samples(
            summary,
            event,
            [{"properties": {"action": "", "action_value": ""}}],
            prop_dict,
            schema_event_props,
        )

        messages = [finding.message for finding in summary.errors]
        self.assertFalse(any("`action`" in message for message in messages))
        self.assertFalse(any("`action_value`" in message for message in messages))
        self.assertTrue(any("`component`" in message for message in messages))
        self.assertFalse(any("`entry_point`" in message for message in messages))

    def test_declared_type_validation_uses_catalog_buckets_only(self):
        summary = runner.ProductRuntimeSummary(product="helix")
        event = runner.RuntimeEvent(
            name="Candidate Interview Started",
            area="Prospect",
            event_type="Started",
            source="Frontend",
            properties=[
                runner.PropertySpec("input_mode"),
                runner.PropertySpec("questions_count"),
                runner.PropertySpec("has_resume"),
                runner.PropertySpec("link_types"),
                runner.PropertySpec("job_id"),
                runner.PropertySpec("current_page_context"),
            ],
            inline_enums={},
            group="job",
            status="Live",
            section="Interview",
        )
        prop_dict = {
            "input_mode": [{"type": "enum", "allowed_values": ["text", "voice"], "used_in": []}],
            "questions_count": [{"type": "number", "allowed_values": [], "used_in": []}],
            "has_resume": [{"type": "boolean", "allowed_values": [], "used_in": []}],
            "link_types": [{"type": "array", "allowed_values": [], "used_in": []}],
            "job_id": [{"type": "UUID", "allowed_values": [], "used_in": []}],
            "current_page_context": [{"type": "string", "allowed_values": [], "used_in": []}],
        }

        runner.validate_samples(
            summary,
            event,
            [
                {
                    "properties": {
                        "input_mode": "video",
                        "questions_count": "3",
                        "has_resume": "true",
                        "link_types": "github",
                        "job_id": "not-a-uuid",
                        "current_page_context": "foo_at",
                    }
                }
            ],
            prop_dict,
            {},
        )

        encoded = "\n".join(finding.message for finding in summary.errors)
        self.assertIn("input_mode", encoded)
        self.assertIn("questions_count", encoded)
        self.assertIn("has_resume", encoded)
        self.assertIn("link_types", encoded)
        self.assertIn("job_id", encoded)
        self.assertNotIn("current_page_context", encoded)

    def test_sample_findings_are_aggregated_instead_of_per_row(self):
        summary = runner.ProductRuntimeSummary(product="helix")
        event = runner.RuntimeEvent(
            name="Create Job Button Clicked",
            area="Hiring",
            event_type="Interaction",
            source="Frontend",
            properties=[runner.PropertySpec("action")],
            inline_enums={},
            group="",
            status="Live",
            section="Hiring",
        )

        runner.validate_samples(
            summary,
            event,
            [{"properties": {"action": "click"}}, {"properties": {"action": "click"}}],
            {"action": [{"type": "enum", "allowed_values": ["click"], "used_in": []}]},
            {"component": {"when": "All `user_action` events"}},
        )

        self.assertEqual(summary.error_count, 1)
        self.assertIn("`component`", summary.errors[0].message)
        self.assertIn("2/2 sampled rows", summary.errors[0].message)

    def test_inline_enum_allowlists_are_validated_without_dictionary_entry(self):
        summary = runner.ProductRuntimeSummary(product="helix")
        event = runner.RuntimeEvent(
            name="Inline Enum Event",
            area="Test",
            event_type="Interaction",
            source="Frontend",
            properties=[runner.PropertySpec("action")],
            inline_enums={"action": ["click"]},
            group="",
            status="Live",
            section="Test",
        )

        runner.validate_samples(
            summary,
            event,
            [{"properties": {"action": "submit"}}, {"properties": {"action": "submit"}}],
            {},
            {},
        )

        self.assertEqual(summary.error_count, 1)
        self.assertEqual(summary.errors[0].rule_id, "enum_drift")
        self.assertIn("2/2 sampled rows", summary.errors[0].message)

    def test_uncataloged_event_drift_reports_truncation(self):
        summary = runner.ProductRuntimeSummary(product="helix")
        now = datetime(2026, 7, 8, tzinfo=timezone.utc)
        event_defs = {
            f"Unexpected Event {i}": {"last_seen_at": "2026-07-08T00:00:00Z"}
            for i in range(22)
        }

        runner.collect_event_drift(summary, {}, event_defs, set(), now, 7)

        messages = [finding.message for finding in summary.warnings]
        self.assertEqual(len(summary.warnings), 21)
        self.assertTrue(any("additional recent uncataloged events" in msg for msg in messages))


class ApiShapeTests(unittest.TestCase):
    def test_normalize_query_results_supports_rows_with_columns(self):
        rows = runner.normalize_query_results(
            {
                "columns": ["event", "timestamp", "properties"],
                "results": [["Page Viewed", "2026-07-08T00:00:00Z", {"foo": "bar"}]],
            }
        )

        self.assertEqual(rows[0]["event"], "Page Viewed")
        self.assertEqual(rows[0]["properties"], {"foo": "bar"})

    def test_load_config_indexes_products(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump(
                {
                    "products": [
                        {
                            "product": "helix",
                            "host": "https://us.posthog.com",
                            "project_id": "123",
                            "api_key_env": "POSTHOG_HELIX_PERSONAL_API_KEY",
                        }
                    ]
                },
                tmp,
            )
            tmp_path = Path(tmp.name)
        self.addCleanup(tmp_path.unlink)

        config = runner.load_posthog_config(tmp_path)

        self.assertEqual(config["helix"].project_id, "123")
        self.assertEqual(config["helix"].host, "https://us.posthog.com")

    def test_freshness_splits_old_and_missing_timestamps(self):
        now = datetime(2026, 7, 8, tzinfo=timezone.utc)
        self.assertFalse(runner.is_fresh(None, now, 7))
        self.assertFalse(runner.is_fresh("2026-06-01T00:00:00Z", now, 7))
        self.assertTrue(runner.is_fresh("2026-07-07T00:00:00Z", now, 7))

    def test_posthog_client_paginates_and_sends_auth_header(self):
        client = runner.PostHogClient("https://us.posthog.com", "123", "secret")
        requests = []
        responses = [
            FakeResponse({"results": [{"name": "one"}], "next": "https://next.example/page"}),
            FakeResponse({"results": [{"name": "two"}], "next": None}),
        ]

        def fake_urlopen(request, timeout):
            requests.append((request, timeout))
            return responses.pop(0)

        with mock.patch.object(runner.urllib.request, "urlopen", side_effect=fake_urlopen):
            rows = client.get_paginated("event_definitions/", {"limit": 1})

        self.assertEqual([row["name"] for row in rows], ["one", "two"])
        self.assertEqual(requests[0][0].headers["Authorization"], "Bearer secret")
        self.assertEqual(requests[0][1], 30)

    def test_posthog_client_rejects_malformed_json(self):
        client = runner.PostHogClient("https://us.posthog.com", "123", "secret")

        with mock.patch.object(
            runner.urllib.request,
            "urlopen",
            return_value=FakeResponse(b"not-json"),
        ):
            with self.assertRaisesRegex(runner.AutomationError, "invalid JSON"):
                client.get_paginated("event_definitions/")

    def test_posthog_client_wraps_http_and_url_errors(self):
        client = runner.PostHogClient("https://us.posthog.com", "123", "secret")
        http_error = urllib.error.HTTPError(
            "https://us.posthog.com",
            403,
            "Forbidden",
            {},
            io.BytesIO(b"missing scope"),
        )

        with mock.patch.object(runner.urllib.request, "urlopen", side_effect=http_error):
            with self.assertRaisesRegex(runner.AutomationError, "HTTP 403"):
                client.get_paginated("event_definitions/")

        url_error = urllib.error.URLError("timed out")
        with mock.patch.object(runner.urllib.request, "urlopen", side_effect=url_error):
            with self.assertRaisesRegex(runner.AutomationError, "request failed"):
                client.get_paginated("event_definitions/")

    def test_posthog_client_config_validation(self):
        with self.assertRaisesRegex(runner.AutomationError, "personal API key"):
            runner.PostHogClient("https://us.posthog.com", "123", "")


if __name__ == "__main__":
    unittest.main()
