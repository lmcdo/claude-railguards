"""Tests for the QA-gate validator (config-driven schema validation)."""
import importlib.util
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "qa_gate", os.path.join(REPO, "plugins", "railguards", "scripts", "qa_gate.py")
)
qa_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qa_gate)

CFG = {
    "tiers": ["critical", "standard", "minor"],
    "min_break_it": {"critical": 5, "standard": 3, "minor": 0},
    "require_functions": {"critical": 1, "standard": 1, "minor": 0},
}


def _bi(n):
    return [{"scenario": f"s{i}", "what_happens": "x", "how": "y"} for i in range(n)]


def test_minimal_minor_report_passes():
    report = {"tier": "minor", "commit_hash": "abc1234", "files": ["a.py"],
              "justification": "tidy"}
    assert qa_gate.validate(report, CFG) == []


def test_unknown_tier_fails():
    errs = qa_gate.validate({"tier": "huge"}, CFG)
    assert any("tier must be one of" in e for e in errs)


def test_bad_commit_hash_fails():
    report = {"tier": "minor", "commit_hash": "zzz", "files": ["a.py"], "justification": "x"}
    assert any("commit_hash" in e for e in qa_gate.validate(report, CFG))


def test_empty_files_fails():
    report = {"tier": "minor", "commit_hash": "abc1234", "files": [], "justification": "x"}
    assert any("files" in e for e in qa_gate.validate(report, CFG))


def test_standard_requires_breakit_and_functions():
    report = {"tier": "standard", "commit_hash": "abc1234", "files": ["a.py"],
              "justification": "x", "break_it": _bi(1), "functions": []}
    errs = qa_gate.validate(report, CFG)
    assert any("break_it" in e for e in errs)
    assert any("functions" in e for e in errs)


def test_standard_passes_when_complete():
    report = {"tier": "standard", "commit_hash": "abc1234", "files": ["a.py"],
              "justification": "x", "break_it": _bi(3),
              "functions": [{"name": "f"}]}
    assert qa_gate.validate(report, CFG) == []


def test_breakit_entry_missing_field_fails():
    report = {"tier": "standard", "commit_hash": "abc1234", "files": ["a.py"],
              "justification": "x",
              "break_it": [{"scenario": "s", "what_happens": "", "how": "y"}] + _bi(2),
              "functions": [{"name": "f"}]}
    assert any("what_happens" in e for e in qa_gate.validate(report, CFG))


def test_critical_needs_five_breakit():
    report = {"tier": "critical", "commit_hash": "abc1234", "files": ["a.py"],
              "justification": "x", "break_it": _bi(4), "functions": [{"name": "f"}]}
    assert any(">= 5 break_it" in e for e in qa_gate.validate(report, CFG))
