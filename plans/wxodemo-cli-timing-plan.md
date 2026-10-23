# wxodemo CLI — Deploy Improvements Plan

## Overview

Two improvements to the `wxodemo.py deploy` (and related) commands:

1. **`all` as a positional target** — `wxodemo.py deploy all` should work identically to `wxodemo.py deploy --all`. The same magic name must also work for `undeploy` and `status`, which share the same target-resolution path. `--all` flag remains unchanged.

2. **Timing for the deploy command** — Print start time, stop time, and elapsed duration after a real deploy finishes (not on `--dry-run`). Format: `HH:MM:SS` for start/stop, `HH:MM:SS` for elapsed. Timing is only added to `deploy`, not `undeploy` or `status`.

---

## Sub-Task 1 — Accept `"all"` as a positional target name

**Intent**  
Allow users to type `wxodemo.py deploy all` (or `undeploy all`, `status all`) instead of having to know about the `--all` flag. The keyword `"all"` in the `targets` list is intercepted and treated as if `--all` was passed.

**Expected Outcomes**  
- `wxodemo.py deploy all` deploys everything (same as `--all`).
- `wxodemo.py undeploy all` and `wxodemo.py status all` work the same way.
- `--all` flag continues to work unchanged.
- Combining `all` with `--kind` works (e.g. `wxodemo.py deploy all --kind scenario`).
- Any other target name is unaffected.

**Todo List**  
- [ ] In `src/wxodemo/cli.py`, modify `_select()`: if `"all"` is present in `args.targets`, remove it from the list and set `select_all=True` before calling `resolve_targets`.

**Relevant Context**  
- [`src/wxodemo/cli.py`](../src/wxodemo/cli.py) — `_select()` at line 72, `add_targets()` at line 221.
- `resolve_targets()` is called with `select_all=args.all`; that kwarg is the toggle to flip.
- No changes needed in `deploy.py`, `discovery.py`, or `build_parser()`.

**Status** `[x] done`

---

## Sub-Task 2 — Add timing to the deploy command

**Intent**  
Show the wall-clock start time, end time, and elapsed duration after a real (non-dry-run) deploy completes. This lets users see how fast deployments are.

**Expected Outcomes**  
- After a successful real deploy the output includes three lines (or a compact single line) such as:
  ```
  Started:  10:32:01
  Finished: 10:32:47
  Elapsed:  00:00:46
  ```
- No timing output on `--dry-run` runs.
- No timing added to `undeploy` or `status`.

**Todo List**  
- [ ] In `src/wxodemo/deploy.py`, add `import time` and `import datetime` (or `from datetime import datetime`) at the top.
- [ ] In `run_deploy()`, record `start = time.monotonic()` and `start_dt = datetime.now()` before the login/execute block (but after the dry-run guard — only when `not dry_run`).
- [ ] After the final `ok(f"Deployed {len(ordered)} target(s)")` line, record `end_dt = datetime.now()`, compute elapsed seconds from `time.monotonic()`, and print start, finish, and elapsed using the existing `plain()` or `ok()` output helpers.
- [ ] Format all three values as `HH:MM:SS` (use `strftime("%H:%M:%S")` for start/end, `str(timedelta(seconds=round(elapsed)))` for elapsed).

**Relevant Context**  
- [`src/wxodemo/deploy.py`](../src/wxodemo/deploy.py) — `run_deploy()` at line 214.
- `time` is already imported in `src/wxodemo/adk.py` — same pattern.
- Output helpers `ok()`, `plain()` are imported from `logging_setup` in `deploy.py`.
- The dry-run guard is the `if not dry_run:` block at line 230; timing must stay inside the real-run path.

**Status** `[x] done`

---

## Files Changed

| File | Change |
|------|--------|
| `src/wxodemo/cli.py` | `_select()` — intercept `"all"` in targets list |
| `src/wxodemo/deploy.py` | `run_deploy()` — add imports + timing output |
