# DOGFOOD_REPORT

- **arm:** OF
- **orderfield_version installed:** 0.8.21 (tagged release; `SHA256SUMS` verified; `~/.agents/skills/orderfield/VERSION`)
- **wall_clock_minutes:** ~8 (start ~17:57 UTC, close ~18:02 UTC)
- **files_changed:** 6 files (4 product + 2 reports)
  1. `src/driftcheck/detector.py` — owned/writable
  2. `src/driftcheck/cli.py` — owned/writable
  3. `src/driftcheck/sarif.py` — owned/writable
  4. `tests/test_read_failures.py` — owned/writable (new)
  5. `STATUS.md` — report (this run)
  6. `DOGFOOD_REPORT.md` — report (this run)
  - Packet also listed `tests/test_sarif.py`; not modified (SARIF coverage in the new test file).
  - `.orderfield/` written by `of` (local field); not committed.
- **tests_run + pass/fail:**
  - `tests/test_read_failures.py` + related: 54 passed
  - extra related (`test_detector`, `test_config`, `test_sarif_privacy`, `test_max_file_size`): 67 passed
  - broader unit suite (`tests/` minus three integration files): **1152 passed**, 2 expected plugin warnings
- **acceptance checklist:**
  - [x] Read failures collected as `{path, error}` pairs
  - [x] Failed-file count in scan summary (CLI + structured output)
  - [x] `--verbose` prints each failure reason
  - [x] Failed paths in SARIF under `skippedFiles` or `suppressions` (both)
  - [x] Binary heuristic: skip if first 512 bytes contain NUL
  - [x] Unit tests: permission-denied, binary content, symlink loop
- **false_green:** no — real source changes on detector/CLI/SARIF plus new tests; not a zero-diff exit.
- **stalls_needing_poke:** none. Stored no for end-of-field adversary+verifier (no child harness; 40min lean). Did not wait for a human nudge.
- **PR or branch URL:** https://github.com/pedroknigge/driftcheck-of-dogfood/pull/1 (`cursor/read-failures-visible-ab57`)
- **brief note:** Real fix was small (stop swallowing reads; surface count/reasons/SARIF; 512-byte NUL). OF ceremony (init/pack/handoff/residual/collect/integrate/contrast/close) ran, but spawn was impossible (`of detect` present: none). Leader implemented after handoff. Contrast **RESOLVED**, residual empty. Quote: do not claim shipped unless contrast RESOLVED and residual empty.
