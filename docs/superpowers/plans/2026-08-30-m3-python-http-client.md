# M3: Python HTTP Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `arcadedb-client`, a Python HTTP client for ArcadeDB generated from the committed
OpenAPI contract, with both a synchronous and an asynchronous surface, and teach this repository's
shared machinery that it hosts more than one language.

**Architecture:** `openapi-python-client` generates operations and models into a private
`_generated/` package that is committed and drift-gated. A hand-written facade
(`ArcadeDBServer` / `ArcadeDBDatabase`, plus `Async*` twins) wraps it with a throwing error model, a
normalised query envelope, and transaction context managers; the generated client stays reachable as
`.raw` and never throws. CI regenerates and fails on any difference.

**Tech Stack:** Python 3.10+, uv workspace, hatchling, httpx, attrs, `openapi-python-client`, pytest,
respx, pytest-asyncio, testcontainers, ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-08-30-m3-python-http-client-design.md`

## Global Constraints

Every task's requirements implicitly include these.

- **Python floor: 3.10.** `requires-python = ">=3.10"` in every `pyproject.toml`.
- **Distribution name `arcadedb-client`, import name `arcadedb_client`.** `arcadedb-client-grpc` is M3b and is NOT created by this plan.
- **Generated code is never hand-edited.** Everything under `src/arcadedb_client/_generated/` is regenerated output. Fix the contract or the generator invocation instead.
- **Contract version: `26.9.1-SNAPSHOT`**, recorded as `[tool.arcadedb] server-version = "26.9.1-SNAPSHOT"` in the package's `pyproject.toml`.
- **The contract path is never hardcoded.** Always `"$(../scripts/resolve-openapi-contract.sh)"`, which fails if there is not exactly one OpenAPI contract.
- **Runtime dependencies are exactly `httpx`, `attrs`, `typing-extensions`.** No pydantic, no second validation library. Everything else is a dev dependency.
- **ruff and mypy exclude `_generated/`.** mypy runs `--strict` over hand-written source only.
- **All commands run from `python/`** unless stated otherwise.
- **Every task ends with a commit.** Commit messages use Conventional Commits (`feat:`, `test:`, `chore:`, `ci:`, `docs:`).

## Known divergence to preserve

`CommandRequest` in the 26.9.1-SNAPSHOT contract now has a `limit` field, which it did not when
`facade/data.ts` was written — that file's comment says `/command` "has no `limit` field" and defers
adding one until the contract grows it. It has now grown it. **Do not add `limit` to `command()` in
this plan.** Keeping the two clients' public surfaces identical matters more than picking up one
optional field, and adding it to both clients is a separate, additive change. Task 7 records this in
a code comment so the next reader does not "fix" it.

---

### Task 1: `python/` workspace scaffolding

**Files:**
- Create: `python/pyproject.toml`, `python/packages/client/pyproject.toml`, `python/packages/client/README.md`, `python/packages/client/LICENSE`, `python/packages/client/src/arcadedb_client/__init__.py`, `python/packages/client/src/arcadedb_client/py.typed`
- Create: `python/packages/client/tests/test_smoke.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: nothing.
- Produces: an installable `arcadedb_client` package exposing `__version__: str`; the commands `uv run pytest`, `uv run ruff check .`, `uv run mypy` all work from `python/`.

- [ ] **Step 1: Create the workspace root**

`python/pyproject.toml`:

```toml
[project]
name = "arcadedb-drivers-workspace"
version = "0.0.0"
description = "Workspace root for ArcadeDB's Python clients. Not published."
requires-python = ">=3.10"
dependencies = []

[tool.uv]
package = false

[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
arcadedb-client = { workspace = true }

[tool.ruff]
line-length = 120
# Generated output is contract-shaped, not style-shaped. Holding it to a
# hand-written bar produces noise, not safety - the same reason
# typescript/eslint.config.js excludes src/generated/ and src/gen/.
extend-exclude = ["packages/*/src/*/_generated"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]

[tool.mypy]
python_version = "3.10"
strict = true
files = ["packages/client/src/arcadedb_client", "packages/client/tests", "e2e"]
# The generated tree is excluded rather than loosened: it is regenerated on
# every contract bump, so any suppression written into it would be erased.
exclude = "(^|/)_generated/"

[[tool.mypy.overrides]]
module = "arcadedb_client._generated.*"
ignore_errors = true
follow_imports = "skip"

[tool.pytest.ini_options]
# e2e/ is excluded here and has its own invocation, so `pytest` never starts a
# container - the same split typescript/vitest.config.ts makes.
testpaths = ["packages/client/tests"]
asyncio_mode = "strict"
```

- [ ] **Step 2: Create the client package**

`python/packages/client/pyproject.toml`:

```toml
[project]
name = "arcadedb-client"
version = "0.1.0"
description = "Python HTTP client for ArcadeDB, generated from ArcadeDB's OpenAPI contract."
readme = "README.md"
license = "Apache-2.0"
license-files = ["LICENSE"]
requires-python = ">=3.10"
keywords = ["arcadedb", "database", "graph-database", "multi-model", "http-client"]
dependencies = [
    "httpx>=0.27",
    "attrs>=23.2",
    "typing-extensions>=4.10",
]

[project.urls]
Homepage = "https://github.com/ArcadeData/arcadedb-drivers/tree/main/python/packages/client#readme"
Issues = "https://github.com/ArcadeData/arcadedb-drivers/issues"
Repository = "https://github.com/ArcadeData/arcadedb-drivers"

# The ArcadeDB server release this package was generated against. publish-python.yml
# re-verifies this against the committed contract's info.version before publishing,
# and scripts/adopt-contract-version.sh rewrites it on a contract bump.
[tool.arcadedb]
server-version = "26.9.1-SNAPSHOT"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/arcadedb_client"]
```

Copy the repository's `LICENSE` to `python/packages/client/LICENSE`, exactly as
`typescript/packages/client/LICENSE` does.

- [ ] **Step 3: Create the package entry point and marker**

`python/packages/client/src/arcadedb_client/__init__.py`:

```python
"""Python HTTP client for ArcadeDB, generated from ArcadeDB's OpenAPI contract."""

__version__ = "0.1.0"

__all__ = ["__version__"]
```

`python/packages/client/src/arcadedb_client/py.typed` is an empty file.

- [ ] **Step 4: Write the failing smoke test**

`python/packages/client/tests/test_smoke.py`:

```python
import arcadedb_client


def test_package_reports_its_version() -> None:
    assert arcadedb_client.__version__ == "0.1.0"
```

- [ ] **Step 5: Install the toolchain and run the test**

```bash
cd python
uv add --dev openapi-python-client mypy pytest pytest-asyncio respx ruff testcontainers
uv sync
uv run pytest
```

Expected: 1 passed. `uv add` writes real resolved pins into `python/uv.lock`; do not hand-write
version numbers.

- [ ] **Step 6: Ignore the generator's cache directory**

Append to the repository-root `.gitignore`:

```
.ruff_cache/
__pycache__/
.venv/
.mypy_cache/
.pytest_cache/
```

`.ruff_cache/` matters specifically: `openapi-python-client` writes one *inside* its output
directory, and the drift gate's untracked-file half is a `git status --porcelain` over that
directory.

- [ ] **Step 7: Verify lint and typecheck run clean**

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Expected: all three pass.

- [ ] **Step 8: Commit**

```bash
git add python .gitignore
git commit -m "feat(python): scaffold the uv workspace and the arcadedb-client package"
```

---

### Task 2: Generate and commit the client

**Files:**
- Create: `python/packages/client/src/arcadedb_client/_generated/**` (generated)
- Modify: `python/pyproject.toml` (add the `generate` script documentation)
- Create: `python/scripts/generate.sh`

**Interfaces:**
- Consumes: Task 1's workspace.
- Produces: `arcadedb_client._generated.client.Client`, `arcadedb_client._generated.types.Response` / `UNSET` / `Unset`, `arcadedb_client._generated.models.*` (including `QueryRequest`, `CommandRequest`, `QueryResponse`, `QueryRequestParams`, `CommandRequestParams`, `ErrorResponse`, `DatabaseList`, `DatabaseExists`, `ServerInfo`), and `arcadedb_client._generated.api.*` operation modules, each exposing `sync`, `sync_detailed`, `asyncio`, `asyncio_detailed`.

- [ ] **Step 1: Write the generate script**

`python/scripts/generate.sh`:

```bash
#!/usr/bin/env bash
#
# Regenerates the HTTP client from the committed OpenAPI contract.
#
# --meta none emits the package body only (api/, models/, client.py, errors.py,
# types.py) with no project scaffolding of its own. The generated modules import
# each other RELATIVELY, which is what lets the tree nest inside an existing
# package without rewriting a single import.
#
# The contract is located by resolve-openapi-contract.sh rather than by a glob:
# two contracts/arcadedb-openapi-*.json would otherwise generate from whichever
# the glob yields first, which is lexical, not version, order.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PYTHON_DIR/.." && pwd)"

SPEC="$("$REPO_ROOT/scripts/resolve-openapi-contract.sh")"
OUT="$PYTHON_DIR/packages/client/src/arcadedb_client/_generated"

cd "$PYTHON_DIR"
uv run openapi-python-client generate \
  --path "$SPEC" \
  --meta none \
  --overwrite \
  --output-path "$OUT"

# The generator leaves its own ruff cache inside the output directory, which the
# drift gate reads with `git status --porcelain`.
rm -rf "$OUT/.ruff_cache"
```

```bash
chmod +x python/scripts/generate.sh
```

- [ ] **Step 2: Generate**

```bash
./scripts/generate.sh
```

Expected: it prints four `WARNING parsing ...` blocks for `POST /api/v1/batch/{database}`,
`POST /api/v1/ts/{database}/write`, `POST /api/v1/ts/{database}/prom/read` and
`POST /api/v1/ts/{database}/prom/write`, plus one about `GET /api/v1/ha/snapshot/{database}`'s zip
response, and **exits 0**. That is expected; Task 3 turns it into a checked invariant.

- [ ] **Step 3: Verify the generated tree is importable and deterministic**

```bash
uv run python -c "from arcadedb_client._generated.client import Client; print(Client)"
./scripts/generate.sh
git status --porcelain -- packages/client/src/arcadedb_client/_generated
```

Expected: the import prints the class; the second generate leaves `git status` reporting only the
files added by the first run (no modifications from re-running).

- [ ] **Step 4: Confirm 60 operation modules were generated**

```bash
find packages/client/src/arcadedb_client/_generated/api -name '*.py' ! -name '__init__.py' | wc -l
```

Expected: `60`. If this is not 60, stop — the contract or the generator version has changed and Task
3's allowlist will be wrong.

- [ ] **Step 5: Commit**

```bash
git add python
git commit -m "feat(python): generate the HTTP client from the 26.9.1-SNAPSHOT contract"
```

---

### Task 3: The codegen skip allowlist guard

**Files:**
- Create: `python/scripts/check_codegen_skips.py`
- Create: `python/packages/client/tests/test_check_codegen_skips.py`

**Interfaces:**
- Consumes: Task 2's generator invocation.
- Produces: `check_codegen_skips.parse_skips(stderr: str) -> set[str]` and `EXPECTED_SKIPS: frozenset[str]`; the script exits 0 when the skip set matches and 1 otherwise.

**Why this exists:** `openapi-python-client` skips endpoints whose media type it cannot model,
warns on stderr, and exits 0. A future contract adding a `text/csv` endpoint would have it silently
dropped with a green build — a failure indistinguishable from success.

- [ ] **Step 1: Write the failing test**

`python/packages/client/tests/test_check_codegen_skips.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "scripts"))

from check_codegen_skips import EXPECTED_SKIPS, parse_skips  # noqa: E402


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


def test_the_allowlist_is_exactly_the_four_known_non_json_endpoints() -> None:
    assert EXPECTED_SKIPS == frozenset(
        {
            "POST /api/v1/batch/{database}",
            "POST /api/v1/ts/{database}/write",
            "POST /api/v1/ts/{database}/prom/read",
            "POST /api/v1/ts/{database}/prom/write",
        }
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest packages/client/tests/test_check_codegen_skips.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'check_codegen_skips'`.

- [ ] **Step 3: Write the script**

`python/scripts/check_codegen_skips.py`:

```python
#!/usr/bin/env python3
"""Fails when the set of endpoints openapi-python-client silently skips changes.

The generator cannot model a non-JSON request body. When it meets one it prints a
warning to stderr, omits the endpoint, and EXITS 0. Nothing else in the build
notices: `git diff` over the generated tree is clean, because the endpoint was
never there to remove.

So the skip set is pinned. Adding an endpoint to EXPECTED_SKIPS is a deliberate
decision to leave it unwrapped or hand-written - never a way to quiet this check.

Run from `python/`:  uv run python scripts/check_codegen_skips.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Endpoints the generator cannot model, and what this repository does about each:
#   POST /api/v1/ts/{database}/write       text/plain      hand-written in facade/timeseries.py
#   POST /api/v1/batch/{database}          jsonl/ndjson/csv  unwrapped, as in @arcadedb/client
#   POST /api/v1/ts/{database}/prom/read   x-protobuf      unwrapped, as in @arcadedb/client
#   POST /api/v1/ts/{database}/prom/write  x-protobuf      unwrapped, as in @arcadedb/client
EXPECTED_SKIPS = frozenset(
    {
        "POST /api/v1/batch/{database}",
        "POST /api/v1/ts/{database}/write",
        "POST /api/v1/ts/{database}/prom/read",
        "POST /api/v1/ts/{database}/prom/write",
    }
)

# Only the "Endpoint will not be generated" form counts. The ha/snapshot warning
# has the same "WARNING parsing" prefix but drops a single RESPONSE while still
# generating the operation, so a looser pattern would report a skip that is not one.
_SKIP = re.compile(
    r"^WARNING parsing (?P<op>[A-Z]+ /\S+) within \S+?\.\s+Endpoint will not be generated\.",
    re.MULTILINE,
)


def parse_skips(stderr: str) -> set[str]:
    """Extracts the operations the generator declined to generate."""
    return {match.group("op") for match in _SKIP.finditer(stderr)}


def main() -> int:
    python_dir = Path(__file__).resolve().parents[1]
    repo_root = python_dir.parent
    spec = subprocess.run(
        [str(repo_root / "scripts" / "resolve-openapi-contract.sh")],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    result = subprocess.run(
        [
            "uv",
            "run",
            "openapi-python-client",
            "generate",
            "--path",
            spec,
            "--meta",
            "none",
            "--overwrite",
            "--output-path",
            str(python_dir / "packages/client/src/arcadedb_client/_generated"),
        ],
        cwd=python_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        return result.returncode

    # The generator writes warnings to stdout in some versions and stderr in others;
    # reading both is cheaper than depending on which.
    found = parse_skips(result.stdout + result.stderr)
    if found == set(EXPECTED_SKIPS):
        print(f"OK: the generator skipped exactly the {len(found)} allowlisted operations.")
        return 0

    for op in sorted(found - set(EXPECTED_SKIPS)):
        sys.stderr.write(
            f"ERROR: {op} is NOT generated and is not on the allowlist. The contract added an\n"
            f"       endpoint this generator cannot model. Either hand-write it in the facade or\n"
            f"       add it to EXPECTED_SKIPS with a comment saying why it is unwrapped.\n"
        )
    for op in sorted(set(EXPECTED_SKIPS) - found):
        sys.stderr.write(
            f"ERROR: {op} is on the allowlist but IS now generated. The contract changed its media\n"
            f"       type; remove it from EXPECTED_SKIPS and use the generated operation.\n"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest packages/client/tests/test_check_codegen_skips.py -v`
Expected: 4 passed.

- [ ] **Step 5: Run the script against the real contract**

Run: `uv run python scripts/check_codegen_skips.py`
Expected: `OK: the generator skipped exactly the 4 allowlisted operations.` and exit 0.

- [ ] **Step 6: Verify it actually fails when the allowlist is wrong**

Temporarily remove `"POST /api/v1/batch/{database}"` from `EXPECTED_SKIPS`, rerun the script,
confirm it exits 1 with the "is NOT generated and is not on the allowlist" message, then restore it.
A guard nobody has seen fail is a guard nobody knows works.

- [ ] **Step 7: Commit**

```bash
git add python
git commit -m "feat(python): guard the generator's silent endpoint skips with an allowlist"
```

---

### Task 4: `ci-python.yml` and the drift gate

**Files:**
- Create: `.github/workflows/ci-python.yml`

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: a `build` job that must stay green for every later task.

- [ ] **Step 1: Write the workflow**

`.github/workflows/ci-python.yml`:

```yaml
name: Python client CI

on:
  push:
    branches:
      - main
    paths:
      - "python/**"
      - "contracts/**"
      - "scripts/**"
      # The drift gate's untracked-file half is a `git status --porcelain` over the
      # generated directory, which an ignore rule covering it would silence
      # permanently and invisibly. ci.yml lists .gitignore for the same reason.
      - ".gitignore"
      - ".github/workflows/ci-python.yml"
  pull_request:
    paths:
      - "python/**"
      - "contracts/**"
      - "scripts/**"
      - ".gitignore"
      - ".github/workflows/ci-python.yml"

jobs:
  build:
    name: Lint, typecheck and drift gate
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
          cache-dependency-glob: python/uv.lock

      - name: Set up Python
        working-directory: python
        # 3.10 is the declared floor. The e2e job below runs 3.14, so the two jobs
        # together cover floor and current without a matrix.
        run: uv python install 3.10

      - name: Install dependencies
        working-directory: python
        run: uv sync --frozen --python 3.10

      - name: Lint
        working-directory: python
        run: |
          uv run ruff check .
          uv run ruff format --check .

      - name: Typecheck
        working-directory: python
        run: uv run mypy

      - name: Regenerate and verify no drift
        working-directory: python
        run: |
          ./scripts/generate.sh

          # Catches a MODIFIED generated file (existing path, changed content).
          git diff --exit-code -- packages/client/src/arcadedb_client/_generated

          # Catches an ADDED or RENAMED generated file: `git diff` above is blind to
          # untracked paths, so a contract that introduces a new model or operation
          # module would leave the diff check green while the new file went uncommitted.
          if [[ -n "$(git status --porcelain -- packages/client/src/arcadedb_client/_generated)" ]]; then
            echo "Generated output changed (untracked and/or modified files below) - commit the regenerated output:" >&2
            git status --porcelain -- packages/client/src/arcadedb_client/_generated >&2
            exit 1
          fi

      - name: Verify the generator skipped exactly the allowlisted endpoints
        working-directory: python
        # The third half of the drift gate, and the one with no TypeScript
        # counterpart: openapi-python-client drops an endpoint it cannot model,
        # warns, and exits 0. Neither check above can see an endpoint that was
        # never generated in the first place.
        run: uv run python scripts/check_codegen_skips.py

      - name: Test
        working-directory: python
        run: uv run pytest
```

- [ ] **Step 2: Verify each gate locally**

```bash
cd python
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
./scripts/generate.sh && git diff --exit-code -- packages/client/src/arcadedb_client/_generated
uv run python scripts/check_codegen_skips.py
```

Expected: every command exits 0.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci-python.yml
git commit -m "ci: add the Python client workflow with a three-part drift gate"
```

---

### Task 5: `ArcadeDBError` and `unwrap`

**Files:**
- Create: `python/packages/client/src/arcadedb_client/errors.py`
- Create: `python/packages/client/src/arcadedb_client/_internal/__init__.py`
- Create: `python/packages/client/src/arcadedb_client/_internal/unwrap.py`
- Create: `python/packages/client/tests/test_errors.py`

**Interfaces:**
- Consumes: `arcadedb_client._generated.types.Response`, `arcadedb_client._generated.models.error_response.ErrorResponse`.
- Produces:
  - `ArcadeDBError(Exception)` with `status: int`, `error: str | None`, `exception: str | None`, `detail: str | None`, `request_id: str | None`, `help_: str | None`, `exception_args: str | None`; constructor `ArcadeDBError(status: int, body: object = None, request_id: str | None = None)`; classmethod `ArcadeDBError.from_response(response: Response[Any]) -> ArcadeDBError`.
  - `unwrap(response: Response[T]) -> T`.

- [ ] **Step 1: Write the failing tests**

`python/packages/client/tests/test_errors.py`:

```python
from http import HTTPStatus
from typing import Any

import pytest

from arcadedb_client._generated.types import Response
from arcadedb_client.errors import ArcadeDBError
from arcadedb_client._internal.unwrap import unwrap


def make_response(status: int, content: bytes = b"", headers: dict[str, str] | None = None) -> Response[Any]:
    return Response(
        status_code=HTTPStatus(status),
        content=content,
        headers=headers or {},
        parsed=None,
    )


def test_carries_every_field_the_body_supplied() -> None:
    err = ArcadeDBError(
        400,
        {
            "error": "Encountered an error",
            "exception": "com.arcadedb.SomeException",
            "detail": "line 1",
            "requestId": "abc-123",
            "help": "check the syntax",
            "exceptionArgs": "arg",
        },
    )
    assert err.status == 400
    assert err.error == "Encountered an error"
    assert err.exception == "com.arcadedb.SomeException"
    assert err.detail == "line 1"
    assert err.request_id == "abc-123"
    assert err.help_ == "check the syntax"
    assert err.exception_args == "arg"
    assert str(err) == "Encountered an error"


def test_falls_back_through_detail_then_status_for_the_message() -> None:
    assert str(ArcadeDBError(500, {"detail": "boom"})) == "boom"
    assert str(ArcadeDBError(503)) == "ArcadeDB request failed with status 503"


@pytest.mark.parametrize("body", [None, "not an object", 42, [1, 2, 3], b"\xff\xfe"])
def test_parsing_never_raises_on_a_body_that_is_not_an_object(body: object) -> None:
    # This runs on the failure path. An error class that can itself fail turns a
    # server error into a confusing client-side crash.
    err = ArcadeDBError(500, body)
    assert err.status == 500
    assert err.error is None


def test_reads_the_request_id_from_the_header_when_the_body_has_none() -> None:
    response = make_response(404, b'{"error":"not found"}', {"X-Request-Id": "hdr-9"})
    err = ArcadeDBError.from_response(response)
    assert err.error == "not found"
    assert err.request_id == "hdr-9"


def test_survives_an_unparsable_error_body() -> None:
    response = make_response(500, b"<html>gateway timeout</html>")
    err = ArcadeDBError.from_response(response)
    assert err.status == 500
    assert err.error is None


def test_unwrap_returns_parsed_on_success() -> None:
    response = Response(status_code=HTTPStatus(200), content=b"{}", headers={}, parsed={"ok": True})
    assert unwrap(response) == {"ok": True}


def test_unwrap_raises_on_a_non_2xx() -> None:
    response = make_response(409, b'{"error":"conflict"}')
    with pytest.raises(ArcadeDBError) as caught:
        unwrap(response)
    assert caught.value.status == 409
    assert caught.value.error == "conflict"


def test_unwrap_accepts_a_204_with_no_body() -> None:
    assert unwrap(make_response(204)) is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest packages/client/tests/test_errors.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'arcadedb_client.errors'`.

- [ ] **Step 3: Write `errors.py`**

```python
"""The facade's error type.

`ArcadeDBServer.raw` - the generated client - never raises this, or anything
else: it returns a `Response` whose `status_code` the caller inspects. That
asymmetry is deliberate and mirrors `@arcadedb/client`, where `raw` returns
`{ data, error }` while every facade method throws.
"""

from __future__ import annotations

import json
from typing import Any

from ._generated.models.error_response import ErrorResponse
from ._generated.types import Response

#: The server sets this on every response, generating a value when the client sent
#: none, so it is a usable correlation id unconditionally - not only when the caller
#: supplied its own.
REQUEST_ID_HEADER = "X-Request-Id"


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _parse_body(body: object) -> dict[str, Any]:
    """Reduces whatever the server sent to a dict, never raising.

    The server guarantees none of these fields, and the body may be absent, empty,
    or not JSON at all. A body that is not a JSON object yields an empty dict, so
    the resulting error carries nothing beyond its HTTP status.
    """
    if isinstance(body, bytes):
        try:
            body = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            return {}
    if isinstance(body, ErrorResponse):
        body = body.to_dict()
    return body if isinstance(body, dict) else {}


class ArcadeDBError(Exception):
    """Raised by every facade method when the server answers with a non-2xx status.

    Carries the HTTP status plus whatever the server's JSON error body contributed.
    Every field beyond `status` is optional, because the body may be absent,
    unparsable, or missing individual fields.
    """

    def __init__(self, status: int, body: object = None, request_id: str | None = None) -> None:
        parsed = _parse_body(body)
        self.status = int(status)
        self.error = _str_or_none(parsed.get("error"))
        self.exception = _str_or_none(parsed.get("exception"))
        self.detail = _str_or_none(parsed.get("detail"))
        self.request_id = request_id or _str_or_none(parsed.get("requestId"))
        # Spelled `help_` to match the generated ErrorResponse model, which is
        # reachable through `.raw`. One awkward name beats two spellings of one
        # field inside a package that exposes both.
        self.help_ = _str_or_none(parsed.get("help"))
        # Despite the plural name the contract types this as a plain string, not an
        # array. Passed through as-is rather than parsed or coerced.
        self.exception_args = _str_or_none(parsed.get("exceptionArgs"))
        super().__init__(self.error or self.detail or f"ArcadeDB request failed with status {self.status}")

    @classmethod
    def from_response(cls, response: Response[Any]) -> ArcadeDBError:
        """Builds an error from a generated `Response`.

        Prefers the already-parsed `ErrorResponse` when the contract documented one
        for this status, and falls back to re-reading the raw bytes when it did not.
        """
        body: object = response.parsed if isinstance(response.parsed, ErrorResponse) else response.content
        return cls(int(response.status_code), body, response.headers.get(REQUEST_ID_HEADER))
```

- [ ] **Step 4: Write `_internal/unwrap.py`**

`python/packages/client/src/arcadedb_client/_internal/__init__.py` is empty.

`python/packages/client/src/arcadedb_client/_internal/unwrap.py`:

```python
"""The single bridge from the generated client's non-throwing `Response` to the throwing facade.

One function serves BOTH facades: `sync_detailed` and `asyncio_detailed` return the
same `Response[T]`, so nothing here is transport-specific.

It lives in `_internal/` rather than being re-exported from `__init__.py` to break
an import cycle: `__init__.py` builds the server and database classes out of the
`facade/` functions, and `facade/` needs `unwrap` too.
"""

from __future__ import annotations

from typing import Any, TypeVar, cast

from .._generated.types import Response
from ..errors import ArcadeDBError

T = TypeVar("T")


def is_success(response: Response[Any]) -> bool:
    """True when the status is 2xx."""
    return 200 <= int(response.status_code) < 300


def unwrap(response: Response[T]) -> T:
    """Returns `parsed` on success; raises `ArcadeDBError` on any non-2xx response.

    `parsed` is `None` for the 204 endpoints (begin/commit/rollback, ts.write), and
    that `None` is returned rather than treated as a failure.
    """
    if not is_success(response):
        raise ArcadeDBError.from_response(response)
    return cast("T", response.parsed)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest packages/client/tests/test_errors.py -v`
Expected: 12 passed.

- [ ] **Step 6: Lint and typecheck**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add python
git commit -m "feat(python): add ArcadeDBError and the unwrap bridge"
```

---

### Task 6: Authentication helpers

**Files:**
- Create: `python/packages/client/src/arcadedb_client/auth.py`
- Create: `python/packages/client/tests/test_auth.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `basic_auth(user: str, password: str) -> dict[str, str]` and `bearer_auth(token: str) -> dict[str, str]`.

- [ ] **Step 1: Write the failing tests**

`python/packages/client/tests/test_auth.py`:

```python
import base64

from arcadedb_client.auth import basic_auth, bearer_auth


def test_basic_auth_encodes_user_and_password_as_rfc_7617() -> None:
    headers = basic_auth("root", "playwithdata")
    assert headers == {"Authorization": "Basic cm9vdDpwbGF5d2l0aGRhdGE="}


def test_basic_auth_encodes_non_ascii_credentials_as_utf8() -> None:
    # The TypeScript client needs 60 lines of TextEncoder plumbing for this case
    # because btoa throws above U+00FF. Python's b64encode takes bytes, so the
    # hazard does not exist here - this test pins that it stays correct anyway.
    headers = basic_auth("josé", "münchen")
    decoded = base64.b64decode(headers["Authorization"].removeprefix("Basic ")).decode("utf-8")
    assert decoded == "josé:münchen"


def test_basic_auth_handles_a_very_long_credential() -> None:
    # The TypeScript version blew the call stack here via String.fromCharCode(...bytes).
    headers = basic_auth("u", "x" * 200_000)
    assert headers["Authorization"].startswith("Basic ")


def test_bearer_auth_sets_the_authorization_header() -> None:
    assert bearer_auth("AU-abc123") == {"Authorization": "Bearer AU-abc123"}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest packages/client/tests/test_auth.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'arcadedb_client.auth'`.

- [ ] **Step 3: Write `auth.py`**

```python
"""Authentication headers for `ArcadeDBServer` and `AsyncArcadeDBServer`.

Both return a plain header mapping, passed to the server constructor's `auth`
argument. The generated `AuthenticatedClient` is deliberately not used: its
token-and-prefix model fits bearer but not basic, and one uniform mechanism for
both is simpler than two.

`@arcadedb/client`'s `auth.ts` spends sixty lines on `TextEncoder`, chunking, and
commentary because `btoa` mangles credentials above U+00FF and a spread call blows
the stack on a large one. `base64.b64encode` takes bytes and has neither hazard.
Do not port that workaround; there is no problem here for it to solve.
"""

from __future__ import annotations

import base64


def basic_auth(user: str, password: str) -> dict[str, str]:
    """HTTP Basic auth, per RFC 7617: `user:password` as UTF-8, then base64."""
    credential = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
    return {"Authorization": f"Basic {credential}"}


def bearer_auth(token: str) -> dict[str, str]:
    """Bearer token auth, for session tokens from `/api/v1/login` (prefixed `AU-`) or any other bearer credential."""
    return {"Authorization": f"Bearer {token}"}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest packages/client/tests/test_auth.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add python
git commit -m "feat(python): add basic_auth and bearer_auth"
```

---

### Task 7: The synchronous data plane

**Files:**
- Create: `python/packages/client/src/arcadedb_client/facade/__init__.py`
- Create: `python/packages/client/src/arcadedb_client/facade/data.py`
- Modify: `python/packages/client/src/arcadedb_client/__init__.py`
- Create: `python/packages/client/tests/test_data.py`
- Create: `python/packages/client/tests/test_server.py`

**Interfaces:**
- Consumes: `unwrap`, `is_success`, `ArcadeDBError`, the generated operation modules.
- Produces:
  - `QueryLanguage = Literal["sql", "cypher", "gremlin", "graphql", "mongo"]`
  - `QueryEnvelope` — frozen dataclass with `result: list[dict[str, Any]]`, `limit: int`, `returned: int`, `truncated: bool`
  - `to_envelope(data: QueryResponse) -> QueryEnvelope`
  - `build_query_request(language, command, params, limit) -> QueryRequest` and `build_command_request(language, command, params) -> CommandRequest`
  - `ArcadeDBServer(base_url: str, auth: Mapping[str, str] | None = None, headers: Mapping[str, str] | None = None, timeout: httpx.Timeout | None = None, verify_ssl: bool = True)` with `.raw`, `.list_databases()`, `.exists(name)`, `.server_info()`, `.health()`, `.ready()`, `.db(name)`, `.close()`, `__enter__` / `__exit__`
  - `ArcadeDBDatabase` with `.name`, `.query(...)`, `.command(...)`

- [ ] **Step 1: Write the failing tests**

`python/packages/client/tests/test_data.py`:

```python
from typing import Any

import httpx
import pytest
import respx

from arcadedb_client import ArcadeDBError, ArcadeDBServer, basic_auth

BASE_URL = "http://db.test"


def server() -> ArcadeDBServer:
    return ArcadeDBServer(base_url=BASE_URL, auth=basic_auth("root", "playwithdata"))


@respx.mock
def test_query_returns_the_whole_envelope() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/query/mydb").mock(
        return_value=httpx.Response(
            200,
            json={"result": [{"name": "Ada"}], "limit": 100, "returned": 1, "truncated": False},
        )
    )
    with server() as srv:
        env = srv.db("mydb").query(language="sql", command="SELECT FROM Person")

    assert env.result == [{"name": "Ada"}]
    assert env.limit == 100
    assert env.returned == 1
    assert env.truncated is False
    assert route.calls.last.request.headers["Authorization"].startswith("Basic ")


@respx.mock
def test_query_defaults_every_omitted_envelope_field() -> None:
    # QueryResponse has no `required` list in the contract, so all four fields are
    # technically optional. The defaults assert a completeness the server never
    # claimed - which is the most reassuring reading of "the server did not say",
    # and identical to what @arcadedb/client's toEnvelope does.
    respx.post(f"{BASE_URL}/api/v1/query/mydb").mock(return_value=httpx.Response(200, json={}))
    with server() as srv:
        env = srv.db("mydb").query(language="sql", command="SELECT 1")

    assert env.result == []
    assert env.limit == -1
    assert env.returned == 0
    assert env.truncated is False


@respx.mock
def test_query_sends_params_and_limit_only_when_supplied() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/query/mydb").mock(
        return_value=httpx.Response(200, json={"result": []})
    )
    with server() as srv:
        srv.db("mydb").query(
            language="sql", command="SELECT FROM P WHERE age > :min", params={"min": 18}, limit=5
        )
        srv.db("mydb").query(language="sql", command="SELECT 1")

    with_opts: dict[str, Any] = route.calls[0].request.read() and __import__("json").loads(
        route.calls[0].request.read()
    )
    without: dict[str, Any] = __import__("json").loads(route.calls[1].request.read())
    assert with_opts["params"] == {"min": 18}
    assert with_opts["limit"] == 5
    assert "params" not in without
    assert "limit" not in without


@respx.mock
def test_command_sends_language_as_a_required_field() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/command/mydb").mock(
        return_value=httpx.Response(200, json={"result": [], "returned": 0})
    )
    with server() as srv:
        srv.db("mydb").command(language="sql", command="INSERT INTO Person SET name = 'Ada'")

    body = __import__("json").loads(route.calls.last.request.read())
    assert body["language"] == "sql"
    assert body["command"] == "INSERT INTO Person SET name = 'Ada'"


@respx.mock
def test_a_non_2xx_raises_arcadedb_error_with_the_servers_detail() -> None:
    respx.post(f"{BASE_URL}/api/v1/query/mydb").mock(
        return_value=httpx.Response(
            400,
            json={"error": "Invalid query", "detail": "line 1:8"},
            headers={"X-Request-Id": "req-77"},
        )
    )
    with server() as srv, pytest.raises(ArcadeDBError) as caught:
        srv.db("mydb").query(language="sql", command="SELCT 1")

    assert caught.value.status == 400
    assert caught.value.error == "Invalid query"
    assert caught.value.detail == "line 1:8"
    assert caught.value.request_id == "req-77"


@respx.mock
def test_raw_does_not_raise() -> None:
    # The deliberate asymmetry: the facade throws, `.raw` never does.
    from arcadedb_client._generated.api.database import list_databases

    respx.get(f"{BASE_URL}/api/v1/databases").mock(return_value=httpx.Response(500, json={"error": "boom"}))
    with server() as srv:
        response = list_databases.sync_detailed(client=srv.raw)

    assert response.status_code == 500
```

`python/packages/client/tests/test_server.py`:

```python
import httpx
import pytest
import respx

from arcadedb_client import ArcadeDBError, ArcadeDBServer

BASE_URL = "http://db.test"


@respx.mock
def test_list_databases_returns_names() -> None:
    respx.get(f"{BASE_URL}/api/v1/databases").mock(
        return_value=httpx.Response(200, json={"result": ["one", "two"]})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        assert srv.list_databases() == ["one", "two"]


@respx.mock
def test_list_databases_defaults_an_omitted_result_to_empty() -> None:
    respx.get(f"{BASE_URL}/api/v1/databases").mock(return_value=httpx.Response(200, json={}))
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        assert srv.list_databases() == []


@respx.mock
def test_exists_returns_the_servers_answer() -> None:
    respx.get(f"{BASE_URL}/api/v1/exists/mydb").mock(
        return_value=httpx.Response(200, json={"result": True})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        assert srv.exists("mydb") is True


@respx.mock
def test_ready_returns_false_on_503_and_raises_on_anything_else() -> None:
    respx.get(f"{BASE_URL}/api/v1/ready").mock(return_value=httpx.Response(503))
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        assert srv.ready() is False

    respx.get(f"{BASE_URL}/api/v1/ready").mock(return_value=httpx.Response(204))
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        assert srv.ready() is True

    respx.get(f"{BASE_URL}/api/v1/ready").mock(return_value=httpx.Response(500, json={"error": "x"}))
    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(ArcadeDBError):
        srv.ready()


@respx.mock
def test_health_raises_when_the_server_does_not_answer_204() -> None:
    respx.get(f"{BASE_URL}/api/v1/health").mock(return_value=httpx.Response(500, json={"error": "down"}))
    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(ArcadeDBError):
        srv.health()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest packages/client/tests/test_data.py packages/client/tests/test_server.py -v`
Expected: FAIL with `ImportError: cannot import name 'ArcadeDBServer' from 'arcadedb_client'`.

- [ ] **Step 3: Write `facade/data.py`**

`python/packages/client/src/arcadedb_client/facade/__init__.py` is empty.

```python
"""The data plane: `query`, `command`, and the transaction primitives.

Everything here takes the generated `Client` explicitly rather than reaching for a
module-level one, so the sync and async facades can share the request-building and
envelope-normalising code without either importing the other.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypeVar

from .._generated.models.command_request import CommandRequest
from .._generated.models.command_request_params import CommandRequestParams
from .._generated.models.query_request import QueryRequest
from .._generated.models.query_request_params import QueryRequestParams
from .._generated.models.query_response import QueryResponse
from .._generated.types import UNSET, Unset

#: Request header carrying the session id that scopes a call to one transaction.
SESSION_HEADER = "arcadedb-session-id"

#: Query/command language, as accepted by the `/query` and `/command` endpoints.
QueryLanguage = Literal["sql", "cypher", "gremlin", "graphql", "mongo"]

T = TypeVar("T")


def _or(value: T | Unset, fallback: T) -> T:
    return fallback if isinstance(value, Unset) else value


@dataclass(frozen=True, slots=True)
class QueryEnvelope:
    """The whole result envelope `query`/`command` return - not just the rows.

    `truncated` means the serializer's row cap stopped mid-serialization with rows
    still pending, so `result` is incomplete: a caller that reads `result` and
    ignores `truncated` can silently work off a partial answer.

    `QueryResponse` has no `required` list in the contract, so every field the
    server sends is technically optional. When one is omitted this client defaults
    it (`limit` to `-1`, meaning uncapped; `returned` to `0`; `truncated` to
    `False`). Those defaults are the most reassuring possible reading of "the server
    did not say" - they assert a completeness the server itself never claimed. In
    practice today's server always sends all four, but that is a property of the
    current implementation, not a guarantee this type enforces.
    """

    result: list[dict[str, Any]]
    limit: int
    returned: int
    truncated: bool


def to_envelope(data: QueryResponse) -> QueryEnvelope:
    """Normalises a generated `QueryResponse` into the public envelope.

    Also flattens each row out of `QueryResponseResultItem`'s additional-properties
    wrapper into the plain dict a caller expects.
    """
    rows = _or(data.result, [])
    return QueryEnvelope(
        result=[row.to_dict() for row in rows],
        limit=_or(data.limit, -1),
        returned=_or(data.returned, 0),
        truncated=_or(data.truncated, False),
    )


def build_query_request(
    *,
    language: QueryLanguage,
    command: str,
    params: dict[str, Any] | None,
    limit: int | None,
) -> QueryRequest:
    """Builds the body for `POST /api/v1/query/{database}`.

    `params` is converted with `from_dict` because the generated params type is an
    "untyped object" artifact rather than a real restriction. `command` and
    `language` are passed through with their real types, so a contract change to
    either still fails the typecheck here rather than only on the wire.
    """
    return QueryRequest(
        command=command,
        language=language,
        params=UNSET if params is None else QueryRequestParams.from_dict(params),
        limit=UNSET if limit is None else limit,
    )


def build_command_request(
    *,
    language: QueryLanguage,
    command: str,
    params: dict[str, Any] | None,
) -> CommandRequest:
    """Builds the body for `POST /api/v1/command/{database}`.

    `language` is a required field here, unlike on `/query`, matching the server's
    `PostCommandHandler`, which rejects a request without it.

    NOTE: `CommandRequest` also carries an optional `limit` in the current contract.
    It is deliberately NOT exposed on `command()`. `@arcadedb/client` does not
    expose it either, and keeping the two clients' public surfaces identical matters
    more than one optional field. Adding it is additive and belongs in a change that
    does it for both clients at once.
    """
    return CommandRequest(
        command=command,
        language=language,
        params=UNSET if params is None else CommandRequestParams.from_dict(params),
    )


def session_kwarg(session_id: str | None) -> str | Unset:
    """The `arcadedb_session_id` argument value: the id inside a transaction, `UNSET` outside one.

    The contract declares the header, so the generator emits it as a keyword
    argument on every data-plane and transaction operation - no header plumbing
    needed.
    """
    return UNSET if session_id is None else session_id
```

- [ ] **Step 4: Write the synchronous facade in `__init__.py`**

Replace `python/packages/client/src/arcadedb_client/__init__.py`:

```python
"""Python HTTP client for ArcadeDB, generated from ArcadeDB's OpenAPI contract."""

from __future__ import annotations

from collections.abc import Mapping
from types import TracebackType
from typing import Any

import httpx

from ._generated.api.database import check_database_exists, list_databases
from ._generated.api.command import execute_command
from ._generated.api.health import check_health, check_ready
from ._generated.api.query import execute_query_post
from ._generated.api.server import get_server_info
from ._generated.client import Client
from ._generated.models.query_response import QueryResponse
from ._generated.models.server_info import ServerInfo
from ._generated.types import Unset
from ._internal.unwrap import is_success, unwrap
from .auth import basic_auth, bearer_auth
from .errors import ArcadeDBError
from .facade.data import (
    QueryEnvelope,
    QueryLanguage,
    build_command_request,
    build_query_request,
    session_kwarg,
    to_envelope,
)

__version__ = "0.1.0"

__all__ = [
    "ArcadeDBDatabase",
    "ArcadeDBError",
    "ArcadeDBServer",
    "QueryEnvelope",
    "QueryLanguage",
    "__version__",
    "basic_auth",
    "bearer_auth",
]


class ArcadeDBDatabase:
    """A single database reached through an `ArcadeDBServer`. Constructed by `ArcadeDBServer.db()`.

    When held as a transaction handle, `session_id` is set and every `query` /
    `command` call made through THIS instance carries it, which is what keeps those
    calls inside the transaction rather than auto-committing individually. Calls
    made through the outer database object do not take part in the transaction.
    """

    def __init__(self, client: Client, name: str, session_id: str | None = None) -> None:
        self._client = client
        self.name = name
        self._session_id = session_id

    def query(
        self,
        *,
        language: QueryLanguage,
        command: str,
        params: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> QueryEnvelope:
        """Executes a read-or-write query and returns the whole result envelope - not just `result`.

        `limit` caps the rows serialized into the response. Omitted, a `LIMIT` stated
        by the query is honoured as written and only a query stating none is capped
        by the server default. `-1` means no cap. No value here widens a response
        past the server's hard ceiling: a result exceeding it is refused with 413
        rather than truncated, so raising `limit` is not always the fix for a
        `truncated` response.
        """
        response = execute_query_post.sync_detailed(
            self.name,
            client=self._client,
            body=build_query_request(language=language, command=command, params=params, limit=limit),
            arcadedb_session_id=session_kwarg(self._session_id),
        )
        data = unwrap(response)
        # `unwrap` has already raised on any non-2xx, so the generated union's
        # ErrorResponse member cannot reach here; this narrows it for the typechecker.
        assert isinstance(data, QueryResponse)
        return to_envelope(data)

    def command(
        self,
        *,
        language: QueryLanguage,
        command: str,
        params: dict[str, Any] | None = None,
    ) -> QueryEnvelope:
        """Executes a command and returns the whole result envelope - not just `result`."""
        response = execute_command.sync_detailed(
            self.name,
            client=self._client,
            body=build_command_request(language=language, command=command, params=params),
            arcadedb_session_id=session_kwarg(self._session_id),
        )
        data = unwrap(response)
        assert isinstance(data, QueryResponse)
        return to_envelope(data)


class ArcadeDBServer:
    """A connection to one ArcadeDB server.

    Scoped to server-level operations (listing and checking databases, server info,
    health and readiness) plus `db()` to reach a specific database.

    This is a context manager because the underlying httpx client owns a connection
    pool that must be released - a concern `@arcadedb/client` does not have, since
    `fetch` owns nothing. Use `with`, or call `close()` yourself.
    """

    def __init__(
        self,
        *,
        base_url: str,
        auth: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
        verify_ssl: bool = True,
    ) -> None:
        merged: dict[str, str] = {**(auth or {}), **(headers or {})}
        #: The generated client this facade is built on. Its
        #: `raise_on_unexpected_status` is False, so it returns a `Response` and does
        #: NOT raise, unlike every method here. That asymmetry is deliberate: use
        #: `raw` when you want to handle an error condition yourself instead of via
        #: `try`/`except`.
        self.raw = Client(base_url=base_url, headers=merged, timeout=timeout, verify_ssl=verify_ssl)

    def db(self, name: str) -> ArcadeDBDatabase:
        """Scopes subsequent calls to one database, reached through this server."""
        return ArcadeDBDatabase(self.raw, name)

    def list_databases(self) -> list[str]:
        """Lists the names of every database visible to the authenticated caller."""
        data = unwrap(list_databases.sync_detailed(client=self.raw))
        result = getattr(data, "result", None)
        return [] if result is None or isinstance(result, Unset) else list(result)

    def exists(self, name: str) -> bool:
        """Checks whether a database exists and is visible to the authenticated caller.

        `False` cannot distinguish "the database does not exist" from "it exists, but
        the caller is not authorized to see it" - the server does not make that
        distinction in its response, so this client cannot either. Do not treat
        `False` as proof the database is absent.
        """
        data = unwrap(check_database_exists.sync_detailed(name, client=self.raw))
        result = getattr(data, "result", None)
        return False if result is None or isinstance(result, Unset) else bool(result)

    def server_info(self) -> ServerInfo:
        """Retrieves server status, version, and configuration information."""
        data = unwrap(get_server_info.sync_detailed(client=self.raw))
        assert isinstance(data, ServerInfo)
        return data

    def health(self) -> None:
        """Liveness probe. Performs no database I/O and requires no authentication.

        Raises `ArcadeDBError` if the server does not answer 204.
        """
        unwrap(check_health.sync_detailed(client=self.raw))

    def ready(self) -> bool:
        """Readiness probe.

        Returns `True` when the server is ready to accept requests and `False` when
        it answers 503 (still starting, not yet joined its Raft group, or catching up
        on replication). Any other failure still raises `ArcadeDBError`.
        """
        response = check_ready.sync_detailed(client=self.raw)
        if int(response.status_code) == 503:
            return False
        if not is_success(response):
            raise ArcadeDBError.from_response(response)
        return True

    def close(self) -> None:
        """Closes the underlying httpx client and its connection pool."""
        self.raw.get_httpx_client().close()

    def __enter__(self) -> ArcadeDBServer:
        self.raw.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.raw.__exit__(exc_type, exc, tb)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest packages/client/tests/test_data.py packages/client/tests/test_server.py -v`
Expected: all pass. If `test_query_sends_params_and_limit_only_when_supplied` fails on the absence
of `params`/`limit`, check that `build_query_request` passes `UNSET` (not `None`) — the generated
`to_dict` omits `UNSET` fields and would serialize `None` as JSON `null`.

- [ ] **Step 6: Lint and typecheck**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add python
git commit -m "feat(python): add the synchronous server, database, and data plane"
```

---

### Task 8: Synchronous transactions

**Files:**
- Create: `python/packages/client/src/arcadedb_client/facade/transaction.py`
- Modify: `python/packages/client/src/arcadedb_client/__init__.py`
- Create: `python/packages/client/tests/test_transaction.py`

**Interfaces:**
- Consumes: Task 7's `ArcadeDBDatabase`, `session_kwarg`, `unwrap`, `is_success`.
- Produces:
  - `begin_transaction(client: Client, database: str) -> str`
  - `commit_transaction(client: Client, database: str, session_id: str) -> None`
  - `rollback_transaction(client: Client, database: str, session_id: str) -> None`
  - `Transaction` context manager whose `__enter__` returns an `ArcadeDBDatabase`
  - `ArcadeDBDatabase.transaction() -> Transaction`

- [ ] **Step 1: Write the failing tests**

`python/packages/client/tests/test_transaction.py`:

```python
import httpx
import pytest
import respx

from arcadedb_client import ArcadeDBError, ArcadeDBServer

BASE_URL = "http://db.test"
SESSION = "AS-0000-1111"


def mock_begin(session_id: str = SESSION) -> None:
    respx.post(f"{BASE_URL}/api/v1/begin/mydb").mock(
        return_value=httpx.Response(204, headers={"arcadedb-session-id": session_id})
    )


@respx.mock
def test_commits_on_a_clean_exit_and_threads_the_session_id() -> None:
    mock_begin()
    command = respx.post(f"{BASE_URL}/api/v1/command/mydb").mock(
        return_value=httpx.Response(200, json={"result": []})
    )
    commit = respx.post(f"{BASE_URL}/api/v1/commit/mydb").mock(return_value=httpx.Response(204))
    rollback = respx.post(f"{BASE_URL}/api/v1/rollback/mydb").mock(return_value=httpx.Response(204))

    with ArcadeDBServer(base_url=BASE_URL) as srv, srv.db("mydb").transaction() as tx:
        tx.command(language="sql", command="INSERT INTO Person SET name = 'Ada'")

    assert command.calls.last.request.headers["arcadedb-session-id"] == SESSION
    assert commit.called
    assert not rollback.called


@respx.mock
def test_calls_outside_the_handle_do_not_join_the_transaction() -> None:
    mock_begin()
    command = respx.post(f"{BASE_URL}/api/v1/command/mydb").mock(
        return_value=httpx.Response(200, json={"result": []})
    )
    respx.post(f"{BASE_URL}/api/v1/commit/mydb").mock(return_value=httpx.Response(204))

    with ArcadeDBServer(base_url=BASE_URL) as srv:
        db = srv.db("mydb")
        with db.transaction():
            db.command(language="sql", command="INSERT INTO P SET n = 1")

    assert "arcadedb-session-id" not in command.calls.last.request.headers


@respx.mock
def test_rolls_back_and_reraises_when_the_body_raises() -> None:
    mock_begin()
    rollback = respx.post(f"{BASE_URL}/api/v1/rollback/mydb").mock(return_value=httpx.Response(204))
    commit = respx.post(f"{BASE_URL}/api/v1/commit/mydb").mock(return_value=httpx.Response(204))

    sentinel = RuntimeError("body failed")
    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(RuntimeError) as caught:
        with srv.db("mydb").transaction():
            raise sentinel

    assert caught.value is sentinel
    assert rollback.called
    assert not commit.called


@respx.mock
def test_a_failed_rollback_is_attached_as_cause_not_substituted() -> None:
    mock_begin()
    respx.post(f"{BASE_URL}/api/v1/rollback/mydb").mock(
        return_value=httpx.Response(500, json={"error": "rollback failed"})
    )

    sentinel = RuntimeError("body failed")
    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(RuntimeError) as caught:
        with srv.db("mydb").transaction():
            raise sentinel

    # The body's error is what the caller asked about, so it wins; the rollback
    # failure rides along rather than replacing it.
    assert caught.value is sentinel
    assert isinstance(caught.value.__cause__, ArcadeDBError)


@respx.mock
def test_an_existing_cause_is_never_overwritten() -> None:
    mock_begin()
    respx.post(f"{BASE_URL}/api/v1/rollback/mydb").mock(
        return_value=httpx.Response(500, json={"error": "rollback failed"})
    )

    original_cause = ValueError("the real reason")
    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(RuntimeError) as caught:
        with srv.db("mydb").transaction():
            raise RuntimeError("body failed") from original_cause

    assert caught.value.__cause__ is original_cause


@respx.mock
def test_a_failed_commit_still_issues_a_rollback_and_raises_the_commit_error() -> None:
    mock_begin()
    respx.post(f"{BASE_URL}/api/v1/commit/mydb").mock(
        return_value=httpx.Response(500, json={"error": "commit failed"})
    )
    rollback = respx.post(f"{BASE_URL}/api/v1/rollback/mydb").mock(return_value=httpx.Response(204))

    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(ArcadeDBError) as caught:
        with srv.db("mydb").transaction():
            pass

    # Without the best-effort rollback the session leaks server-side until
    # arcadedb.server.httpTxExpireTimeout reaps it.
    assert caught.value.error == "commit failed"
    assert rollback.called


@respx.mock
def test_a_rollback_failing_after_a_failed_commit_is_swallowed() -> None:
    mock_begin()
    respx.post(f"{BASE_URL}/api/v1/commit/mydb").mock(
        return_value=httpx.Response(500, json={"error": "commit failed"})
    )
    respx.post(f"{BASE_URL}/api/v1/rollback/mydb").mock(
        return_value=httpx.Response(500, json={"error": "rollback failed too"})
    )

    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(ArcadeDBError) as caught:
        with srv.db("mydb").transaction():
            pass

    assert caught.value.error == "commit failed"


@respx.mock
def test_begin_raises_when_the_server_returns_no_session_id() -> None:
    respx.post(f"{BASE_URL}/api/v1/begin/mydb").mock(return_value=httpx.Response(204))

    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(ArcadeDBError) as caught:
        with srv.db("mydb").transaction():
            pass

    assert "session id" in str(caught.value)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest packages/client/tests/test_transaction.py -v`
Expected: FAIL with `AttributeError: 'ArcadeDBDatabase' object has no attribute 'transaction'`.

- [ ] **Step 3: Write `facade/transaction.py`**

```python
"""Transaction primitives and the synchronous transaction context manager."""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Literal

from .._generated.api.transaction import begin_transaction as begin_op
from .._generated.api.transaction import commit_transaction as commit_op
from .._generated.api.transaction import rollback_transaction as rollback_op
from .._generated.client import Client
from .._internal.unwrap import is_success, unwrap
from ..errors import ArcadeDBError
from .data import SESSION_HEADER

if TYPE_CHECKING:
    from .. import ArcadeDBDatabase


def begin_transaction(client: Client, database: str) -> str:
    """Begins a transaction and returns its session id.

    The endpoint answers 204 with no body and carries the id in the
    `arcadedb-session-id` RESPONSE header, so this reads `headers` rather than
    `parsed`. Threading that id onto every subsequent call is what keeps those calls
    inside the transaction.
    """
    response = begin_op.sync_detailed(database, client=client)
    if not is_success(response):
        raise ArcadeDBError.from_response(response)
    session_id = response.headers.get(SESSION_HEADER)
    if not session_id:
        raise ArcadeDBError(
            int(response.status_code),
            {"error": "begin_transaction did not return a session id"},
        )
    return session_id


def commit_transaction(client: Client, database: str, session_id: str) -> None:
    """Commits the transaction identified by `session_id`. The endpoint answers 204 with no body."""
    unwrap(commit_op.sync_detailed(database, client=client, arcadedb_session_id=session_id))


def rollback_transaction(client: Client, database: str, session_id: str) -> None:
    """Rolls back the transaction identified by `session_id`. The endpoint answers 204 with no body."""
    unwrap(rollback_op.sync_detailed(database, client=client, arcadedb_session_id=session_id))


class Transaction:
    """Runs a block inside a server-side transaction.

    `__enter__` begins the transaction and returns a SECOND `ArcadeDBDatabase`
    carrying the session id, so every call made through that handle - not through
    the outer database object - takes part in the transaction. Commits when the
    block exits cleanly; rolls back and re-raises when it raises.

    Two failure paths beyond the block raising are handled explicitly, so the
    server-side session is never left open and the caller's real error is never
    swallowed:

    - If the block raises and the resulting rollback ALSO fails, the rollback's
      error is attached as `__cause__` on the block's exception rather than
      replacing it - the block's error is what the caller asked about. The attach is
      skipped when `__cause__` is already set (a caller-set causal chain is never
      overwritten) and swallowed if it fails.
    - If the commit itself fails, a best-effort rollback is issued to release the
      session (its own failure discarded - the commit error is what the caller needs
      to see) before the commit error is re-raised. Without this a failed commit
      leaves the session open server-side until `arcadedb.server.httpTxExpireTimeout`
      reaps it.
    """

    def __init__(self, client: Client, database: str) -> None:
        self._client = client
        self._database = database
        self._session_id: str | None = None

    def __enter__(self) -> ArcadeDBDatabase:
        from .. import ArcadeDBDatabase

        self._session_id = begin_transaction(self._client, self._database)
        return ArcadeDBDatabase(self._client, self._database, self._session_id)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        session_id = self._session_id
        assert session_id is not None

        if exc is not None:
            try:
                rollback_transaction(self._client, self._database, session_id)
            except Exception as rollback_err:  # noqa: BLE001
                if exc.__cause__ is None:
                    try:
                        exc.__cause__ = rollback_err
                    except Exception:  # noqa: BLE001, S110
                        # Some libraries intern frozen sentinel errors that cannot take a
                        # new attribute. The rollback failure is dropped in that case;
                        # `exc` is re-raised as itself either way.
                        pass
            return False

        try:
            commit_transaction(self._client, self._database, session_id)
        except Exception:
            try:
                rollback_transaction(self._client, self._database, session_id)
            except Exception:  # noqa: BLE001, S110
                # Best-effort: the commit error is what the caller needs to see, so the
                # rollback's own failure is deliberately discarded rather than chained.
                pass
            raise
        return False
```

- [ ] **Step 4: Wire `transaction()` onto `ArcadeDBDatabase`**

Add to `ArcadeDBDatabase` in `__init__.py`:

```python
    def transaction(self) -> Transaction:
        """Runs a block inside a server-side transaction; see `Transaction`."""
        return Transaction(self._client, self.name)
```

Add the import and the `__all__` entry:

```python
from .facade.transaction import Transaction
```

`__all__` becomes:

```python
__all__ = [
    "ArcadeDBDatabase",
    "ArcadeDBError",
    "ArcadeDBServer",
    "QueryEnvelope",
    "QueryLanguage",
    "Transaction",
    "__version__",
    "basic_auth",
    "bearer_auth",
]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest packages/client/tests/test_transaction.py -v`
Expected: 8 passed.

- [ ] **Step 6: Full check**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add python
git commit -m "feat(python): add synchronous transactions with the full commit/rollback contract"
```

---

### Task 9: The asynchronous facade

**Files:**
- Create: `python/packages/client/src/arcadedb_client/aio.py`
- Modify: `python/packages/client/src/arcadedb_client/__init__.py`
- Create: `python/packages/client/tests/test_async.py`

**Interfaces:**
- Consumes: Task 7's `build_query_request` / `build_command_request` / `to_envelope` / `session_kwarg`, Task 5's `unwrap` / `is_success`, Task 8's transaction contract.
- Produces: `AsyncArcadeDBServer`, `AsyncArcadeDBDatabase`, `AsyncTransaction`, all exported from `arcadedb_client`.

The request-building and envelope-normalising code is shared with the sync facade; only the call
style differs. `unwrap` is shared unchanged, because `asyncio_detailed` returns the same `Response`.

- [ ] **Step 1: Write the failing tests**

`python/packages/client/tests/test_async.py`:

```python
import httpx
import pytest
import respx

from arcadedb_client import ArcadeDBError, AsyncArcadeDBServer

BASE_URL = "http://db.test"
SESSION = "AS-0000-2222"

pytestmark = pytest.mark.asyncio


@respx.mock
async def test_query_returns_the_whole_envelope() -> None:
    respx.post(f"{BASE_URL}/api/v1/query/mydb").mock(
        return_value=httpx.Response(
            200, json={"result": [{"name": "Ada"}], "limit": 100, "returned": 1, "truncated": True}
        )
    )
    async with AsyncArcadeDBServer(base_url=BASE_URL) as srv:
        env = await srv.db("mydb").query(language="sql", command="SELECT FROM Person")

    assert env.result == [{"name": "Ada"}]
    assert env.truncated is True


@respx.mock
async def test_a_non_2xx_raises_arcadedb_error() -> None:
    respx.post(f"{BASE_URL}/api/v1/command/mydb").mock(
        return_value=httpx.Response(400, json={"error": "Invalid"})
    )
    async with AsyncArcadeDBServer(base_url=BASE_URL) as srv:
        with pytest.raises(ArcadeDBError) as caught:
            await srv.db("mydb").command(language="sql", command="NOPE")

    assert caught.value.status == 400


@respx.mock
async def test_list_databases_and_ready() -> None:
    respx.get(f"{BASE_URL}/api/v1/databases").mock(
        return_value=httpx.Response(200, json={"result": ["one"]})
    )
    respx.get(f"{BASE_URL}/api/v1/ready").mock(return_value=httpx.Response(503))
    async with AsyncArcadeDBServer(base_url=BASE_URL) as srv:
        assert await srv.list_databases() == ["one"]
        assert await srv.ready() is False


@respx.mock
async def test_commits_on_a_clean_exit() -> None:
    respx.post(f"{BASE_URL}/api/v1/begin/mydb").mock(
        return_value=httpx.Response(204, headers={"arcadedb-session-id": SESSION})
    )
    command = respx.post(f"{BASE_URL}/api/v1/command/mydb").mock(
        return_value=httpx.Response(200, json={"result": []})
    )
    commit = respx.post(f"{BASE_URL}/api/v1/commit/mydb").mock(return_value=httpx.Response(204))

    async with AsyncArcadeDBServer(base_url=BASE_URL) as srv:
        async with srv.db("mydb").transaction() as tx:
            await tx.command(language="sql", command="INSERT INTO P SET n = 1")

    assert command.calls.last.request.headers["arcadedb-session-id"] == SESSION
    assert commit.called


@respx.mock
async def test_a_failed_rollback_is_attached_as_cause_not_substituted() -> None:
    respx.post(f"{BASE_URL}/api/v1/begin/mydb").mock(
        return_value=httpx.Response(204, headers={"arcadedb-session-id": SESSION})
    )
    respx.post(f"{BASE_URL}/api/v1/rollback/mydb").mock(
        return_value=httpx.Response(500, json={"error": "rollback failed"})
    )

    sentinel = RuntimeError("body failed")
    async with AsyncArcadeDBServer(base_url=BASE_URL) as srv:
        with pytest.raises(RuntimeError) as caught:
            async with srv.db("mydb").transaction():
                raise sentinel

    assert caught.value is sentinel
    assert isinstance(caught.value.__cause__, ArcadeDBError)


@respx.mock
async def test_a_failed_commit_still_issues_a_rollback() -> None:
    respx.post(f"{BASE_URL}/api/v1/begin/mydb").mock(
        return_value=httpx.Response(204, headers={"arcadedb-session-id": SESSION})
    )
    respx.post(f"{BASE_URL}/api/v1/commit/mydb").mock(
        return_value=httpx.Response(500, json={"error": "commit failed"})
    )
    rollback = respx.post(f"{BASE_URL}/api/v1/rollback/mydb").mock(return_value=httpx.Response(204))

    async with AsyncArcadeDBServer(base_url=BASE_URL) as srv:
        with pytest.raises(ArcadeDBError) as caught:
            async with srv.db("mydb").transaction():
                pass

    assert caught.value.error == "commit failed"
    assert rollback.called
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest packages/client/tests/test_async.py -v`
Expected: FAIL with `ImportError: cannot import name 'AsyncArcadeDBServer'`.

- [ ] **Step 3: Write `aio.py`**

```python
"""The asynchronous facade: `AsyncArcadeDBServer`, `AsyncArcadeDBDatabase`, `AsyncTransaction`.

Every generated operation emits both a `sync_detailed` and an `asyncio_detailed`
returning the SAME `Response`, so this module shares request building, envelope
normalisation and `unwrap` with the synchronous facade and differs only in which
call style it uses. The duplication that remains is mechanical and deliberate;
`unasync`-style single-source generation is a non-goal.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import TracebackType
from typing import Any, Literal

import httpx

from ._generated.api.command import execute_command
from ._generated.api.database import check_database_exists, list_databases
from ._generated.api.health import check_health, check_ready
from ._generated.api.query import execute_query_post
from ._generated.api.server import get_server_info
from ._generated.api.transaction import begin_transaction as begin_op
from ._generated.api.transaction import commit_transaction as commit_op
from ._generated.api.transaction import rollback_transaction as rollback_op
from ._generated.client import Client
from ._generated.models.query_response import QueryResponse
from ._generated.models.server_info import ServerInfo
from ._generated.types import Unset
from ._internal.unwrap import is_success, unwrap
from .errors import ArcadeDBError
from .facade.data import (
    SESSION_HEADER,
    QueryEnvelope,
    QueryLanguage,
    build_command_request,
    build_query_request,
    session_kwarg,
    to_envelope,
)

__all__ = ["AsyncArcadeDBDatabase", "AsyncArcadeDBServer", "AsyncTransaction"]


async def begin_transaction(client: Client, database: str) -> str:
    """Begins a transaction and returns its session id, read from the `arcadedb-session-id` response header."""
    response = await begin_op.asyncio_detailed(database, client=client)
    if not is_success(response):
        raise ArcadeDBError.from_response(response)
    session_id = response.headers.get(SESSION_HEADER)
    if not session_id:
        raise ArcadeDBError(
            int(response.status_code),
            {"error": "begin_transaction did not return a session id"},
        )
    return session_id


async def commit_transaction(client: Client, database: str, session_id: str) -> None:
    """Commits the transaction identified by `session_id`."""
    unwrap(await commit_op.asyncio_detailed(database, client=client, arcadedb_session_id=session_id))


async def rollback_transaction(client: Client, database: str, session_id: str) -> None:
    """Rolls back the transaction identified by `session_id`."""
    unwrap(await rollback_op.asyncio_detailed(database, client=client, arcadedb_session_id=session_id))


class AsyncTransaction:
    """The async twin of `Transaction`; the same commit/rollback contract, awaited.

    - The block's exception always wins.
    - A rollback that fails after the block raised is attached as `__cause__` only
      when `__cause__` is unset, and the attach is swallowed if it fails.
    - A commit that fails still issues a best-effort rollback (its own failure
      discarded) before the commit error is re-raised, so the session is not left
      open until `arcadedb.server.httpTxExpireTimeout` reaps it.
    """

    def __init__(self, client: Client, database: str) -> None:
        self._client = client
        self._database = database
        self._session_id: str | None = None

    async def __aenter__(self) -> AsyncArcadeDBDatabase:
        self._session_id = await begin_transaction(self._client, self._database)
        return AsyncArcadeDBDatabase(self._client, self._database, self._session_id)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        session_id = self._session_id
        assert session_id is not None

        if exc is not None:
            try:
                await rollback_transaction(self._client, self._database, session_id)
            except Exception as rollback_err:  # noqa: BLE001
                if exc.__cause__ is None:
                    try:
                        exc.__cause__ = rollback_err
                    except Exception:  # noqa: BLE001, S110
                        pass
            return False

        try:
            await commit_transaction(self._client, self._database, session_id)
        except Exception:
            try:
                await rollback_transaction(self._client, self._database, session_id)
            except Exception:  # noqa: BLE001, S110
                pass
            raise
        return False


class AsyncArcadeDBDatabase:
    """A single database reached through an `AsyncArcadeDBServer`.

    When held as a transaction handle, `session_id` is set and every call made
    through THIS instance carries it. Calls through the outer database object do not
    take part in the transaction.
    """

    def __init__(self, client: Client, name: str, session_id: str | None = None) -> None:
        self._client = client
        self.name = name
        self._session_id = session_id

    async def query(
        self,
        *,
        language: QueryLanguage,
        command: str,
        params: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> QueryEnvelope:
        """Executes a read-or-write query and returns the whole result envelope - not just `result`."""
        response = await execute_query_post.asyncio_detailed(
            self.name,
            client=self._client,
            body=build_query_request(language=language, command=command, params=params, limit=limit),
            arcadedb_session_id=session_kwarg(self._session_id),
        )
        data = unwrap(response)
        assert isinstance(data, QueryResponse)
        return to_envelope(data)

    async def command(
        self,
        *,
        language: QueryLanguage,
        command: str,
        params: dict[str, Any] | None = None,
    ) -> QueryEnvelope:
        """Executes a command and returns the whole result envelope - not just `result`."""
        response = await execute_command.asyncio_detailed(
            self.name,
            client=self._client,
            body=build_command_request(language=language, command=command, params=params),
            arcadedb_session_id=session_kwarg(self._session_id),
        )
        data = unwrap(response)
        assert isinstance(data, QueryResponse)
        return to_envelope(data)

    def transaction(self) -> AsyncTransaction:
        """Runs a block inside a server-side transaction; see `AsyncTransaction`."""
        return AsyncTransaction(self._client, self.name)


class AsyncArcadeDBServer:
    """The async twin of `ArcadeDBServer`.

    An async context manager because the underlying `httpx.AsyncClient` owns a
    connection pool that must be released. Use `async with`, or `await aclose()`.
    """

    def __init__(
        self,
        *,
        base_url: str,
        auth: Mapping[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
        verify_ssl: bool = True,
    ) -> None:
        merged: dict[str, str] = {**(auth or {}), **(headers or {})}
        #: The generated client. Returns a `Response` and does NOT raise, unlike
        #: every method here.
        self.raw = Client(base_url=base_url, headers=merged, timeout=timeout, verify_ssl=verify_ssl)

    def db(self, name: str) -> AsyncArcadeDBDatabase:
        """Scopes subsequent calls to one database, reached through this server."""
        return AsyncArcadeDBDatabase(self.raw, name)

    async def list_databases(self) -> list[str]:
        """Lists the names of every database visible to the authenticated caller."""
        data = unwrap(await list_databases.asyncio_detailed(client=self.raw))
        result = getattr(data, "result", None)
        return [] if result is None or isinstance(result, Unset) else list(result)

    async def exists(self, name: str) -> bool:
        """Checks whether a database exists and is visible to the authenticated caller.

        `False` cannot distinguish absence from a lack of authorization; the server
        does not make that distinction, so this client cannot either.
        """
        data = unwrap(await check_database_exists.asyncio_detailed(name, client=self.raw))
        result = getattr(data, "result", None)
        return False if result is None or isinstance(result, Unset) else bool(result)

    async def server_info(self) -> ServerInfo:
        """Retrieves server status, version, and configuration information."""
        data = unwrap(await get_server_info.asyncio_detailed(client=self.raw))
        assert isinstance(data, ServerInfo)
        return data

    async def health(self) -> None:
        """Liveness probe. Raises `ArcadeDBError` if the server does not answer 204."""
        unwrap(await check_health.asyncio_detailed(client=self.raw))

    async def ready(self) -> bool:
        """Readiness probe. `False` on 503; any other failure raises `ArcadeDBError`."""
        response = await check_ready.asyncio_detailed(client=self.raw)
        if int(response.status_code) == 503:
            return False
        if not is_success(response):
            raise ArcadeDBError.from_response(response)
        return True

    async def aclose(self) -> None:
        """Closes the underlying httpx client and its connection pool."""
        await self.raw.get_async_httpx_client().aclose()

    async def __aenter__(self) -> AsyncArcadeDBServer:
        await self.raw.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.raw.__aexit__(exc_type, exc, tb)
```

- [ ] **Step 4: Re-export from `__init__.py`**

Add:

```python
from .aio import AsyncArcadeDBDatabase, AsyncArcadeDBServer, AsyncTransaction
```

and add `"AsyncArcadeDBDatabase"`, `"AsyncArcadeDBServer"`, `"AsyncTransaction"` to `__all__`,
keeping it alphabetically sorted.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest packages/client/tests/test_async.py -v`
Expected: 6 passed.

- [ ] **Step 6: Full check**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add python
git commit -m "feat(python): add the asynchronous facade over the shared generated layer"
```

---

### Task 10: The `ts`, `grafana` and `promql` namespaces

**Files:**
- Create: `python/packages/client/src/arcadedb_client/facade/timeseries.py`
- Create: `python/packages/client/src/arcadedb_client/facade/dashboards.py`
- Modify: `python/packages/client/src/arcadedb_client/__init__.py`, `python/packages/client/src/arcadedb_client/aio.py`
- Create: `python/packages/client/tests/test_timeseries.py`, `python/packages/client/tests/test_dashboards.py`

**Interfaces:**
- Consumes: `unwrap`, the generated `time_series`, `grafana` and `prom_ql` operation modules.
- Produces: `db.ts` (`.write(...)`, `.query(...)`, `.latest(...)`), `db.grafana` (`.query(...)`), `db.promql` (`.query(...)`, `.query_range(...)`, `.labels()`, `.series(...)`), on both the sync and async database classes.

**`ts.write` is hand-written.** The generator skips `POST /api/v1/ts/{database}/write` because its
body is `text/plain`, so this posts through the pooled httpx client the generated operations already
use. Unlike TypeScript, the namespaces do **not** lazily import their implementation — that is a
bundler contract with no Python meaning, and there is no tree-shaking test to satisfy.

- [ ] **Step 1: Write the failing tests**

`python/packages/client/tests/test_timeseries.py`:

```python
import httpx
import pytest
import respx

from arcadedb_client import ArcadeDBError, ArcadeDBServer, AsyncArcadeDBServer

BASE_URL = "http://db.test"


@respx.mock
def test_write_posts_line_protocol_as_text_plain() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/ts/mydb/write").mock(return_value=httpx.Response(204))
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        srv.db("mydb").ts.write(line_protocol="cpu,host=a value=0.9 1700000000000000000")

    request = route.calls.last.request
    assert request.headers["Content-Type"].startswith("text/plain")
    assert request.read() == b"cpu,host=a value=0.9 1700000000000000000"
    assert "precision" not in str(request.url)


@respx.mock
def test_write_sends_precision_when_supplied() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/ts/mydb/write").mock(return_value=httpx.Response(204))
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        srv.db("mydb").ts.write(line_protocol="cpu value=1 1700000000000", precision="ms")

    assert "precision=ms" in str(route.calls.last.request.url)


@respx.mock
def test_write_raises_on_a_non_2xx() -> None:
    respx.post(f"{BASE_URL}/api/v1/ts/mydb/write").mock(
        return_value=httpx.Response(400, json={"error": "bad line protocol"})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv, pytest.raises(ArcadeDBError) as caught:
        srv.db("mydb").ts.write(line_protocol="garbage")

    assert caught.value.error == "bad line protocol"


@respx.mock
def test_query_returns_the_raw_response_shape_unaltered() -> None:
    respx.post(f"{BASE_URL}/api/v1/ts/mydb/query").mock(
        return_value=httpx.Response(200, json={"rows": [[1700000000000, 0.9]]})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        result = srv.db("mydb").ts.query(body={"type": "cpu"})

    # The endpoint answers a oneOf: TimeSeriesRawResponse without an aggregation,
    # TimeSeriesAggregatedResponse with one. The facade passes both through
    # unaltered; narrow with isinstance where TypeScript narrows with `in`.
    assert result.rows == [[1700000000000, 0.9]]


@pytest.mark.asyncio
@respx.mock
async def test_async_write_posts_line_protocol() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/ts/mydb/write").mock(return_value=httpx.Response(204))
    async with AsyncArcadeDBServer(base_url=BASE_URL) as srv:
        await srv.db("mydb").ts.write(line_protocol="cpu value=1 1700000000000")

    assert route.calls.last.request.headers["Content-Type"].startswith("text/plain")
```

`python/packages/client/tests/test_dashboards.py`:

```python
import httpx
import respx

from arcadedb_client import ArcadeDBServer

BASE_URL = "http://db.test"


@respx.mock
def test_promql_labels_returns_the_generated_model() -> None:
    respx.get(f"{BASE_URL}/api/v1/ts/mydb/prom/api/v1/labels").mock(
        return_value=httpx.Response(200, json={"status": "success", "data": ["__name__", "host"]})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        result = srv.db("mydb").promql.labels()

    assert result.data == ["__name__", "host"]


@respx.mock
def test_grafana_query_reaches_the_right_route() -> None:
    route = respx.post(f"{BASE_URL}/api/v1/ts/mydb/grafana/query").mock(
        return_value=httpx.Response(200, json={"results": {}})
    )
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        srv.db("mydb").grafana.query(body={"targets": []})

    assert route.called


@respx.mock
def test_the_namespaces_are_cached_per_database_handle() -> None:
    with ArcadeDBServer(base_url=BASE_URL) as srv:
        db = srv.db("mydb")
        assert db.ts is db.ts
        assert db.grafana is db.grafana
        assert db.promql is db.promql
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest packages/client/tests/test_timeseries.py packages/client/tests/test_dashboards.py -v`
Expected: FAIL with `AttributeError: 'ArcadeDBDatabase' object has no attribute 'ts'`.

- [ ] **Step 3: Write `facade/timeseries.py`**

```python
"""The `db.ts` namespace: ingesting and querying samples in a time-series type.

`write` is HAND-WRITTEN. `openapi-python-client` skips
`POST /api/v1/ts/{database}/write` because its body is `text/plain`, not JSON -
see `scripts/check_codegen_skips.py`, which pins that skip so a future contract
cannot silently drop another endpoint the same way. The request goes through the
generated client's own pooled httpx client, so it shares connections, headers and
timeout with every generated call.
"""

from __future__ import annotations

from typing import Any, Literal

from .._generated.api.time_series import get_time_series_latest, query_time_series
from .._generated.client import Client
from .._generated.models.time_series_aggregated_response import TimeSeriesAggregatedResponse
from .._generated.models.time_series_latest_response import TimeSeriesLatestResponse
from .._generated.models.time_series_query_request import TimeSeriesQueryRequest
from .._generated.models.time_series_raw_response import TimeSeriesRawResponse
from .._generated.types import Response
from .._internal.unwrap import unwrap
from ..errors import ArcadeDBError

#: Unit of the timestamps in a line-protocol payload. Defaults to nanoseconds server-side when omitted.
Precision = Literal["ns", "us", "ms", "s"]

TimeSeriesQueryResult = TimeSeriesRawResponse | TimeSeriesAggregatedResponse


def _write_url(database: str) -> str:
    return f"/api/v1/ts/{database}/write"


def _write_response(raw: Any) -> None:
    """Raises `ArcadeDBError` unless the server answered 2xx. The endpoint answers 204 with no body."""
    if not 200 <= raw.status_code < 300:
        raise ArcadeDBError(raw.status_code, raw.content, raw.headers.get("X-Request-Id"))


class TimeSeriesNamespace:
    """Ingests and queries samples in a time-series type - the `db.ts` namespace."""

    def __init__(self, client: Client, database: str) -> None:
        self._client = client
        self._database = database

    def write(self, *, line_protocol: str, precision: Precision | None = None) -> None:
        """Ingests samples in InfluxDB Line Protocol.

        The endpoint takes the line-protocol text as a raw `text/plain` body, not
        JSON, which is why this is hand-written rather than generated.
        """
        raw = self._client.get_httpx_client().post(
            _write_url(self._database),
            content=line_protocol.encode("utf-8"),
            headers={"Content-Type": "text/plain"},
            params=None if precision is None else {"precision": precision},
        )
        _write_response(raw)

    def query(self, *, body: dict[str, Any]) -> TimeSeriesQueryResult:
        """Queries samples, optionally aggregated into buckets.

        Returns whichever member of the contract's `oneOf` the server sent:
        `TimeSeriesRawResponse` without an aggregation, `TimeSeriesAggregatedResponse`
        with one. Narrow with `isinstance`.
        """
        response = query_time_series.sync_detailed(
            self._database, client=self._client, body=TimeSeriesQueryRequest.from_dict(body)
        )
        data = unwrap(response)
        assert isinstance(data, TimeSeriesRawResponse | TimeSeriesAggregatedResponse)
        return data

    def latest(self, **kwargs: Any) -> TimeSeriesLatestResponse:
        """Returns the most recent sample per series."""
        data = unwrap(get_time_series_latest.sync_detailed(self._database, client=self._client, **kwargs))
        assert isinstance(data, TimeSeriesLatestResponse)
        return data


class AsyncTimeSeriesNamespace:
    """The async twin of `TimeSeriesNamespace`."""

    def __init__(self, client: Client, database: str) -> None:
        self._client = client
        self._database = database

    async def write(self, *, line_protocol: str, precision: Precision | None = None) -> None:
        """Ingests samples in InfluxDB Line Protocol."""
        raw = await self._client.get_async_httpx_client().post(
            _write_url(self._database),
            content=line_protocol.encode("utf-8"),
            headers={"Content-Type": "text/plain"},
            params=None if precision is None else {"precision": precision},
        )
        _write_response(raw)

    async def query(self, *, body: dict[str, Any]) -> TimeSeriesQueryResult:
        """Queries samples, optionally aggregated into buckets."""
        response = await query_time_series.asyncio_detailed(
            self._database, client=self._client, body=TimeSeriesQueryRequest.from_dict(body)
        )
        data = unwrap(response)
        assert isinstance(data, TimeSeriesRawResponse | TimeSeriesAggregatedResponse)
        return data

    async def latest(self, **kwargs: Any) -> TimeSeriesLatestResponse:
        """Returns the most recent sample per series."""
        data = unwrap(
            await get_time_series_latest.asyncio_detailed(self._database, client=self._client, **kwargs)
        )
        assert isinstance(data, TimeSeriesLatestResponse)
        return data
```

Note: `TimeSeriesRawResponse | TimeSeriesAggregatedResponse` inside `isinstance` requires Python
3.10, which is the declared floor.

- [ ] **Step 4: Write `facade/dashboards.py`**

```python
"""The `db.grafana` and `db.promql` namespaces.

Both pass the generated request and response models through unaltered, exactly as
`facade/dashboards.ts` re-exports `components["schemas"][...]` unaltered. `Unset` is
visible on optional fields here in the same way `?: T | undefined` is visible in
TypeScript; the normalising `QueryEnvelope` treatment is deliberately confined to
the data plane.
"""

from __future__ import annotations

from typing import Any

from .._generated.api.grafana import query_grafana
from .._generated.api.prom_ql import (
    prom_ql_labels,
    prom_ql_query,
    prom_ql_query_range,
    prom_ql_series,
)
from .._generated.client import Client
from .._generated.models.grafana_query_request import GrafanaQueryRequest
from .._generated.models.grafana_query_response import GrafanaQueryResponse
from .._generated.models.prom_ql_data_response import PromQLDataResponse
from .._generated.models.prom_ql_labels_response import PromQLLabelsResponse
from .._generated.models.prom_ql_series_response import PromQLSeriesResponse
from .._internal.unwrap import unwrap


class GrafanaNamespace:
    """Grafana panel queries over a time-series type - the `db.grafana` namespace."""

    def __init__(self, client: Client, database: str) -> None:
        self._client = client
        self._database = database

    def query(self, *, body: dict[str, Any]) -> GrafanaQueryResponse:
        """Executes one query per `targets` entry, returning DataFrames keyed by `refId`."""
        data = unwrap(
            query_grafana.sync_detailed(
                self._database, client=self._client, body=GrafanaQueryRequest.from_dict(body)
            )
        )
        assert isinstance(data, GrafanaQueryResponse)
        return data


class PromQLNamespace:
    """A Prometheus-compatible query surface over a time-series type - the `db.promql` namespace."""

    def __init__(self, client: Client, database: str) -> None:
        self._client = client
        self._database = database

    def query(self, **kwargs: Any) -> PromQLDataResponse:
        """Evaluates a PromQL expression at one instant."""
        data = unwrap(prom_ql_query.sync_detailed(self._database, client=self._client, **kwargs))
        assert isinstance(data, PromQLDataResponse)
        return data

    def query_range(self, **kwargs: Any) -> PromQLDataResponse:
        """Evaluates a PromQL expression at every step across a range."""
        data = unwrap(prom_ql_query_range.sync_detailed(self._database, client=self._client, **kwargs))
        assert isinstance(data, PromQLDataResponse)
        return data

    def labels(self) -> PromQLLabelsResponse:
        """Lists every label name present in the database, sorted, always including `__name__`."""
        data = unwrap(prom_ql_labels.sync_detailed(self._database, client=self._client))
        assert isinstance(data, PromQLLabelsResponse)
        return data

    def series(self, **kwargs: Any) -> PromQLSeriesResponse:
        """Returns the label sets of the series matching the given `match[]` selectors."""
        data = unwrap(prom_ql_series.sync_detailed(self._database, client=self._client, **kwargs))
        assert isinstance(data, PromQLSeriesResponse)
        return data


class AsyncGrafanaNamespace:
    """The async twin of `GrafanaNamespace`."""

    def __init__(self, client: Client, database: str) -> None:
        self._client = client
        self._database = database

    async def query(self, *, body: dict[str, Any]) -> GrafanaQueryResponse:
        """Executes one query per `targets` entry, returning DataFrames keyed by `refId`."""
        data = unwrap(
            await query_grafana.asyncio_detailed(
                self._database, client=self._client, body=GrafanaQueryRequest.from_dict(body)
            )
        )
        assert isinstance(data, GrafanaQueryResponse)
        return data


class AsyncPromQLNamespace:
    """The async twin of `PromQLNamespace`."""

    def __init__(self, client: Client, database: str) -> None:
        self._client = client
        self._database = database

    async def query(self, **kwargs: Any) -> PromQLDataResponse:
        """Evaluates a PromQL expression at one instant."""
        data = unwrap(await prom_ql_query.asyncio_detailed(self._database, client=self._client, **kwargs))
        assert isinstance(data, PromQLDataResponse)
        return data

    async def query_range(self, **kwargs: Any) -> PromQLDataResponse:
        """Evaluates a PromQL expression at every step across a range."""
        data = unwrap(
            await prom_ql_query_range.asyncio_detailed(self._database, client=self._client, **kwargs)
        )
        assert isinstance(data, PromQLDataResponse)
        return data

    async def labels(self) -> PromQLLabelsResponse:
        """Lists every label name present in the database, sorted, always including `__name__`."""
        data = unwrap(await prom_ql_labels.asyncio_detailed(self._database, client=self._client))
        assert isinstance(data, PromQLLabelsResponse)
        return data

    async def series(self, **kwargs: Any) -> PromQLSeriesResponse:
        """Returns the label sets of the series matching the given `match[]` selectors."""
        data = unwrap(await prom_ql_series.asyncio_detailed(self._database, client=self._client, **kwargs))
        assert isinstance(data, PromQLSeriesResponse)
        return data
```

- [ ] **Step 5: Attach the namespaces to both database classes**

In `__init__.py`, add to `ArcadeDBDatabase`:

```python
    @cached_property
    def ts(self) -> TimeSeriesNamespace:
        """Ingests and queries samples in a time-series type."""
        return TimeSeriesNamespace(self._client, self.name)

    @cached_property
    def grafana(self) -> GrafanaNamespace:
        """Grafana panel queries over a time-series type."""
        return GrafanaNamespace(self._client, self.name)

    @cached_property
    def promql(self) -> PromQLNamespace:
        """A Prometheus-compatible query surface over a time-series type."""
        return PromQLNamespace(self._client, self.name)
```

with `from functools import cached_property` and the namespace imports. Add the async equivalents
to `AsyncArcadeDBDatabase` in `aio.py` using `AsyncTimeSeriesNamespace`, `AsyncGrafanaNamespace` and
`AsyncPromQLNamespace`.

`cached_property` needs a `__dict__`, so neither database class may declare `__slots__`.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest packages/client/tests/test_timeseries.py packages/client/tests/test_dashboards.py -v`
Expected: all pass.

- [ ] **Step 7: Full check**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add python
git commit -m "feat(python): add the ts, grafana and promql namespaces with a hand-written ts.write"
```

---

### Task 11: Public surface lock and the package README

**Files:**
- Create: `python/packages/client/tests/test_public_surface.py`
- Create: `python/packages/client/README.md`
- Modify: `python/packages/client/src/arcadedb_client/__init__.py`

**Interfaces:**
- Consumes: everything above.
- Produces: a test that fails whenever `__all__` changes without the change being deliberate.

This is the honest Python replacement for `test/treeshake.test.ts`: the same job of guarding an
API-shape promise that is easy to break invisibly, by the mechanism this language actually has.

- [ ] **Step 1: Write the failing test**

`python/packages/client/tests/test_public_surface.py`:

```python
import arcadedb_client

EXPECTED_SURFACE = {
    "ArcadeDBDatabase",
    "ArcadeDBError",
    "ArcadeDBServer",
    "AsyncArcadeDBDatabase",
    "AsyncArcadeDBServer",
    "AsyncTransaction",
    "QueryEnvelope",
    "QueryLanguage",
    "Transaction",
    "__version__",
    "basic_auth",
    "bearer_auth",
}


def test_all_is_exactly_the_documented_surface() -> None:
    # Changing this set is a deliberate API decision, not a refactor. If this test
    # fails, update EXPECTED_SURFACE and the README's API section together.
    assert set(arcadedb_client.__all__) == EXPECTED_SURFACE


def test_all_is_sorted_and_free_of_duplicates() -> None:
    assert arcadedb_client.__all__ == sorted(set(arcadedb_client.__all__))


def test_every_name_in_all_actually_resolves() -> None:
    for name in arcadedb_client.__all__:
        assert hasattr(arcadedb_client, name), f"__all__ names {name}, which does not exist"


def test_the_generated_package_is_not_part_of_the_public_surface() -> None:
    # `_generated` is reachable as `arcadedb_client._generated` on purpose - `.raw`
    # returns its Client - but it must never be re-exported at the top level, or a
    # contract bump becomes a breaking change to this package's API.
    assert "_generated" not in arcadedb_client.__all__
    assert not any(name.startswith("_") and name != "__version__" for name in arcadedb_client.__all__)
```

- [ ] **Step 2: Run the test to verify it fails or passes**

Run: `uv run pytest packages/client/tests/test_public_surface.py -v`
Expected: passes if Task 9's `__all__` edit was made correctly; if it fails, the message names the
exact discrepancy — fix `__all__`, not the test, unless the surface change was intended.

- [ ] **Step 3: Write the package README**

`python/packages/client/README.md` mirrors `typescript/packages/client/README.md`'s section
structure, with Python examples:

- `# arcadedb-client` — one-paragraph description.
- `## Requirements` — Python >= 3.10; an ArcadeDB server >= the version in the compatibility table.
- `## Installation` — `pip install arcadedb-client` and `uv add arcadedb-client`.
- `## Quick start` — the sync example, then the async example.
- `## The result envelope, and why `truncated` matters` — port the TypeScript section, including that raising `limit` is not always the fix, because a result over the server's hard ceiling is refused with 413 rather than truncated.
- `## Sync and async` — the two facades; the connection-pool reason both are context managers.
- `## Transactions` — the context manager, that calls through the outer handle do not join the transaction, and the three-clause commit/rollback contract.
- `## Two error models` — the facade raises `ArcadeDBError`; `.raw` returns a `Response` and never raises. Note that `help_` is spelled to match the generated model.
- `## `exists` cannot prove absence` — port verbatim in substance.
- `## Endpoints this client does not wrap` — `batch`, `prom/read`, `prom/write`; that `ts.write` is hand-written because the generator cannot model a `text/plain` body; and that `scripts/check_codegen_skips.py` keeps the list honest.
- `## Contract version and compatibility` — a table with one row: `| 0.1.0 | 26.9.1-SNAPSHOT |`. This table is a historical record; `adopt-contract-version.sh` deliberately does not touch it.
- `## License` — Apache-2.0.

- [ ] **Step 4: Full check**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add python
git commit -m "docs(python): lock the public surface with a test and document the client"
```

---

### Task 12: The e2e suite

**Files:**
- Create: `python/e2e/__init__.py`, `python/e2e/conftest.py`, `python/e2e/test_data_plane.py`
- Modify: `.github/workflows/ci-python.yml`

**Interfaces:**
- Consumes: the whole client.
- Produces: `uv run pytest e2e` running against a real container; a fixture exposing `base_url` and a created database.

- [ ] **Step 1: Write the container fixture**

`python/e2e/conftest.py`:

```python
"""Fixtures for the end-to-end suite. Requires Docker."""

from __future__ import annotations

import os
import time
from collections.abc import Iterator

import httpx
import pytest
from testcontainers.core.container import DockerContainer

# Image pin: arcadedata/arcadedb:26.8.1 is correct here even though the OpenAPI
# contract this client is generated from is newer (26.9.1-SNAPSHOT). The upstream
# fixes the newer contract carries changed only spec-generator classes (M0) - no
# request handler changed. The server has always answered 204 on the transaction
# endpoints and has always used the arcadedb-session-id header; the spec was simply
# wrong about it. CommandRequest.language was the same story: the contract now marks
# it required (upstream fix #6562), and the 26.8.1 SERVER already required it too.
# So a client generated from the newer contract works unmodified against 26.8.1.
#
# DO NOT GENERALISE THIS. It holds only because this particular contract bump was a
# documentation fix. The moment a contract bump reflects a real wire change, this
# pin must move with it.
DEFAULT_ARCADEDB_IMAGE = "arcadedata/arcadedb:26.8.1"

# ARCADEDB_DOCKER_IMAGE overrides the pin. It exists for the smoke job in
# ArcadeData/arcadedb, which runs against the image built from the server commit
# under review rather than a published tag - the only check that catches a
# payload-shape change on the PR that introduces one. The variable name matches the
# one ArcadeDB's own e2e-js suite uses, so the harnesses are driven the same way.
ARCADEDB_IMAGE = os.environ.get("ARCADEDB_DOCKER_IMAGE", DEFAULT_ARCADEDB_IMAGE)

ROOT_PASSWORD = "playwithdata"
DB_NAME = "clienttest"


def _wait_until_ready(base_url: str, timeout: float = 90.0) -> None:
    """Polls /api/v1/ready for a 204.

    testcontainers-python's wait_for_logs matches log OUTPUT, not an HTTP status, so
    readiness is polled here rather than expressed as a built-in wait strategy.
    """
    deadline = time.monotonic() + timeout
    last: Exception | None = None
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"{base_url}/api/v1/ready", timeout=5.0).status_code == 204:
                return
        except httpx.HTTPError as err:  # the port is not accepting connections yet
            last = err
        time.sleep(1.0)
    raise TimeoutError(f"{base_url} was not ready within {timeout}s") from last


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    """Starts an ArcadeDB container and yields its base URL.

    The port is exposed, not bound: a developer machine may already have ArcadeDB on
    host port 2480, so binding directly would clash.
    """
    container = (
        DockerContainer(ARCADEDB_IMAGE)
        .with_env("JAVA_OPTS", f"-Darcadedb.server.rootPassword={ROOT_PASSWORD}")
        .with_exposed_ports(2480)
    )
    with container:
        url = f"http://{container.get_container_host_ip()}:{container.get_exposed_port(2480)}"
        _wait_until_ready(url)
        yield url


@pytest.fixture(scope="session")
def database(base_url: str) -> str:
    """Creates the test database and returns its name.

    No dedicated create-database endpoint exists; database creation goes through the
    generic server-command endpoint (POST /api/v1/server), the same one root-only
    administrative commands share.
    """
    from arcadedb_client import ArcadeDBServer, basic_auth

    with ArcadeDBServer(base_url=base_url, auth=basic_auth("root", ROOT_PASSWORD)) as srv:
        from arcadedb_client._generated.api.server import execute_server_command
        from arcadedb_client._generated.models.command_request import CommandRequest
        from arcadedb_client._internal.unwrap import unwrap

        unwrap(
            execute_server_command.sync_detailed(
                client=srv.raw,
                body=CommandRequest(command=f"create database {DB_NAME}", language="sql"),
            )
        )
    return DB_NAME
```

`python/e2e/__init__.py` is empty.

- [ ] **Step 2: Write the e2e tests**

`python/e2e/test_data_plane.py`:

```python
"""End-to-end tests against a real ArcadeDB server. Requires Docker."""

from __future__ import annotations

import pytest

from arcadedb_client import ArcadeDBError, ArcadeDBServer, AsyncArcadeDBServer, basic_auth

from .conftest import ROOT_PASSWORD


def test_sync_round_trip(base_url: str, database: str) -> None:
    with ArcadeDBServer(base_url=base_url, auth=basic_auth("root", ROOT_PASSWORD)) as srv:
        assert srv.ready() is True
        assert database in srv.list_databases()
        assert srv.exists(database) is True

        db = srv.db(database)
        db.command(language="sql", command="CREATE VERTEX TYPE PersonSync IF NOT EXISTS")
        db.command(language="sql", command="INSERT INTO PersonSync SET name = 'Ada', age = 36")

        env = db.query(
            language="sql",
            command="SELECT FROM PersonSync WHERE age > :min",
            params={"min": 18},
        )
        assert [row["name"] for row in env.result] == ["Ada"]
        assert env.truncated is False


def test_a_transaction_commits(base_url: str, database: str) -> None:
    with ArcadeDBServer(base_url=base_url, auth=basic_auth("root", ROOT_PASSWORD)) as srv:
        db = srv.db(database)
        db.command(language="sql", command="CREATE VERTEX TYPE TxCommit IF NOT EXISTS")

        with db.transaction() as tx:
            tx.command(language="sql", command="INSERT INTO TxCommit SET n = 1")

        env = db.query(language="sql", command="SELECT count(*) AS c FROM TxCommit")
        assert env.result[0]["c"] == 1


def test_a_transaction_rolls_back_on_an_exception(base_url: str, database: str) -> None:
    with ArcadeDBServer(base_url=base_url, auth=basic_auth("root", ROOT_PASSWORD)) as srv:
        db = srv.db(database)
        db.command(language="sql", command="CREATE VERTEX TYPE TxRollback IF NOT EXISTS")

        with pytest.raises(RuntimeError):
            with db.transaction() as tx:
                tx.command(language="sql", command="INSERT INTO TxRollback SET n = 1")
                raise RuntimeError("abort")

        env = db.query(language="sql", command="SELECT count(*) AS c FROM TxRollback")
        assert env.result[0]["c"] == 0


def test_a_bad_query_raises_arcadedb_error_with_a_request_id(base_url: str, database: str) -> None:
    with ArcadeDBServer(base_url=base_url, auth=basic_auth("root", ROOT_PASSWORD)) as srv:
        with pytest.raises(ArcadeDBError) as caught:
            srv.db(database).query(language="sql", command="SELCT nonsense")

    assert caught.value.status >= 400
    assert caught.value.request_id is not None


@pytest.mark.asyncio
async def test_async_round_trip(base_url: str, database: str) -> None:
    async with AsyncArcadeDBServer(base_url=base_url, auth=basic_auth("root", ROOT_PASSWORD)) as srv:
        assert await srv.ready() is True

        db = srv.db(database)
        await db.command(language="sql", command="CREATE VERTEX TYPE PersonAsync IF NOT EXISTS")

        async with db.transaction() as tx:
            await tx.command(language="sql", command="INSERT INTO PersonAsync SET name = 'Grace'")

        env = await db.query(language="sql", command="SELECT FROM PersonAsync")
        assert [row["name"] for row in env.result] == ["Grace"]
```

- [ ] **Step 3: Run the e2e suite**

Run: `uv run pytest e2e -v`
Expected: all pass. First run pulls the image; allow several minutes.

- [ ] **Step 4: Confirm the unit suite still never starts a container**

Run: `uv run pytest`
Expected: it collects only `packages/client/tests` (`testpaths` in Task 1) and finishes without
Docker.

- [ ] **Step 5: Add the e2e job to CI**

Append to `.github/workflows/ci-python.yml`:

```yaml
  e2e:
    name: End-to-end against a real server
    needs: build
    runs-on: ubuntu-latest
    # Container pull plus ArcadeDB JVM startup can run well past what the unit job
    # needs; an explicit cap keeps a hung container from burning the runner's
    # default multi-hour budget instead of failing fast.
    timeout-minutes: 15
    steps:
      - name: Checkout
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
          cache-dependency-glob: python/uv.lock

      - name: Set up Python
        working-directory: python
        # 3.14, not the build job's 3.10: the two jobs together cover the declared
        # floor and the current release without a matrix.
        run: uv python install 3.14

      - name: Install dependencies
        working-directory: python
        run: uv sync --frozen --python 3.14

      - name: E2E tests against a real ArcadeDB server
        working-directory: python
        run: uv run pytest e2e -v
```

- [ ] **Step 6: Commit**

```bash
git add python .github/workflows/ci-python.yml
git commit -m "test(python): add the end-to-end suite against a real ArcadeDB container"
```

---

### Task 13: Make `adopt-contract-version.sh` language-aware

**Files:**
- Modify: `scripts/adopt-contract-version.sh`
- Modify: `scripts/tests/test-contract-scripts.sh`

**Interfaces:**
- Consumes: `python/packages/client/pyproject.toml`'s `[tool.arcadedb] server-version`.
- Produces: `adopt-contract-version.sh <version>` leaves both `typescript/` and `python/` consistent with one contract version.

- [ ] **Step 1: Add the Python language entry**

In `scripts/adopt-contract-version.sh`, replace the single hardcoded `TS_DIR` walk with an explicit
table of language directories, each with its own file extensions and skip set. Inside the embedded
Python block, replace the `ts = root / "typescript"` / `candidates()` pair with:

```python
# An explicit table, not filesystem discovery. The "found by search rather than
# hardcoded" rule above governs FILES WITHIN a language directory - a new source
# file must not escape repointing by not being on a list. Which top-level
# directories are language clients is a different question, and a script that
# silently began rewriting any new sibling of contracts/ would be worse, not
# better. Adding a language stays a deliberate one-line change here.
LANGUAGES = {
    "typescript": {
        "suffixes": (".ts", ".md"),
        "skip_dirs": {"node_modules", ".git", "dist", "gen", ".superpowers", "docs"},
    },
    "python": {
        "suffixes": (".py", ".md", ".toml"),
        "skip_dirs": {
            "_generated",
            "__pycache__",
            ".venv",
            ".git",
            "dist",
            "build",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            "docs",
        },
    },
}


def candidates():
    for language, config in LANGUAGES.items():
        base = root / language
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in config["suffixes"]:
                continue
            if any(part in config["skip_dirs"] for part in path.relative_to(root).parts):
                continue
            yield path
```

- [ ] **Step 2: Rewrite the recorded server version in `pyproject.toml`**

After the existing `package.json` loop, add:

```python
# pyproject.toml carries server-version as real data. Python has tomllib for
# reading and no stdlib writer, so this is a targeted line substitution that
# asserts it matched exactly once - a malformed or duplicated key fails loudly
# rather than silently leaving a stale version behind.
PYPROJECT_SERVER_VERSION = re.compile(r'^(server-version\s*=\s*")[^"]*(")', re.MULTILINE)

for pyproject in sorted((root / "python").glob("packages/*/pyproject.toml")):
    original = pyproject.read_text()
    updated, count = PYPROJECT_SERVER_VERSION.subn(rf"\g<1>{version}\g<2>", original)
    if count > 1:
        raise SystemExit(f"{pyproject} has {count} server-version keys; expected exactly one")
    if count == 1 and updated != original:
        pyproject.write_text(updated)
        changed.append(pyproject.relative_to(root))
```

- [ ] **Step 3: Extend `make_fixture` to lay down a Python package**

`scripts/tests/test-contract-scripts.sh` already has `make_fixture`, `ok`, `bad` and `check`
(`scripts/tests/test-contract-scripts.sh:27-29,34`). Do not add a parallel fixture or a new
assertion helper — extend the one that exists.

Add `"$root/python/packages/client"` to `make_fixture`'s `mkdir -p` list, and add this before its
closing `echo "$root"`:

```bash
  cat > "$root/python/packages/client/pyproject.toml" <<TOML
[project]
name = "arcadedb-client"
version = "0.1.0"

[tool.arcadedb]
server-version = "${version}"
TOML
  cat > "$root/python/packages/client/README.md" <<MD
This package was generated from \`contracts/arcadedb-openapi-${version}.json\`.

| Package | Server contract |
| --- | --- |
| 0.1.0 | ${version} |
MD
  cat > "$root/python/packages/client/src_index.py" <<PY
# The contract this client is generated from is ${version}, in prose.
PY
```

(`src_index.py` sits directly in the package directory rather than under `src/arcadedb_client/`
because the fixture only needs a `.py` file outside the `_generated` skip set for the prose-repointing
assertion.)

- [ ] **Step 4: Add the test cases**

Append to `scripts/tests/test-contract-scripts.sh`, in the `adopt-contract-version.sh` section
alongside the existing cases:

```bash
echo "adopt-contract-version.sh - Python"

FIX="$(make_fixture 26.9.1-SNAPSHOT)"
echo '{}' > "$FIX/contracts/arcadedb-openapi-26.10.1-SNAPSHOT.json"
echo 'syntax = "proto3";' > "$FIX/contracts/arcadedb-server-26.10.1-SNAPSHOT.proto"
"$FIX/scripts/adopt-contract-version.sh" 26.10.1-SNAPSHOT >/dev/null 2>&1; rc=$?
check "$rc" "0" "adopts a new version with a Python package present"

PYPROJECT="$FIX/python/packages/client/pyproject.toml"
if grep -q 'server-version = "26.10.1-SNAPSHOT"' "$PYPROJECT"; then
  ok "rewrites [tool.arcadedb] server-version in pyproject.toml"
else
  bad "rewrites [tool.arcadedb] server-version in pyproject.toml (got: $(grep server-version "$PYPROJECT"))"
fi

PYREADME="$FIX/python/packages/client/README.md"
case "$(cat "$PYREADME")" in
  *arcadedb-openapi-26.10.1-SNAPSHOT.json*) ok "repoints the contract filename in a Python README" ;;
  *) bad "repoints the contract filename in a Python README" ;;
esac

case "$(cat "$FIX/python/packages/client/src_index.py")" in
  *26.10.1-SNAPSHOT*) ok "repoints a prose version mention in a .py file" ;;
  *) bad "repoints a prose version mention in a .py file" ;;
esac

# The TABLE_ROW guard must cover Python files exactly as it covers TypeScript ones.
# A compatibility row records that 0.1.0 really WAS generated from 26.9.1-SNAPSHOT;
# rewriting it falsifies history rather than updating it.
if grep -q '^| 0.1.0 | 26.9.1-SNAPSHOT |$' "$PYREADME"; then
  ok "leaves the Python compatibility table row untouched"
else
  bad "leaves the Python compatibility table row untouched (the TABLE_ROW guard is not covering Python files)"
fi
rm -rf "$FIX"

# A malformed or merge-mangled pyproject must fail loudly rather than leave one of
# two keys silently stale.
FIX="$(make_fixture 26.9.1-SNAPSHOT)"
echo '{}' > "$FIX/contracts/arcadedb-openapi-26.10.1-SNAPSHOT.json"
echo 'syntax = "proto3";' > "$FIX/contracts/arcadedb-server-26.10.1-SNAPSHOT.proto"
printf '[tool.arcadedb]\nserver-version = "26.9.1-SNAPSHOT"\nserver-version = "26.9.1-SNAPSHOT"\n' \
  > "$FIX/python/packages/client/pyproject.toml"
"$FIX/scripts/adopt-contract-version.sh" 26.10.1-SNAPSHOT >/dev/null 2>&1; rc=$?
check "$rc" "1" "refuses a pyproject.toml carrying two server-version keys"
rm -rf "$FIX"
```

- [ ] **Step 5: Run the script tests**

Run: `./scripts/tests/test-contract-scripts.sh` (from the repository root)
Expected: all cases pass, including the existing TypeScript ones — Step 1 rewrote the shared
`candidates()` function, so a TypeScript regression here is the likeliest way this task goes wrong.

- [ ] **Step 6: Verify idempotency against the real repository**

```bash
./scripts/adopt-contract-version.sh 26.9.1-SNAPSHOT
git status --porcelain
```

Expected: "no references needed repointing" and a clean tree. Adopting the version already in force
must change nothing.

- [ ] **Step 7: Commit**

```bash
git add scripts
git commit -m "feat(scripts): make adopt-contract-version.sh language-aware"
```

---

### Task 14: Extend the contract watch to both languages

**Files:**
- Modify: `.github/workflows/contract-watch.yml`
- Modify: `scripts/report-contract-watch.sh`

**Interfaces:**
- Consumes: Task 13's language-aware adopt script, Task 4's Python CI commands.
- Produces: a daily job whose issue and PR describe both clients.

**Why one job, not two:** two daily workflows would each fetch, adopt, and open a PR touching
`contracts/`, conflicting by construction. One contract version is adopted repo-wide, atomically.

- [ ] **Step 1: Add Python setup and regeneration to the workflow**

In `.github/workflows/contract-watch.yml`, after the existing Node setup, add the uv install and
`uv sync --frozen` steps from `ci-python.yml`, and extend the "Regenerate" step to run
`./scripts/generate.sh` from `python/` alongside `npm run generate`.

- [ ] **Step 2: Widen the change detection**

Change the `Detect contract change` step's porcelain path list from `contracts typescript` to
`contracts typescript python`.

- [ ] **Step 3: Split the verify step per language**

Replace the single `verify` step with two `continue-on-error: true` steps, `verify-ts` (id
`verify_ts`) and `verify-py` (id `verify_py`). `verify-py` runs, from `python/`:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run python scripts/check_codegen_skips.py
uv run pytest
uv run pytest e2e
```

with `ARCADEDB_DOCKER_IMAGE` set to the snapshot image, exactly as the TypeScript half does.

Update the `Summarise the outcome` step so `quiet` requires the contract to be unchanged **and both**
verify outcomes to be `success`:

```bash
if [[ "$CHANGED" == "false" && "$VERIFY_TS" == "success" && "$VERIFY_PY" == "success" ]]; then
  echo "state=quiet" >> "$GITHUB_OUTPUT"
elif [[ "$CHANGED" == "false" ]]; then
  echo "state=behaviour-regression" >> "$GITHUB_OUTPUT"
else
  echo "state=contract-changed" >> "$GITHUB_OUTPUT"
fi
```

Raise the job's `timeout-minutes` from 30 to 45; it now starts containers for two e2e suites.

- [ ] **Step 4: Teach the report script about two clients**

In `scripts/report-contract-watch.sh`:

Replace `verify_line()` with a per-language version:

```bash
verify_line() {
  local ts="${VERIFY_TS:-}" py="${VERIFY_PY:-}"
  if [[ "$ts" == "success" && "$py" == "success" ]]; then
    echo "Both clients build and their full suites pass against \`${IMAGE:-}\`."
    return
  fi
  echo "**One or more clients FAIL against \`${IMAGE:-}\`.** See the run for which stage."
  echo
  [[ "$ts" == "success" ]] && echo "- \`@arcadedb/client\` (TypeScript): passing" || echo "- \`@arcadedb/client\` (TypeScript): **failing**"
  [[ "$py" == "success" ]] && echo "- \`arcadedb-client\` (Python): passing" || echo "- \`arcadedb-client\` (Python): **failing**"
}
```

Extend the fingerprint so a change in *either* language's verdict is a changed finding:

```bash
finding_fingerprint() {
  printf '%s\n%s\n%s\n%s\n%s\n' \
    "${STATE:-}" "${VERSION:-}" "${VERIFY_TS:-}" "${VERIFY_PY:-}" "${CHANGED_FILES:-}" \
    | shasum -a 256 | cut -c1-16
}
```

**This is the part that is easy to get wrong:** without both verdicts in the fingerprint, TypeScript
recovering while Python stays red produces an identical fingerprint, and the script silently declines
to comment on a finding that genuinely changed.

Update `main()`'s guard from `"${VERIFY:?}"` to `"${VERIFY_TS:?}" "${VERIFY_PY:?}"`, and change both
`CHANGED_FILES="$(git status --porcelain -- contracts typescript ...)"` and
`git add contracts typescript` to include `python`. In `open_refresh_pr`, change "regenerates both
clients" to "regenerates every client".

- [ ] **Step 5: Exercise the report script's pure functions offline**

```bash
cd /tmp && mkdir -p cw && cd cw
STATE=contract-changed VERSION=26.10.1-SNAPSHOT IMAGE=arcadedata/arcadedb:26.10.1-SNAPSHOT \
  VERIFY_TS=success VERIFY_PY=failure RUN_URL=http://example/run CHANGED_FILES="python/x" \
  bash -c 'source /path/to/repo/scripts/report-contract-watch.sh; build_body'
```

Expected: the body names the Python client as failing and the TypeScript client as passing. Then
rerun with `VERIFY_PY=success` and confirm `finding_fingerprint` returns a **different** value.

- [ ] **Step 6: Dry-run the workflow**

```bash
gh workflow run contract-watch.yml -f dry_run=true
```

Expected: the run completes and the step summary reports a state; `dry_run` suppresses issue and PR
creation.

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/contract-watch.yml scripts/report-contract-watch.sh
git commit -m "ci: extend the contract watch to regenerate and verify both clients"
```

---

### Task 15: Publishing, Dependabot, and the repository docs

**Files:**
- Create: `.github/workflows/publish-python.yml`, `python/CLAUDE.md`, `python/README.md`
- Modify: `.github/dependabot.yml`, `README.md`, `CLAUDE.md`

**Interfaces:**
- Consumes: everything above.
- Produces: a manual-dispatch PyPI release path and the documentation a newcomer needs.

- [ ] **Step 1: Write the publish workflow**

`.github/workflows/publish-python.yml`:

```yaml
name: Publish arcadedb-client (PyPI)

# Manual release only. Nothing in this repository publishes on push, tag, or
# schedule - a human triggers this from the Actions UI after bumping
# python/packages/client/pyproject.toml's "version". This workflow is the ONLY
# place that talks to PyPI.
on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version being published. Must equal packages/client/pyproject.toml "version" exactly - a guardrail against dispatching the wrong release, not a bump mechanism.'
        required: true
        type: string

permissions:
  contents: read
  # PyPI Trusted Publishing (OIDC) needs a token to attest with.
  #
  # This INVERTS npm's bootstrap problem, which publish.yml documents at length:
  # PyPI supports PENDING publishers, so the trusted publisher for this project can
  # be configured BEFORE the project exists on the index. The first Python publish
  # therefore needs no short-lived token and no stored secret, ever.
  #
  # The other npm caveat does carry over: whenever this file is renamed, or the
  # publisher is reconfigured, check the workflow filename entered in PyPI's
  # publisher settings against this file's actual name (currently
  # `publish-python.yml`) once, deliberately, side by side rather than from memory.
  id-token: write

jobs:
  publish:
    name: Publish to PyPI
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - name: Checkout
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
          cache-dependency-glob: python/uv.lock

      - name: Install dependencies
        working-directory: python
        run: uv sync --frozen

      - name: Verify the dispatch input matches the package version
        working-directory: python
        env:
          REQUESTED_VERSION: ${{ inputs.version }}
        run: |
          uv run python - <<'PY'
          import os, sys, tomllib, pathlib
          pkg = tomllib.loads(pathlib.Path("packages/client/pyproject.toml").read_text())
          actual = pkg["project"]["version"]
          requested = os.environ["REQUESTED_VERSION"]
          if actual != requested:
              sys.exit(
                  f'Dispatch input "{requested}" does not match packages/client/pyproject.toml '
                  f'version "{actual}". Bump the package version first, or dispatch with the correct version.'
              )
          print(f"OK: dispatch input matches pyproject.toml version {actual}")
          PY

      - name: Run the full unit test suite
        working-directory: python
        run: uv run pytest

      - name: Verify the recorded server version matches the committed contract
        working-directory: python
        # The package records the ArcadeDB release it was generated against in
        # [tool.arcadedb] server-version. That must still match the committed
        # contract's info.version at publish time - otherwise the compatibility table
        # this package ships in its README would be lying the moment it is published.
        run: |
          uv run python - <<'PY'
          import json, pathlib, sys, tomllib
          contracts = pathlib.Path("../contracts")
          candidates = sorted(contracts.glob("arcadedb-openapi-*.json"))
          if len(candidates) != 1:
              sys.exit(f"Expected exactly one contracts/arcadedb-openapi-*.json, found {len(candidates)}")
          pkg = tomllib.loads(pathlib.Path("packages/client/pyproject.toml").read_text())
          pkg_version = pkg.get("tool", {}).get("arcadedb", {}).get("server-version")
          contract_version = json.loads(candidates[0].read_text()).get("info", {}).get("version")
          if not pkg_version or not contract_version:
              sys.exit(f'Missing version field(s): server-version="{pkg_version}", info.version="{contract_version}"')
          if pkg_version != contract_version:
              sys.exit(
                  f'[tool.arcadedb] server-version ("{pkg_version}") does not match '
                  f'{candidates[0].name}\'s info.version ("{contract_version}")'
              )
          print(f"OK: server-version matches contract info.version ({pkg_version})")
          PY

      - name: Build the wheel and sdist, and verify their contents
        working-directory: python
        # Asserting the built artifacts actually contain the generated tree and the
        # typing marker turns a silent no-op build into a hard CI failure instead of
        # an empty published package - the same guard publish.yml applies to dist/.
        run: |
          uv build --package arcadedb-client --out-dir dist
          WHEEL="$(ls dist/arcadedb_client-*.whl)"
          for entry in \
            "arcadedb_client/__init__.py" \
            "arcadedb_client/py.typed" \
            "arcadedb_client/_generated/client.py" \
            "arcadedb_client/_generated/api/query/execute_query_post.py"; do
            unzip -l "$WHEEL" | grep -q "$entry" \
              || { echo "$entry is missing from $WHEEL - the published package would be broken" >&2; exit 1; }
          done
          ls dist/arcadedb_client-*.tar.gz >/dev/null

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: python/dist
          attestations: true
```

- [ ] **Step 2: Add the uv ecosystem to Dependabot**

Append to `.github/dependabot.yml`:

```yaml
  - package-ecosystem: "uv"
    directory: "/python"
    schedule:
      interval: "weekly"
    groups:
      uv-minor-and-patch:
        update-types:
          - "minor"
          - "patch"
```

- [ ] **Step 3: Write `python/CLAUDE.md`**

The sibling of `typescript/CLAUDE.md`, covering:

- **Commands** — `uv sync`, `./scripts/generate.sh`, `uv run mypy`, `uv run ruff check .`, `uv run pytest`, `uv run pytest e2e`, and how to run one test (`uv run pytest packages/client/tests/test_data.py -v`, `uv run pytest -k "rolls back"`).
- **Generation** — the generator command; that `_generated/` is never hand-edited; that the generator silently skips four endpoints and `scripts/check_codegen_skips.py` is what keeps that honest.
- **Two facades, one generated layer** — why the duplication exists and why `unasync` is a non-goal.
- **Deliberate asymmetries** — the facade raises, `.raw` does not; `help_` matches the generated model; `auth.py` is three lines where `auth.ts` is sixty, and why not to port that workaround; the lazy-import/tree-shaking construct is deliberately absent.
- **The transaction contract** — the three clauses, and that they are individually tested.
- **`QueryEnvelope` is hand-written** — the `Unset` normalisation and why the namespaces do not get the same treatment.
- **`CommandRequest.limit`** — present in the contract, deliberately not exposed, and why.

- [ ] **Step 4: Update the repository-level docs**

In the root `README.md`:

- Add `python/` to the Layout section: `arcadedb-client`, the HTTP client, with a pointer to `python/packages/client/README.md`.
- Change "`python/`, `go/`, and other language directories will appear here as siblings of `typescript/` as this repository grows; none exist yet." to name `python/` as existing and `go/` as still to come.

In the root `CLAUDE.md`:

- Change "Today the only language directory is `typescript/`" to name both, and point at `python/CLAUDE.md` beside `typescript/CLAUDE.md`.
- In the Workflows section, add `ci-python.yml` and `publish-python.yml`, and note that `contract-watch.yml` now regenerates and verifies both clients.
- Note that `adopt-contract-version.sh` is language-aware and carries an explicit language table.

Add `python/README.md` as a short pointer to the package README and `python/CLAUDE.md`.

- [ ] **Step 5: Verify the whole repository is green**

```bash
cd python && uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest && uv run pytest e2e
cd .. && ./scripts/tests/test-contract-scripts.sh
cd typescript && npm ci && npm test
```

Expected: everything passes. The TypeScript suite must be untouched by this milestone; if it is not,
Task 13's script changes broke it.

- [ ] **Step 6: Commit**

```bash
git add .github python README.md CLAUDE.md
git commit -m "ci(python): add the PyPI publish workflow, Dependabot, and the docs"
```

---

## Post-plan notes

**Not done by this plan, by design:**

- `arcadedb-client-grpc` (M3b). Section 12 of the spec records the three open questions it inherits: buf remote-versus-local plugins, whether `protoc` version-stamps its output filenames (which would mean `adopt-contract-version.sh` needs a Python retirement step), and grpcio versus betterproto.
- A README compatibility-table row for any version beyond `0.1.0` / `26.9.1-SNAPSHOT`. Those rows are a historical record tied to a package version, and adding one is a human decision — `adopt-contract-version.sh` deliberately does not.
- Adding `limit` to `command()` in either client.
