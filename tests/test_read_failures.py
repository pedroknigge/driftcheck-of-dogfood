"""Tests for visible file-read failures (issue #178)."""
from __future__ import annotations

import json
from pathlib import Path

from driftcheck.cli import main
from driftcheck.detector import _read_files_parallel, scan_repo
from driftcheck.sarif import to_sarif


def test_read_files_parallel_binary_content(tmp_path):
    """Binary files (NUL in first 512 bytes) are recorded, not swallowed."""
    (tmp_path / "ok.txt").write_text("hello")
    (tmp_path / "blob.bin").write_bytes(b"PNG\x00" + b"\xff" * 32)
    text, failures = _read_files_parallel(tmp_path, ["*"])
    assert "hello" in text
    assert any(
        Path(item["path"]).name == "blob.bin" and "binary" in item["error"]
        for item in failures
    )


def test_read_files_parallel_permission_denied(tmp_path):
    """Permission-denied files are recorded as {path, error} pairs."""
    locked = tmp_path / "locked.txt"
    locked.write_text("secret")
    locked.chmod(0o000)
    try:
        _text, failures = _read_files_parallel(tmp_path, ["locked.txt"])
        if failures:
            assert failures[0]["path"] in {"locked.txt", str(locked)}
            assert failures[0]["error"]
        else:
            # Running as root can still read mode 000 files.
            assert locked.read_text() == "secret"
    finally:
        locked.chmod(0o644)


def test_read_files_parallel_symlink_loop(tmp_path):
    """Symlink loops are recorded instead of crashing or vanishing."""
    a = tmp_path / "loop-a"
    b = tmp_path / "loop-b"
    a.symlink_to(b)
    b.symlink_to(a)
    _text, failures = _read_files_parallel(tmp_path, ["loop-*"])
    assert isinstance(failures, list)
    assert any("loop" in item["path"] for item in failures)


def test_scan_repo_failed_file_count_and_pairs(tmp_path):
    """scan_repo exposes failed_file_count and {path, error} pairs."""
    (tmp_path / "README.md").write_bytes(b"docs\x00binary")
    (tmp_path / ".gitattributes").write_text("* text=auto eol=lf\n")
    result = scan_repo(tmp_path)
    assert result["failed_file_count"] >= 1
    assert any(
        item["path"] == "README.md" and "binary" in item["error"]
        for item in result["_skipped_files"]
    )


def test_cli_verbose_prints_failure_reason(tmp_path, capsys):
    """--verbose prints each failure reason; JSON includes the count."""
    (tmp_path / "README.md").write_bytes(b"docs\x00binary")
    (tmp_path / ".gitattributes").write_text("* text=auto eol=lf\n")
    code = main(["--verbose", "--json", str(tmp_path)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["failed_file_count"] >= 1
    assert "binary" in captured.err
    assert code in (0, 1)


def test_cli_summary_prints_failed_count(tmp_path, capsys):
    """Human CLI summary includes the failed-file count."""
    (tmp_path / "README.md").write_bytes(b"docs\x00binary")
    (tmp_path / ".gitattributes").write_text("* text=auto eol=lf\n")
    main([str(tmp_path)])
    captured = capsys.readouterr()
    assert "failed to read" in captured.out


def test_sarif_skipped_files_property_and_suppressions():
    """Failed paths appear in SARIF skippedFiles and suppressions."""
    result = {
        "failed_file_count": 1,
        "_skipped_files": [{"path": "vendor/font.woff2", "error": "binary file detected"}],
    }
    doc = to_sarif(result, version="0.0.0")
    run = doc["runs"][0]
    assert run["properties"]["skippedFiles"][0]["path"] == "vendor/font.woff2"
    notes = [r for r in run["results"] if r.get("ruleId") == "file-read-skipped"]
    assert len(notes) == 1
    assert notes[0]["suppressions"][0]["kind"] == "inSource"
    assert "binary" in notes[0]["message"]["text"]
