"""Unit tests for the object–action segregation logic in the analytics validator.

The validator script has a dash in its filename, so it is loaded by path via
importlib rather than imported normally.
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "validate-analytics-docs.py"
_spec = importlib.util.spec_from_file_location("validate_analytics_docs", _SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

# Representative Standard Objects, including nested prefixes to exercise
# longest-prefix and exact-equality matching.
OBJECTS = {
    "Job",
    "Job Wizard",
    "Job Wizard Step",
    "Auth",
    "Interest",
    "Review",
    "Chat",
    "Team Member",
    "Page",
    "Account",
}


class ObjectPrefixTests(unittest.TestCase):
    def test_exact_equality(self):
        self.assertEqual(mod._object_prefix("Job Wizard Step", OBJECTS), "Job Wizard Step")

    def test_longest_prefix_wins(self):
        self.assertEqual(
            mod._object_prefix("Job Wizard Step Completed", OBJECTS), "Job Wizard Step"
        )

    def test_unknown_prefix(self):
        self.assertIsNone(mod._object_prefix("Fnord Created", OBJECTS))


class SplitObjectActionTests(unittest.TestCase):
    def test_simple_past_tense(self):
        self.assertEqual(mod._split_object_action("Job Published", OBJECTS), ("Job", "Published"))

    def test_outcome_event(self):
        self.assertEqual(
            mod._split_object_action("Job Publish Failed", OBJECTS), ("Job", "Publish Failed")
        )

    def test_multiword_action(self):
        self.assertEqual(
            mod._split_object_action("Auth Session Restore Succeeded", OBJECTS),
            ("Auth", "Session Restore Succeeded"),
        )

    def test_exact_object_empty_action(self):
        self.assertEqual(
            mod._split_object_action("Job Wizard Step", OBJECTS), ("Job Wizard Step", "")
        )

    def test_unknown_prefix(self):
        self.assertEqual(mod._split_object_action("Fnord Bar", OBJECTS), (None, None))


class CandidateObjectTests(unittest.TestCase):
    def test_outcome_terminal_drops_two(self):
        self.assertEqual(mod._candidate_object("Pipeline Publish Failed"), "Pipeline")

    def test_variant_terminal_also_drops_two(self):
        self.assertEqual(mod._candidate_object("Pipeline Publish Error"), "Pipeline")

    def test_plain_event_drops_one(self):
        self.assertEqual(mod._candidate_object("Pipeline Created"), "Pipeline")

    def test_too_short_returns_none(self):
        self.assertIsNone(mod._candidate_object("Publish Failed"))


class ActionErrorsTests(unittest.TestCase):
    def test_passes_valid_actions(self):
        names = [
            "Review Decision Made",   # irregular past
            "Interest Withdrawn",     # irregular past
            "Job Publish Errored",    # canonical outcome terminal
            "Share Button Clicked",   # intent event, skipped
        ]
        self.assertEqual(mod._action_errors(names, OBJECTS), [])

    def test_flags_non_past_tense(self):
        errs = mod._action_errors(["Chat WebSocket Abnormal Close"], OBJECTS)
        self.assertEqual(len(errs), 1)
        self.assertIn("Chat WebSocket Abnormal Close", errs[0])

    def test_flags_garbage_action(self):
        self.assertEqual(len(mod._action_errors(["Job Fnord Xyz"], OBJECTS)), 1)

    def test_flags_only_object(self):
        errs = mod._action_errors(["Job Wizard Step"], OBJECTS)
        self.assertEqual(len(errs), 1)
        self.assertIn("only an object", errs[0])

    def test_skips_variant_terminal(self):
        # Variant outcome terminals are deferred to Rule 16, not flagged here.
        self.assertEqual(mod._action_errors(["Job Publish Success"], OBJECTS), [])

    def test_skips_unknown_object(self):
        # Unknown object prefix is owned by Rule 1 / TP7, not here.
        self.assertEqual(mod._action_errors(["Fnord Bar"], OBJECTS), [])


class OutcomeTerminalTests(unittest.TestCase):
    def test_success_wrong_terminal(self):
        errs = mod._outcome_terminal_errors([("Job Created", "Success")])
        self.assertEqual(len(errs), 1)
        self.assertIn("does not end in", errs[0])

    def test_success_correct(self):
        self.assertEqual(
            mod._outcome_terminal_errors([("Job Create Succeeded", "Success")]), []
        )

    def test_failure_accepts_failed_and_errored(self):
        self.assertEqual(
            mod._outcome_terminal_errors(
                [("Job Share Failed", "Failure"), ("Job Share Errored", "Failure")]
            ),
            [],
        )

    def test_error_variant_terminal(self):
        errs = mod._outcome_terminal_errors([("Chat WebSocket Error", "Error")])
        self.assertEqual(len(errs), 1)
        self.assertIn("Errored", errs[0])

    def test_error_correct(self):
        self.assertEqual(
            mod._outcome_terminal_errors([("Chat WebSocket Errored", "Error")]), []
        )

    def test_variant_is_type_independent(self):
        errs = mod._outcome_terminal_errors([("Job Publish Success", None)])
        self.assertEqual(len(errs), 1)
        self.assertIn("Succeeded", errs[0])

    def test_one_message_per_event(self):
        # Variant check and type check both apply; only one message is emitted.
        errs = mod._outcome_terminal_errors([("Job Publish Success", "Success")])
        self.assertEqual(len(errs), 1)


class EventTypeTests(unittest.TestCase):
    def test_invalid_types_flagged(self):
        typed = [
            ("A B", "--"),
            ("C D", "user_action"),
            ("E F", "page_view"),
            ("G H", ""),
        ]
        self.assertEqual(len(mod._event_type_errors(typed, mod.EVENT_TYPES)), 4)

    def test_all_enum_members_pass(self):
        typed = [(f"Obj{i} Acted", t) for i, t in enumerate(sorted(mod.EVENT_TYPES))]
        self.assertEqual(mod._event_type_errors(typed, mod.EVENT_TYPES), [])

    def test_none_type_skipped(self):
        self.assertEqual(mod._event_type_errors([("A B", None)], mod.EVENT_TYPES), [])

    def test_rule_17_missing_table_and_row_violations(self):
        catalog = {"Job Created": {"type": "--"}}
        errs, warns = mod.rule_17(catalog, set())
        self.assertEqual(warns, [])
        self.assertTrue(any("Event Types table not found" in e for e in errs))
        self.assertTrue(any("Job Created" in e and "Type" in e for e in errs))


class ParseTrackingPlanTests(unittest.TestCase):
    NEW_FORMAT = """# Tracking Plan: Test

## New Events

| Event | Area | Type | Trigger | Key Properties | Group | Property Updates |
|---|---|---|---|---|---|---|
| Job Created | Hiring | Success | server confirms | `job_id`, `surface` | `job` | -- |
"""

    # No Type column, plus an extra Source column between Trigger and Key
    # Properties — the real-world shape of hm-job-creation-wizard-v2.md.
    OLD_FORMAT = """# Tracking Plan: Test

## New Events

| Event | Area | Trigger | Source | Key Properties | Group | Property Updates |
|---|---|---|---|---|---|---|
| Job Created | Hiring | server confirms | Backend | `job_id`, `surface` | `job` | -- |
"""

    def _parse(self, body):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(body)
            path = Path(f.name)
        try:
            return mod.parse_tracking_plan(path)
        finally:
            path.unlink()

    def test_new_format_populates_type(self):
        events = self._parse(self.NEW_FORMAT).events
        self.assertIn("Job Created", events)
        self.assertEqual(events["Job Created"]["type"], "Success")
        # Header-keyed: properties read from the Key Properties column.
        self.assertIn("job_id", events["Job Created"]["properties"])

    def test_old_format_type_none(self):
        events = self._parse(self.OLD_FORMAT).events
        self.assertIn("Job Created", events)
        self.assertIsNone(events["Job Created"]["type"])
        # Header-keying reads Key Properties correctly despite the extra Source column.
        self.assertIn("job_id", events["Job Created"]["properties"])

    def test_old_format_tp12_missing_column(self):
        events = self._parse(self.OLD_FORMAT).events
        errs, _ = mod.tp_rule_12(events, mod.EVENT_TYPES)
        self.assertTrue(any('no "Type" column' in e for e in errs))

    def test_new_format_tp12_passes(self):
        events = self._parse(self.NEW_FORMAT).events
        errs, _ = mod.tp_rule_12(events, mod.EVENT_TYPES)
        self.assertEqual(errs, [])


if __name__ == "__main__":
    unittest.main()
