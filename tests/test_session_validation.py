"""Regression coverage for JSON ingress, budgets and preflight artifacts."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.run_session import parse_commands

ROOT = Path(__file__).resolve().parents[1]


class SessionValidationTests(unittest.TestCase):
    def validate(self, commands, **metadata):
        doc = {"format": "sandspiel-lab-session/v1", "commands": commands, **metadata}
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "session.json"
            source.write_text(json.dumps(doc), encoding="utf-8")
            return parse_commands(source)

    def refuse(self, commands, reason, **metadata):
        with self.assertRaisesRegex(ValueError, reason):
            self.validate(commands, **metadata)

    def test_valid_maximum_tick_budget(self):
        accepted = self.validate([
            {"op": "paint", "x": 12, "y": 15, "material": "Wood"},
            {"op": "step", "ticks": 240},
            {"op": "step", "ticks": 240},
            {"op": "step", "ticks": 120},
        ])
        self.assertEqual(len(accepted["commands"]), 4)

    def test_negative_offset_cannot_bypass_600_tick_budget(self):
        self.refuse([{"op": "step", "ticks": n} for n in (240, 240, 240, -120)], "budget exceeded")
        self.refuse([{"op": "step", "ticks": n} for n in (240, 240, -120)], "ticks must")
        self.refuse([{"op": "step", "ticks": 0}], "ticks must")
        self.refuse([{"op": "step", "ticks": 241}], "ticks must")
        self.refuse([{"op": "step", "ticks": True}], "ticks must")

    def test_non_string_operations_refused_cleanly(self):
        for op in ([], {}, None, 0, True):
            with self.subTest(op=op):
                self.refuse([{"op": op}], "unsupported operation")

    def test_boolean_options_are_strict(self):
        self.refuse([{"op": "rect", "x": 1, "y": 1, "width": 10, "height": 10,
                      "material": "Wood", "fill": "false"}], "fill must be boolean")
        self.refuse([{"op": "inspect", "x": 1, "y": 1, "width": 2, "height": 2,
                      "includeCells": "false"}], "includeCells must be boolean")
        self.refuse([{"op": "pause", "capture": "true"}], "capture must be boolean")
        self.refuse([{"op": "paint", "x": 1, "y": 2, "material": "Wood",
                      "expectedRevision": False}], "expectedRevision")

    def test_invalid_batch_generates_preflight_evidence_without_browser(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "session.json"
            output = Path(temp) / "evidence"
            source.write_text(json.dumps({"format": "sandspiel-lab-session/v1",
                                          "commands": [{"op": "step", "ticks": -3}]}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/run_session.py"),
                 "--commands", str(source), "--out", str(output)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "refused")
            self.assertEqual(report["stage"], "preflight")
            self.assertEqual(report["commands_applied"], 0)
            self.assertEqual(report["ticks"], 0)
            self.assertEqual(json.loads((output / "session.json").read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main()
