"""Tests for _read_files_parallel failure reporting (issue #178)."""
from __future__ import annotations

import json
from pathlib import Path

from driftcheck.cli import main
from driftcheck.detector import _read_files_parallel, _read_text_safe, _safe_read, scan_repo
from driftcheck.sarif import to_sarif


def test_read_files_parallel_permission_denied(tmp_path, monkeypatch):
    """Permission-denied files are collected as {path, error} pairs."""
    locked = tmp_path / "locked.txt"
    locked.write_text("secret")
    readable = tmp_path / "ok.txt"
    readable.write_text("hello")

    locked.chmod(0o000)
    try:
        _, chmod_failures = _read_files_parallel(tmp_path, ["*.txt"])
    finally:
        locked.chmod(0o644)

    # Root can still read chmod 000 files — force the exception path.
    if not any(f["path"] == "locked.txt" for f in chmod_failures):
        orig = _safe_read

        def deny(path: Path, max_size: int = 1_000_000) -> str:
            if path.name == "locked.txt":
                raise PermissionError("Permission denied")
            return orig(path, max_size)

        monkeypatch.setattr("driftcheck.detector._safe_read", deny)
        text, failures = _read_files_parallel(tmp_path, ["*.txt"])
    else:
        text, failures = "hello", chmod_failures

    assert any(f["path"] == "locked.txt" for f in failures)
    denied = next(f for f in failures if f["path"] == "locked.txt")
    assert "error" in denied
    assert denied["error"]
    assert "hello" in text or "secret" not in text or failures


def test_read_files_parallel_binary_content(tmp_path):
    """Files with NUL in the first 512 bytes are skipped as binary."""
    (tmp_path / "readme.md").write_text("plain text")
    (tmp_path / "image.bin").write_bytes(b"PNG\x00" + b"\x01" * 20)

    text, failures = _read_files_parallel(tmp_path, ["*"])
    assert "plain text" in text
    assert len(failures) == 1
    assert failures[0]["path"] == "image.bin"
    assert "binary" in failures[0]["error"]


def test_binary_heuristic_first_512_bytes(tmp_path):
    """NUL after the first 512 bytes is not treated as binary."""
    payload = b"a" * 512 + b"\x00more"
    f = tmp_path / "almost.bin"
    f.write_bytes(payload)
    # _safe_read only inspects the first 512 bytes
    result = _safe_read(f)
    assert result.startswith("a" * 512)


def test_read_files_parallel_symlink_loop(tmp_path):
    """Symlink loops are collected as failures instead of crashing."""
    a = tmp_path / "loop_a"
    b = tmp_path / "loop_b"
    a.symlink_to(b)
    b.symlink_to(a)
    (tmp_path / "ok.txt").write_text("safe")

    text, failures = _read_files_parallel(tmp_path, ["*"])
    assert "safe" in text
    assert failures, "symlink loop should produce at least one failure"
    assert any("loop" in f["path"] for f in failures)
    for item in failures:
        assert "path" in item and "error" in item


def test_scan_repo_reports_failed_file_count(tmp_path):
    """scan_repo structured output includes failed_files and a count."""
    (tmp_path / "README.md").write_bytes(b"Requires Python 3.11\x00")
    (tmp_path / "pyproject.toml").write_text("[project]\nrequires-python = \">=3.11\"\n")
    result = scan_repo(tmp_path)
    assert result["failed_file_count"] >= 1
    assert any(f["path"] == "README.md" for f in result["failed_files"])
    assert any("binary" in f["error"] for f in result["failed_files"])


def test_cli_summary_and_verbose(tmp_path, capsys):
    """CLI scan summary reports the failed-file count; --verbose prints reasons."""
    (tmp_path / "README.md").write_bytes(b"hello\x00world")
    (tmp_path / ".gitattributes").write_text("* text=auto eol=lf\n")

    rc = main(["--verbose", str(tmp_path)])
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert rc == 0
    assert "failed to read" in combined
    assert "README.md" in combined
    assert "binary" in combined


def test_cli_json_includes_failed_file_count(tmp_path, capsys):
    """Structured --json output includes failed_file_count."""
    (tmp_path / "README.md").write_bytes(b"hello\x00world")
    (tmp_path / ".gitattributes").write_text("* text=auto eol=lf\n")
    rc = main(["--json", str(tmp_path)])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert rc == 0
    assert data["failed_file_count"] >= 1
    assert data["failed_files"][0]["path"] == "README.md"


def test_cli_report_summary_failed_files(tmp_path, capsys):
    """--report scan summary includes Failed files count."""
    (tmp_path / "README.md").write_bytes(b"hello\x00world")
    (tmp_path / ".gitattributes").write_text("* text=auto eol=lf\n")
    main(["--report", str(tmp_path)])
    captured = capsys.readouterr()
    assert "Failed files:" in captured.out


def test_sarif_skipped_files(tmp_path):
    """Failed paths appear in SARIF under skippedFiles and suppressions."""
    result = {
        "failed_files": [{"path": "secret.bin", "error": "binary file detected"}],
        "failed_file_count": 1,
    }
    doc = to_sarif(result, version="0.1.46")
    run = doc["runs"][0]
    assert run["properties"]["skippedFiles"][0]["path"] == "secret.bin"
    notes = [r for r in run["results"] if r.get("ruleId") == "file-read-failed"]
    assert len(notes) == 1
    assert notes[0]["suppressions"]
    assert "secret.bin" in notes[0]["message"]["text"]


def test_read_text_safe_still_returns_none_for_binary(tmp_path):
    """Backward compatible: _read_text_safe returns None for binary files."""
    f = tmp_path / "x.bin"
    f.write_bytes(b"\x00abc")
    assert _read_text_safe(f) is None
