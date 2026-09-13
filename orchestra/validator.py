from __future__ import annotations

import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from orchestra.catalog import Incident
from orchestra.fixer import apply_changes, build_fix
from orchestra.paths import SAMPLE


def _clear_imported_suites() -> None:
    for name in list(sys.modules):
        if name == "reportly" or name.startswith("reportly.") or name.startswith("test_"):
            del sys.modules[name]


def run_suite(root: Path, pattern: str = "test_*.py") -> dict:
    added = str(root)
    sys.path.insert(0, added)
    _clear_imported_suites()
    stream = io.StringIO()
    try:
        suite = unittest.TestLoader().discover(str(root / "tests"), pattern=pattern)
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        failed = len(result.failures) + len(result.errors)
        return {
            "total": result.testsRun,
            "failed": failed,
            "passed": result.testsRun - failed,
            "output": stream.getvalue(),
        }
    finally:
        if sys.path and sys.path[0] == added:
            sys.path.pop(0)
        _clear_imported_suites()


def validate_incident(incident: Incident) -> dict:
    plan = build_fix(incident)
    baseline = run_suite(SAMPLE)
    before_dir = Path(tempfile.mkdtemp(prefix="orchestra-before-"))
    after_dir = Path(tempfile.mkdtemp(prefix="orchestra-after-"))
    try:
        shutil.copytree(SAMPLE, before_dir, dirs_exist_ok=True)
        shutil.copytree(SAMPLE, after_dir, dirs_exist_ok=True)
        tests_only = [item for item in plan["changes"] if item["file"].startswith("tests/")]
        apply_changes(before_dir, tests_only)
        apply_changes(after_dir, plan["changes"])
        regression_before = run_suite(before_dir, "test_orchestra_regression.py")
        after_fix = run_suite(after_dir)
    finally:
        shutil.rmtree(before_dir, ignore_errors=True)
        shutil.rmtree(after_dir, ignore_errors=True)
    return {
        "baseline": baseline,
        "regression_before": regression_before,
        "after_fix": after_fix,
        "added_tests": plan["tests"],
    }
