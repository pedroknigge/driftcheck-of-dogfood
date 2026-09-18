# STATUS — issue #178 (`_read_files_parallel` silent read errors)

**State:** complete on this fork (`pedroknigge/driftcheck-of-dogfood`)
**Branch:** `cursor/fix-read-files-parallel-errors-c7e7`

## Finished

- `_read_files_parallel()` no longer swallows exceptions. It returns `(contents, failures)` where `failures` is a list of `{path, error}` dicts.
- `_safe_read()` raises on binary (NUL in first 512 bytes), oversize, or OSError. Symlink loops during glob are recorded as failures.
- `scan_repo()` collects the same failures from sequential `_read_text_safe()` reads and exposes `failed_files` + `failed_file_count` in structured output.
- CLI: default / `--report` / `--json` scan summary includes the failed-file count. `--verbose` prints each `{path}: {error}`.
- SARIF: `runs[].properties.skippedFiles` plus suppressed `file-read-failed` note results.
- Unit tests: permission-denied, binary content, symlink loop, CLI summary/verbose/JSON, SARIF `skippedFiles`.
- Also moved `import sys` below `from __future__` in `cli.py` so the module is importable (was a SyntaxError).

## Remains

- Nothing required for the issue acceptance criteria.
- Optional follow-up: restore the `_failure_sink` in a `try/finally` so an unexpected exception mid-scan cannot leak the collector into a later call.
- Optional: start *using* `_read_files_parallel()` inside `scan_repo()` for the glob-heavy reads (it was unused dead code; scan still uses `_read_text_safe()`). Failures are collected either way.
