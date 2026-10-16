"""Keep failed Windows test diagnostics visible without weakening pytest's exit code."""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "ci" / "report_test_failures.py"


def report(path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True, check=False
    )


def test_failure_and_error_annotations_escape_workflow_commands(tmp_path):
    path = tmp_path / "results.xml"
    path.write_text(
        '<testsuites><testsuite><testcase name="failed"><failure>one%\ntwo</failure></testcase><testcase name="broken"><error message="setup failed"/></testcase></testsuite></testsuites>',
        encoding="utf-8",
    )
    result = report(path)
    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "::error::failed%0Aone%25%0Atwo",
        "::error::broken%0Asetup failed",
    ]


def test_passing_cases_do_not_emit_false_errors(tmp_path):
    path = tmp_path / "results.xml"
    path.write_text(
        '<testsuites><testsuite><testcase name="passed"/></testsuite></testsuites>',
        encoding="utf-8",
    )
    result = report(path)
    assert result.returncode == 0
    assert not result.stdout


def test_missing_report_is_visible(tmp_path):
    result = report(tmp_path / "missing.xml")
    assert result.returncode == 0
    assert result.stdout.startswith("::warning::Pytest did not produce")
