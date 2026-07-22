# TODO: python-proptest

Tracks open tasks and feature gaps relative to the C++ reference implementation (`cppproptest2`).

---

## Open

---

## Completed

- **[x] Classification/statistics API** — `tag(key, value)`, `classify(condition, key, value)`, `stat(label, value)` in `python_proptest.core.context`; exported from package root; `Property.assert_stat_ge/le/in_range(key, bound)`; summary printed to `output_stream` on success; context isolated per `for_all()` call
- **[x] no_shrink combinator** — `Gen.no_shrink(gen)` and `gen.no_shrink()`; values retain distribution, shrink stream is empty; tested with int/list/str generators and flat_map U-axis suppression

- **[x] Basic seed + num_runs config** — `run_for_all(..., seed=42, num_runs=100)`
- **[x] Explicit examples** — `@example(...)` decorator
- **[x] Tuple shrinking** — recursive, matches `shrinkTupleUsingVector` in C++
- **[x] Dict shrinking** — `shrink_dict` via pair shrinking in `shrinker/list.py`
- **[x] Finite float generation** — rejection loop with bit interpretation, covers full finite float space including denormals
- **[x] Floating point nan/inf probability config** — `Gen.float(nan_prob, posinf_prob, neginf_prob)`; validated; sum exactly 1.0 supported
- **[x] Floating point shrinker bug fix** — `-inf` shrinks through negative finite values instead of positive `sys.float_info.min`
- **[x] Fluent property configuration** — `Property(...).set_num_runs(...).set_seed(...).set_max_duration_ms(...).set_on_startup(...).set_on_cleanup(...)`
- **[x] onStartup / onCleanup lifecycle hooks** — `run_for_all(..., on_startup=fn, on_cleanup=fn)` and `@settings(...)`; cleanup fires only after successful property evaluations
- **[x] maxDurationMs time-boxing** — `run_for_all(..., max_duration_ms=5000)` and `@settings(max_duration_ms=...)` stop starting new random trials after the budget expires
- **[x] shrinkMaxRetries** — `shrink_max_retries` retries shrink candidates for flaky properties
- **[x] shrinkTimeoutMs / shrinkRetryTimeoutMs** — `shrink_timeout_ms` and `shrink_retry_timeout_ms` cap total shrink time and per-candidate retry time
- **[x] outputStream / errorStream** — `output_stream` and `error_stream` accept `.write(str)` streams for runner output
- **[x] onReproductionStats** — `on_reproduction_stats` receives shrink retry stats with reproduction counts and elapsed time
- **[x] Stateful shrink retry/logging parity** — `StatefulProperty` accepts `shrink_max_retries`, `shrink_timeout_ms`, `shrink_retry_timeout_ms`, `output_stream`, `error_stream`, and `on_reproduction_stats`, plus fluent setters.
