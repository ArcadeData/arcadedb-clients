import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "scripts"))

from check_codegen_skips import EXPECTED_SKIPS, parse_skips


def test_parses_a_skip_warning() -> None:
    stderr = (
        "WARNING parsing POST /api/v1/ts/{database}/write within time_series. "
        "Endpoint will not be generated.\n\nUnsupported content type text/plain\n"
    )
    assert parse_skips(stderr) == {"POST /api/v1/ts/{database}/write"}


def test_ignores_warnings_that_do_not_skip_the_endpoint() -> None:
    # The ha/snapshot warning drops a RESPONSE, not the endpoint: the operation is
    # still generated, so it must not be counted as a skip.
    stderr = (
        "WARNING parsing GET /api/v1/ha/snapshot/{database} within cluster.\n\n"
        "Cannot parse response for status code 200 (Unsupported content_type "
        "{'application/zip': ...}), response will be omitted from generated client\n"
    )
    assert parse_skips(stderr) == set()


def test_parses_every_expected_skip_together() -> None:
    stderr = "\n".join(
        f"WARNING parsing {op} within x. Endpoint will not be generated.\n\nUnsupported content type y\n"
        for op in EXPECTED_SKIPS
    )
    assert parse_skips(stderr) == set(EXPECTED_SKIPS)


def test_glued_streams_without_a_separator_would_lose_the_skip() -> None:
    # `_SKIP` is `^`-anchored under `re.MULTILINE`. Bare `stdout + stderr`
    # concatenation glues stderr's first line onto stdout's last whenever stdout
    # has no trailing newline, which stops that line from matching `^WARNING
    # parsing ...` - exactly the silent-drop failure mode this script exists to
    # prevent, reproduced inside the script itself. `main()` therefore joins with
    # `"\n".join((result.stdout, result.stderr))`, not `+`; this pins both halves
    # of that fix - that a bare concatenation loses the skip, and the newline join
    # recovers it.
    stdout_no_trailing_newline = "some generator progress output, no trailing newline"
    stderr_starting_with_a_skip = (
        "WARNING parsing POST /api/v1/ts/{database}/write within time_series. "
        "Endpoint will not be generated.\n\nUnsupported content type text/plain\n"
    )

    glued = stdout_no_trailing_newline + stderr_starting_with_a_skip
    assert parse_skips(glued) == set()

    joined = "\n".join((stdout_no_trailing_newline, stderr_starting_with_a_skip))
    assert parse_skips(joined) == {"POST /api/v1/ts/{database}/write"}


def test_the_allowlist_is_exactly_the_four_known_non_json_endpoints() -> None:
    assert (
        frozenset(
            {
                "POST /api/v1/batch/{database}",
                "POST /api/v1/ts/{database}/write",
                "POST /api/v1/ts/{database}/prom/read",
                "POST /api/v1/ts/{database}/prom/write",
            }
        )
        == EXPECTED_SKIPS
    )
