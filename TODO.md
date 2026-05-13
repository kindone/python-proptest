# TODO: python-proptest

Tracks open tasks and feature gaps relative to the C++ reference implementation (`cppproptest2`).

---

## Open

### [ ] onStartup / onCleanup lifecycle hooks
- **What**: Callbacks invoked before/after each property run (including during shrinking).
- **C++ API**: `ForAllConfig{ .onStartup = [](){}, .onCleanup = [](){} }`
- **Python API (proposed)**: `run_for_all(..., on_startup=fn, on_cleanup=fn)`
- **Use case**: Set up / tear down external state (DB connections, temp files, mock resets) around each trial without leaking state between runs.
- **Note**: `on_cleanup` should only fire on success (matching C++ semantics).

### [ ] maxDurationMs — time-box the test loop
- **What**: Stop running new trials after a wall-clock duration, even if `num_runs` hasn't been reached.
- **C++ API**: `ForAllConfig{ .maxDurationMs = 5000 }`
- **Python API (proposed)**: `run_for_all(..., max_duration_ms=5000)`
- **Use case**: CI time budgets; slow generators or properties where you'd rather run fewer trials than time out the build.

### [ ] shrinkMaxRetries — retry-based shrinking for flaky properties
- **What**: Retry each shrink candidate up to N times before accepting or rejecting it. Improves minimal counterexample quality for non-deterministic (flaky) properties.
- **C++ API**: `ForAllConfig{ .shrinkMaxRetries = 5 }`
- **Python API (proposed)**: `run_for_all(..., shrink_max_retries=5)`
- **Use case**: Properties with timing, concurrency, or probabilistic conditions that don't fail 100% of the time.

### [ ] shrinkTimeoutMs / shrinkRetryTimeoutMs — shrink phase time budgets
- **What**: Cap total shrink phase time (`shrink_timeout_ms`) and per-candidate retry time (`shrink_retry_timeout_ms`).
- **C++ API**: `ForAllConfig{ .shrinkTimeoutMs = 2000, .shrinkRetryTimeoutMs = 500 }`
- **Python API (proposed)**: `run_for_all(..., shrink_timeout_ms=2000, shrink_retry_timeout_ms=500)`
- **Use case**: Prevents runaway shrinking on slow properties; pairs with `shrink_max_retries`.

### [ ] outputStream / errorStream — redirect log output
- **What**: Direct informational and failure output to custom streams instead of stdout/stderr.
- **C++ API**: `ForAllConfig{ .outputStream = &my_stream, .errorStream = &my_err_stream }`
- **Python API (proposed)**: `run_for_all(..., output_stream=io_obj, error_stream=io_obj)`
- **Use case**: Capture output in tests; suppress terminal noise; route to loggers.

### [ ] onReproductionStats callback
- **What**: Callback invoked after each shrink-retry assessment with reproduction rate data (`num_reproduced`, `total_runs`, `elapsed_sec`, `args_as_string`).
- **C++ API**: `property(...).setOnReproductionStats(fn)`
- **Python API (proposed)**: `run_for_all(..., on_reproduction_stats=fn)`
- **Use case**: Observability into shrink behaviour for flaky tests; logging, debugging, CI dashboards.

---

## Completed

- **[x] Basic seed + num_runs config** — `run_for_all(..., seed=42, num_runs=100)`
- **[x] Explicit examples** — `@example(...)` decorator
- **[x] Tuple shrinking** — recursive, matches `shrinkTupleUsingVector` in C++
- **[x] Dict shrinking** — `shrink_dict` via pair shrinking in `shrinker/list.py`
- **[x] Finite float generation** — rejection loop with bit interpretation, covers full finite float space including denormals
- **[x] Floating point nan/inf probability config** — `Gen.float(nan_prob, posinf_prob, neginf_prob)`; validated; sum exactly 1.0 supported
- **[x] Floating point shrinker bug fix** — `-inf` shrinks through negative finite values instead of positive `sys.float_info.min`
