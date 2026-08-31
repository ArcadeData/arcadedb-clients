# M3: `arcadedb-client`, the Python HTTP client

**Status:** design approved, plan pending
**Date:** 2026-08-30
**Parent:** ArcadeData/arcadedb Epic #4894, milestone M3
**Predecessors:** M1 (`@arcadedb/client`), M1b (`@arcadedb/client-grpc`), and M2 (the smoke job in
`ArcadeData/arcadedb`). M1's spec deferred "any non-TypeScript language" to M3+; this is the first
of those.

## 1. Scope

M3 ships `arcadedb-client`: a Python HTTP client generated from the same committed OpenAPI contract
`@arcadedb/client` is generated from, with a hand-written facade over the generated layer and both a
synchronous and an asynchronous surface.

It also does the one-time work of teaching this repository that it hosts more than one language:
`scripts/adopt-contract-version.sh` stops assuming `typescript/`, `contract-watch.yml` starts
regenerating and verifying both clients, and CI and publishing split per language.

`arcadedb-client-grpc` is **M3b**, for the same reason `@arcadedb/client-grpc` was M1b: proving a new
toolchain and a new transport at once means debugging both at once. The uv workspace glob admits
`packages/client-grpc/` from day one and nothing more.

## 2. Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | M3 scope | HTTP only; gRPC deferred to M3b |
| 2 | Codegen | `openapi-python-client --meta none`: generated operations **and** models, over httpx |
| 3 | Concurrency | Both surfaces: `ArcadeDBServer` (sync) and `AsyncArcadeDBServer` (async) |
| 4 | Toolchain | uv workspace, hatchling, ruff, mypy; one committed `python/uv.lock` |
| 5 | Distribution names | `arcadedb-client` and `arcadedb-client-grpc`; imports `arcadedb_client`, `arcadedb_client_grpc` |
| 6 | Endpoints the generator skips | Hand-write `ts.write` only; guard the skip set with an allowlist check |
| 7 | Python floor | 3.10 |
| 8 | Repo machinery | Language-aware scripts, one contract-watch job, split CI and publish workflows |

Inherited from M1 and not revisited: generated code is committed and drift-gated, publishing is a
manual `workflow_dispatch`, each package carries independent semver plus a recorded contract version,
and the README compatibility tables are a human decision.

## 3. Why a client generator, not a model generator

TypeScript gets path-level typing for free. `openapi-typescript` emits both `paths` and `components`,
and `openapi-fetch` is keyed on `paths`, so a route that disappears from the contract fails
`tsc`. The drift gate therefore covers routes and schemas together, and `facade/*.ts` never writes a
URL by hand.

Python has no `openapi-fetch` equivalent. A model-only generator (`datamodel-code-generator` into
Pydantic models or TypedDicts) produces a smaller, more idiomatic-looking tree, but every URL then
lives hand-written in the facade, outside the gate: a path the server drops stays hardcoded and green
until the e2e suite happens to touch it. Keeping routes under the contract is the property this whole
repository is built around, so the generator that emits operations wins over the one that emits only
shapes, and the attrs runtime dependency and the large `_generated/` tree are the price.

### What the generator does not cover

Against the committed 26.9.1-SNAPSHOT contract, `openapi-python-client` generates **60 of the
contract's 64 operations**. It skips four, warning to stderr and **exiting 0**:

| Skipped operation | Media type | Wrapped in TypeScript? |
|---|---|---|
| `POST /api/v1/ts/{database}/write` | `text/plain` (Line Protocol) | yes — `db.ts.write()` |
| `POST /api/v1/batch/{database}` | `jsonl` / `ndjson` / `csv` | no |
| `POST /api/v1/ts/{database}/prom/read` | `application/x-protobuf` | no |
| `POST /api/v1/ts/{database}/prom/write` | `application/x-protobuf` | no |

`GET /api/v1/ha/snapshot/{database}` is generated, but its `application/zip` 200 response is dropped
from the return type. It is not wrapped by the facade in either language, so this costs nothing today.

The generator is JSON-schema-shaped, and every one of these is a non-JSON body. This is a property of
the tool, not a bug to report.

**`db.ts.write()` is hand-written** so the Python time-series namespace can ingest as well as query;
a namespace that queried but could not write would be an odd shape to ship and a worse one to
explain. It posts a `text/plain` body through `client.get_httpx_client()` — the same pooled httpx
client every generated operation uses — which is the direct analogue of what `facade/timeseries.ts`
does with `bodySerializer: (body) => body`. The other three stay unwrapped exactly as in TypeScript.

**`python/scripts/check_codegen_skips.py`** is the guard that makes this safe over time. It runs the
generator, parses the skip warnings out of stderr, and asserts the set equals a committed allowlist of
those four operations. Without it, a future contract adding a `text/csv` endpoint would have that
endpoint silently dropped, with a zero exit code and a green build — a failure mode indistinguishable
from success, which is precisely the class of failure the drift gate exists to catch.

## 4. Repository layout

```
python/
├── pyproject.toml            # [tool.uv.workspace] members = ["packages/*"]; dev deps; ruff + mypy config
├── uv.lock                   # committed
├── CLAUDE.md  README.md
├── scripts/
│   └── check_codegen_skips.py
├── e2e/
│   ├── conftest.py           # container fixture, image pin, ARCADEDB_DOCKER_IMAGE override
│   └── test_data_plane.py
└── packages/
    └── client/               # arcadedb-client
        ├── pyproject.toml    # [tool.arcadedb] server-version = "26.9.1-SNAPSHOT"
        ├── README.md  LICENSE
        ├── src/arcadedb_client/
        │   ├── __init__.py   # the entire public surface
        │   ├── py.typed
        │   ├── auth.py  errors.py
        │   ├── _internal/unwrap.py
        │   ├── facade/{data,timeseries,dashboards}.py
        │   └── _generated/   # openapi-python-client output; NEVER hand-edited
        └── tests/
```

`packages/client-grpc/` is created by M3b.

### Toolchain

uv is the analogue of npm workspaces: `python/uv.lock` is one committed lockfile for the whole
directory, Dependabot has a native `uv` ecosystem so the existing weekly grouped-update pattern
carries over unchanged, and `uv sync --frozen` in CI is the analogue of `npm ci`.

- **hatchling** — build backend.
- **ruff** — lint and format, eslint's role. Excludes `_generated/`, as `eslint.config.js` excludes
  `src/generated/` and `src/gen/`.
- **mypy --strict** — `tsc`'s role, over `src/arcadedb_client` excluding `_generated/`. Scoping strict
  typing to hand-written source mirrors M1's decision to scope `recommendedTypeChecked` to
  `packages/*/src/**`: generated output is contract-shaped, not style-shaped, and holding it to a
  hand-written bar produces noise, not safety.
- **Python 3.10 floor.** 3.9 reached end of life in October 2025. Unit, lint, typecheck and the drift
  gate run on 3.10; e2e runs on 3.14. That is the same floor-and-current split `ci.yml` already uses
  for Node 20 and Node 24, and it gives two-version coverage without a matrix.
- The package ships `py.typed`.

## 5. Contract and codegen

One command:

```
openapi-python-client generate \
  --path "$(../scripts/resolve-openapi-contract.sh)" \
  --meta none --overwrite \
  --output-path packages/client/src/arcadedb_client/_generated
```

`--meta none` emits the package body only — `api/`, `models/`, `client.py`, `errors.py`, `types.py` —
with no project scaffolding of its own. Generated modules import each other **relatively**
(`from ...client import Client`), so the tree nests under `src/arcadedb_client/_generated/` untouched.

The generator version is pinned in `uv.lock`, which is what makes the output reproducible. Two
consecutive runs against the committed contract were verified byte-identical.

### The drift gate

`ci-python.yml` regenerates and then applies three checks. The first two mirror `ci.yml`:

1. `git diff --exit-code -- packages/client/src/arcadedb_client/_generated` — a **modified**
   generated file.
2. `git status --porcelain` over the same path — an **added or renamed** one, which `git diff` is
   blind to.
3. `check_codegen_skips.py` — the skip allowlist from section 3. This has no TypeScript counterpart,
   because `openapi-typescript` has no equivalent silent-skip behaviour.

The generator writes a `.ruff_cache/` into its output directory; that goes in `.gitignore`. Because an
ignore rule over a generated path would permanently and invisibly silence check 2, root `.gitignore`
stays in `ci-python.yml`'s `paths` filter for exactly the reason `ci.yml` already lists it.

### Version stamping and `adopt-contract-version.sh`

Each package records its contract version in `pyproject.toml`:

```toml
[tool.arcadedb]
server-version = "26.9.1-SNAPSHOT"
```

`scripts/adopt-contract-version.sh` becomes language-aware. Today it hardcodes `TS_DIR` and walks
`typescript/` for `.ts` and `.md` files; it must instead iterate an **explicit table** of language
directories, each with its own file extensions and skip set — for Python, `.py`, `.md` and `.toml`,
skipping `_generated`, `__pycache__`, `.venv`, `dist` and `build` alongside the existing entries.

An explicit table rather than filesystem discovery, and this does not contradict the script's
existing "found by search rather than hardcoded" comment: that rule is about *files within* a
language directory, where a new source file must not escape repointing by not being on a list. Which
top-level directories are language clients is a different question, and a script that silently began
rewriting any new sibling of `contracts/` would be worse, not better. Adding a language stays a
deliberate one-line change.

The `server-version` rewrite is a targeted line
substitution — Python has `tomllib` for reading and no stdlib writer — and asserts it matched exactly
once, so a malformed or duplicated key fails loudly rather than silently leaving a stale version.

Two existing behaviours are preserved verbatim over Python files: the `TABLE_ROW` guard, so README
compatibility rows stay the historical record they are, and the "version segment must start with a
digit" patterns, so `<version>` placeholders in prose survive a bump.

M3 adds **no** retirement step for the Python generated tree. Unlike the gRPC `_pb.ts`, the
openapi-python-client output is not version-stamped in its filenames, so a bump modifies files in
place — the `openapi-typescript` situation, not the `buf` one. M3b will need one; see section 12.

`scripts/tests/test-contract-scripts.sh` gains cases for the Python half of both scripts.

## 6. The client API

```python
from arcadedb_client import ArcadeDBServer, AsyncArcadeDBServer, basic_auth

with ArcadeDBServer(base_url="http://localhost:2480", auth=basic_auth("root", "pw")) as srv:
    db = srv.db("mydb")
    env = db.query(language="sql", command="SELECT FROM Person WHERE age > :min", params={"min": 18})
    if env.truncated:
        ...
    for row in env.result:            # list[dict[str, Any]]
        ...

    with db.transaction() as tx:      # commits on clean exit, rolls back on exception
        tx.command(language="sql", command="INSERT INTO Person SET name = 'Ada'")
```

`AsyncArcadeDBServer` is the same surface with `async with` and `await`.

**Both are context managers**, and this has no TypeScript counterpart: an httpx client owns a
connection pool that must be released, where `fetch` owns nothing. `close()` and `aclose()` exist for
callers who cannot use a `with` block.

**Two facades over one generated layer.** Every generated operation emits `sync`, `sync_detailed`,
`asyncio` and `asyncio_detailed`, so the sync and async facades differ only in which pair they call.
The duplication is real and accepted; `unasync`-style single-source generation is a non-goal.

**`.raw` is the generated `Client`.** Its `raise_on_unexpected_status` defaults to `False`, so the
non-throwing escape hatch `server.raw` provides in TypeScript comes for free, with the same
asymmetry preserved: `srv.raw` never raises, the facade always does.

### The query envelope

`db.query()` and `db.command()` return a hand-written frozen dataclass, **not** the generated
`QueryResponse`:

```python
@dataclass(frozen=True, slots=True)
class QueryEnvelope:
    result: list[dict[str, Any]]
    limit: int
    returned: int
    truncated: bool
```

The generated model types every field as `T | Unset`, because `QueryResponse` has no `required` list
in the contract. `facade/data.ts`'s `toEnvelope` deliberately normalises all four —
`result ?? []`, `limit ?? -1`, `returned ?? 0`, `truncated ?? false` — and the Python facade defaults
them identically. Its doc comment's reasoning carries over verbatim and must be reproduced: those
defaults are the most reassuring possible reading of "the server did not say", asserting a
completeness the server never claimed, and today's server always sends all four, which is a property
of the current implementation rather than a guarantee the type enforces. Returning the generated
model instead would hand every caller an `Unset` check on `truncated`, which is precisely the silent
partial-result hazard the whole-envelope return exists to prevent.

The dataclass also flattens `QueryResponseResultItem`'s `additional_properties` wrapper into the
plain dicts a Python caller expects. In the other direction, `params` is a `dict[str, Any]` in the
public signature and is converted with `QueryRequestParams.from_dict()` when building the request
body — the analogue of the one narrow cast `buildCommandBody` makes, and for the same reason: the
generated params type is an "untyped object" artifact, not a real restriction. `command` and
`language` are passed through untouched so that a contract change to either still fails the
typecheck here rather than only on the wire.

The three dashboard/ingest namespaces do **not** get this treatment: `db.ts`, `db.grafana` and
`db.promql` pass the generated models through unaltered, exactly as `facade/timeseries.ts` and
`facade/dashboards.ts` re-export `components["schemas"][...]` unaltered. `Unset` is visible there in
the same way `?: T | undefined` is visible in TypeScript. `db.ts.query()` returns the generated
`TimeSeriesRawResponse | TimeSeriesAggregatedResponse` union, narrowed with `isinstance` where
TypeScript narrows with `in`.

**The lazy-`import()` trick is not carried over.** In TypeScript the three namespaces load their
implementation dynamically, and `test/treeshake.test.ts` enforces it; that is a bundler contract with
no Python meaning. The namespaces are plain cached properties over module-level imports. This is
recorded explicitly because it is exactly the kind of construct a faithful port reproduces by reflex.

### Transactions

`db.transaction()` returns a context manager rather than taking a callback. The handle is a **second**
database object carrying the session id, so calls made through the outer `db` are not part of the
transaction — the same subtlety `ArcadeDBDatabase`'s doc comment spells out, and it must be documented
identically here.

Session threading needs no header plumbing: because the contract declares the header, the generator
emits `arcadedb_session_id: str | Unset = UNSET` as a keyword argument on every data-plane and
transaction operation. `begin_transaction`, however, answers **204 with the id in the
`arcadedb-session-id` response header**, so `begin` must call `sync_detailed` / `asyncio_detailed` and
read `response.headers`. This is the exact contract shape M0 existed to make honest, and the marker
`fetch-contract.sh` refuses a spec for lacking.

The error contract is transliterated from `transaction`'s doc comment in `index.ts`, and each clause
gets its own test:

- The body's exception always wins.
- If the body raises and the rollback then fails, the rollback error is attached to the body's
  exception as `__cause__` **only when `__cause__` is unset** — a caller-set causal chain is never
  overwritten — and the attach is swallowed if it fails.
- If the commit fails, a best-effort rollback is issued to release the session server-side (its own
  failure swallowed) before the commit error is raised. Without it the session leaks until
  `arcadedb.server.httpTxExpireTimeout` reaps it.

### Auth

`basic_auth(user, password)` and `bearer_auth(token)` return `dict[str, str]` headers, passed to the
server constructor. The generated `Client` takes `headers` directly, so `AuthenticatedClient` — whose
token/prefix model fits bearer but not basic — is not used; one uniform mechanism serves both.

`auth.ts` is sixty lines of `TextEncoder`, chunking and commentary because `btoa` mangles non-Latin-1
credentials and a spread call blows the stack on a large one. Python's equivalent is
`base64.b64encode(f"{user}:{password}".encode())` and has neither hazard. The asymmetry is noted in
`auth.py` so nobody ports a workaround for a problem this language does not have.

## 7. Errors

`ArcadeDBError(Exception)` carries `status`, `error`, `exception`, `detail`, `request_id`, `help_` and
`exception_args` — a transliteration of `errors.ts`. The field is `help_`, not `help`, because that is
what the generated `ErrorResponse` model calls it, and two spellings of one field inside a package
whose `.raw` surface exposes both models is worse than one slightly awkward name.

`_internal/unwrap.py` holds one function serving **both** facades, since `sync_detailed` and
`asyncio_detailed` return the same `Response[T]`:

```python
def unwrap(response: Response[T]) -> T: ...   # returns .parsed, or raises ArcadeDBError
```

It lives in `_internal/` for the same import-cycle reason it does in TypeScript: `__init__.py` builds
the server and database classes out of the `facade/` functions, and `facade/` needs `unwrap` too.

`ErrorResponse` carries no request id, so `request_id` is read from the `X-Request-Id` response
header — which the server sets on every response, generating one when the client sent none — with a
defensive JSON re-read of `response.content` as a fallback. Error parsing never itself raises: a body
that is absent, unparsable, or missing fields yields an error carrying nothing beyond the status. That
is `parseBody`'s contract and it is load-bearing, since this code runs on the failure path.

## 8. Testing

**Unit** — pytest, `respx` for httpx mocking, `pytest-asyncio` in strict mode for the async facade.
Offline, no Docker, mirroring `npm test`. Suites per facade area (data, timeseries, dashboards), plus
errors, auth, and the transaction contract with one test per clause in section 6.

**Public surface** — a test asserting `__all__` matches the documented surface exactly and that
`_generated` is not re-exported. This is the honest Python replacement for `test/treeshake.test.ts`:
the same job of guarding an API-shape promise that is easy to break invisibly, by the mechanism that
actually applies to this language.

**e2e** — `testcontainers`, pinned `arcadedata/arcadedb:26.8.1` with the `ARCADEDB_DOCKER_IMAGE`
override, the database created through `POST /api/v1/server` because no dedicated create-database
endpoint exists. Both facades run against the container. The image-pin comment from
`e2e/data-plane.test.ts` is carried over in full — including its "DO NOT GENERALISE THIS" warning —
because the reasoning is identical and equally non-obvious: it holds only because the 26.9.1-SNAPSHOT
contract bump was a documentation fix, and must move the moment a bump reflects a real wire change.

One implementation note: testcontainers-python's `wait_for_logs` matches log output, not HTTP status,
so readiness is a small helper polling `/api/v1/ready` for 204 rather than a built-in wait strategy.

## 9. CI and release

**`ci-python.yml`** (new). Paths: `python/**`, `contracts/**`, `scripts/**`, `.gitignore`, and itself.
Deliberately **not** `buf.yaml` — M3b adds that when the gRPC package starts reading the module.

- `build` on Python 3.10: `uv sync --frozen` → `ruff check` + `ruff format --check` → `mypy` →
  regenerate + the three-part drift gate → `pytest` unit.
- `e2e` on Python 3.14, `needs: build`, `timeout-minutes: 15`.

The contract-script tests stay in `ci.yml` alone rather than being duplicated. `scripts/**` is in both
workflows' path filters, and they are one repo-level gate, not a per-language one.

**`contract-watch.yml`** stays a single job. Duplicating it per language is not an option: two daily
jobs would each fetch, adopt and open a PR touching `contracts/`, conflicting by construction. One
contract version is adopted repo-wide, atomically, or the invariant this repository rests on stops
holding. Changes:

- uv and Python setup beside the existing Node setup.
- The regenerate step runs both generators.
- `git status --porcelain -- contracts typescript` gains `python`.
- The single `verify` step splits into `verify-ts` and `verify-py`, each `continue-on-error`, reduced
  by the existing outcome step: `quiet` only when the contract is unchanged **and** both are green.
- `timeout-minutes` rises from 30, since the job now starts containers for two suites.

`report-contract-watch.sh` changes with it. `VERIFY` becomes `VERIFY_TS` and `VERIFY_PY` so the issue
body names which client broke, and **both must feed `finding_fingerprint`** — otherwise TypeScript
recovering while Python stays red yields an identical fingerprint and the script stays silent about a
finding that changed, which is the exact failure mode the fingerprint's own comment warns about.
`CHANGED_FILES` and the `git add` in `open_refresh_pr` both gain `python`. One-time cost: the first
run after this change re-fingerprints and posts a single "the finding changed" comment.

**`publish-python.yml`** (new, manual `workflow_dispatch` only, like npm). It verifies the dispatch
input against `packages/client/pyproject.toml`'s version, runs the unit suite, verifies
`[tool.arcadedb] server-version` equals the committed contract's `info.version` via `tomllib`, runs
`uv build`, asserts the built wheel actually contains `_generated/` and `py.typed` — the analogue of
`publish.yml`'s dist check, which exists so a silent no-op build fails CI instead of publishing an
empty package — and uploads with `pypa/gh-action-pypi-publish` under `id-token: write`. PyPI Trusted
Publishing, no stored token.

One asymmetry is worth recording in that workflow's comments because it **inverts** npm's: PyPI
supports pending publishers, so a trusted publisher can be configured before the project exists. The
first Python publish therefore needs no bootstrap token, where `publish.yml` explains at length why
the first npm publish may. The second npm caveat does carry over: verify the workflow filename entered
in the publisher configuration against this file's actual name, deliberately, whenever either changes.

**`dependabot.yml`** gains a `uv` ecosystem entry on `/python`, weekly, with the same minor-and-patch
grouping as the npm entry.

Root `README.md` and `CLAUDE.md` are updated — `python/` stops being a directory that "will appear
here" — and `python/CLAUDE.md` is written as the sibling of `typescript/CLAUDE.md`.

## 10. Sequencing

1. `python/` scaffolding: uv workspace, `pyproject.toml` files, ruff and mypy config, `uv.lock`.
2. Codegen wired up; `_generated/` committed; `check_codegen_skips.py` with its allowlist.
3. `ci-python.yml` with the three-part drift gate — the gate exists before there is a client to drift.
4. `errors.py`, `_internal/unwrap.py`, `auth.py`, and the sync facade with its tests.
5. The async facade with its tests.
6. `ts.write` hand-written; the `ts` / `grafana` / `promql` namespaces.
7. The e2e suite and its CI job.
8. `adopt-contract-version.sh` and `test-contract-scripts.sh` made language-aware.
9. `contract-watch.yml` and `report-contract-watch.sh` extended to both languages.
10. `publish-python.yml`, `dependabot.yml`, and the README/CLAUDE.md updates.

Steps 8 and 9 come late deliberately: they are the only steps that can break the working TypeScript
pipeline, and they are easier to review once the Python side they must serve actually exists.

## 11. Non-goals

- **The gRPC client** — M3b.
- **`batch`, `prom/read`, `prom/write`** — unwrapped, as in TypeScript. The allowlist guard keeps them
  visible rather than forgotten.
- **`unasync` or any single-source sync/async generation** — two hand-written facades over one
  generated layer.
- **Pydantic** — attrs arrives as the generator's runtime, not as a modelling choice. No second
  validation library.
- **A CLI, an ORM, connection pooling beyond httpx's own, or a retry/backoff policy.**
- **A Python version matrix** beyond floor-and-current, until a version-specific bug appears.
- **Automating the README compatibility tables** — the same human decision it is today.

## 12. Open questions for M3b

Recorded here so they are not rediscovered:

- **Protobuf codegen mechanism.** `buf.yaml` is already at the repository root, language-agnostic by
  design, so the module is shared. What is undecided is the plugin: buf **remote** plugins
  (`buf.build/protocolbuffers/python`, `buf.build/grpc/python`) need network at generate time, which
  the drift gate runs on every PR; **local** plugins mean `grpcio-tools` in the dev dependencies and a
  `protoc-gen-*` on PATH. The TypeScript side sidesteps this because `protoc-gen-es` installs from npm
  like any other dependency.
- **Version-stamped generated filenames.** `protoc` derives the output name from the `.proto`
  filename, so `arcadedb-server-26.9.1-SNAPSHOT.proto` yields something like
  `arcadedb_server_26_9_1_SNAPSHOT_pb2.py` — dots and dashes folded to underscores. If so, M3b
  inherits the `_pb.ts` situation and `adopt-contract-version.sh` needs a retirement step and an
  import-repointing pattern for Python too, which M3 deliberately does not add.
- **grpcio versus betterproto.** The official `grpcio` stubs are stable but not idiomatic; betterproto
  produces dataclasses and native async closer to protobuf-es's ergonomics, and is still pre-1.0.
