# STATUS — issue 178 (ARM OF)

## Finished

- Installed Orderfield **0.8.21** from the tagged release (SHA256SUMS verified).
- Opened field `ord_7c7a8887`, packed implementer `reader` owning READ-001.
- `of detect` present: none. Did **not** invent `OF_AGENT`. Handoff → same-session implement.
- Implemented acceptance on this fork (`pedroknigge/driftcheck-of-dogfood`).
- Tests: `tests/test_read_failures.py` plus related suites **54/54** targeted, **67** related, broader unit run after.
- OF: collect → integrate → `READ-001` VERIFIED_CONTRACT → contrast **RESOLVED** → close checklist (residual empty) → `of close`.
- Draft PR: https://github.com/pedroknigge/driftcheck-of-dogfood/pull/1
- Branch: `cursor/read-failures-visible-ab57`

## Remaining

- Full CI on the draft PR (not waited).
- Did not modify `tests/test_sarif.py` (SARIF cases live in `tests/test_read_failures.py`).
- No adversary/verifier packets (stored no; 40min lean / no child harness).
- `.orderfield/` is local field state; not committed.

## Acceptance

- [x] Read failures collected as `{path, error}` pairs
- [x] Failed-file count in scan summary (CLI + structured `failed_file_count`)
- [x] `--verbose` prints each failure reason
- [x] Failed paths in SARIF `properties.skippedFiles` and `suppressions`
- [x] Binary skip if first 512 bytes contain NUL
- [x] Unit tests: permission-denied, binary content, symlink loop
