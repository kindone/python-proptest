"""
Per-property-run context for tag collection and stat assertions.

The module-level singleton (_current_ctx) lets property body code call
tag() / classify() / stat() without an explicit context argument, matching
the ergonomics of C++ PROP_TAG / PROP_CLASSIFY / PROP_STAT macros.
"""

from typing import Dict, List, Optional

TagCounts = Dict[str, Dict[str, int]]  # key -> value -> count


class PropertyContext:
    """Accumulates tag/stat data across all runs of a single for_all() call."""

    def __init__(self) -> None:
        self._tags: TagCounts = {}

    # ---- tag accumulation ----

    def tag(self, key: str, value: object) -> None:
        val = str(value)
        if key not in self._tags:
            self._tags[key] = {}
        self._tags[key][val] = self._tags[key].get(val, 0) + 1

    def classify(self, condition: bool, key: str, value: object) -> None:
        if condition:
            self.tag(key, value)

    def stat(self, label: str, value: object) -> None:
        self.tag(label, value)

    def has_tags(self) -> bool:
        return bool(self._tags)

    # ---- stat assertions ----

    def check_stat_assertions(
        self, assertions: List[dict], total_runs: int
    ) -> List[str]:
        """Return a list of failure messages (empty if all assertions pass)."""
        if total_runs == 0:
            return []
        failures: List[str] = []
        for a in assertions:
            key = a["key"]
            counts = self._tags.get(key, {})
            # stat() records bool via str() → "True" / "False" in Python
            count = counts.get("True", 0)
            ratio = count / total_runs
            t = a["type"]
            if t == "GE":
                if ratio < a["bound"]:
                    failures.append(
                        f'assert_stat_ge("{key}", {a["bound"]}) failed: '
                        f"ratio {ratio:.4f} < {a['bound']} ({count}/{total_runs})"
                    )
            elif t == "LE":
                if ratio > a["bound"]:
                    failures.append(
                        f'assert_stat_le("{key}", {a["bound"]}) failed: '
                        f"ratio {ratio:.4f} > {a['bound']} ({count}/{total_runs})"
                    )
            elif t == "IN_RANGE":
                if ratio < a["min"] or ratio > a["max"]:
                    failures.append(
                        f'assert_stat_in_range("{key}", {a["min"]}, {a["max"]}) failed: '
                        f"ratio {ratio:.4f} not in [{a['min']}, {a['max']}] "
                        f"({count}/{total_runs})"
                    )
        return failures

    # ---- summary ----

    def print_summary(self, stream: object) -> None:
        """Write a frequency table of all collected tags to *stream*."""
        for key, value_map in self._tags.items():
            total = sum(value_map.values())
            stream.write(f"  {key}:\n")  # type: ignore[attr-defined]
            for value, count in value_map.items():
                pct = count / total * 100
                stream.write(f"    {value}: {count}/{total} ({pct:.1f}%)\n")  # type: ignore[attr-defined]


# ---- Module-level singleton ----

_current_ctx: Optional[PropertyContext] = None


def _set_context(ctx: Optional[PropertyContext]) -> None:
    """@internal — set by Property.for_all(); do not call directly."""
    global _current_ctx
    _current_ctx = ctx


def _get_context() -> Optional[PropertyContext]:
    """@internal"""
    return _current_ctx


# ---- User-facing functions (callable from inside a property body) ----


def tag(key: str, value: object) -> None:
    """Record a key/value label for the current test run.

    Counts accumulate across all runs and appear in the post-run summary
    when an output_stream is configured on the Property.

    Example::

        from python_proptest import Gen, run_for_all
        from python_proptest.core.context import tag

        run_for_all(
            lambda n: (tag('bucket', 'high' if n > 50 else 'low'), True)[-1],
            Gen.int(0, 100),
        )
    """
    if _current_ctx is not None:
        _current_ctx.tag(key, value)


def classify(condition: bool, key: str, value: object) -> None:
    """Conditionally record a label — records *value* under *key* only when
    *condition* is ``True``.

    Example::

        classify(n < 0, 'sign', 'negative')
    """
    if _current_ctx is not None:
        _current_ctx.classify(condition, key, value)


def stat(label: str, value: object) -> None:
    """Record a boolean/numeric expression result under its label.

    Equivalent to ``tag(label, str(value))``.  Use together with
    ``Property.assert_stat_ge`` / ``assert_stat_le`` / ``assert_stat_in_range``
    to enforce that the ratio of ``True`` outcomes meets a bound.

    Example::

        from python_proptest.core.context import stat
        from python_proptest import Property, Gen

        Property(lambda n: (stat('is_positive', n > 0), True)[-1]) \\
            .assert_stat_ge('is_positive', 0.4) \\
            .run(Gen.int(-100, 100))
    """
    if _current_ctx is not None:
        _current_ctx.stat(label, value)
