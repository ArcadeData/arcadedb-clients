# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Language clients for ArcadeDB's HTTP and gRPC APIs. One contract per API in `contracts/`, many
language clients generated from it. `typescript/` and `python/` are the language directories
today; `go/` and others will appear as their siblings.

The organising rule: **generated code is never hand-edited.** The contract is the single source of
truth, and CI's *drift gate* regenerates from the committed contract and fails if the result
differs from what is checked in. If a generated file looks wrong, fix the contract or the
generator config — editing the output only makes CI red.

See `typescript/CLAUDE.md` for the TypeScript workspace and `python/CLAUDE.md` for the Python
workspace (commands, package layout, conventions).

## The contracts

`contracts/` holds exactly one OpenAPI JSON and exactly one `.proto`, each named after the
ArcadeDB server version it came from (`arcadedb-openapi-<version>.json`,
`arcadedb-server-<version>.proto`). "Exactly one" is enforced, not conventional — two OpenAPI
files make `openapi-typescript` silently generate from whichever the glob yields first (lexical,
not version, order), and two `.proto` files make `buf generate` fail on a duplicate symbol.

```bash
scripts/fetch-contract.sh --release <tag>            # download + checksum-verify a GitHub release asset (OpenAPI)
scripts/fetch-contract.sh --image <image-reference>  # start the image, fetch /api/v1/openapi.json (OpenAPI)
scripts/fetch-contract.sh --proto-from <checkout> [<version>]  # copy arcadedb-server.proto from a local arcadedb checkout

scripts/adopt-contract-version.sh <version>          # retire the old version, adopt the new one, repo-wide
scripts/resolve-openapi-contract.sh                  # print the single OpenAPI contract path, or fail
scripts/tests/test-contract-scripts.sh               # tests for the two scripts above (runs in CI)
```

`fetch-contract.sh` writes the new contract **beside** the old one rather than in place, so a
version bump is a two-step operation: fetch both contracts, then run
`adopt-contract-version.sh <version>`, which deletes the retired contract and generated module,
rewrites the version-stamped imports, and updates each package's `arcadedb.serverVersion`. It
deliberately does not touch the compatibility tables in the READMEs — those rows are a historical
record tied to a package version, and adding one is a human decision.

`adopt-contract-version.sh` is language-aware: which files it rewrites is driven by an explicit
`LANGUAGES` table (file suffixes and directories to skip, per language) rather than by crawling
every top-level directory. Adding a language client to this repository is a deliberate one-line
addition to that table, not something the script infers by finding a new sibling of `contracts/`.

In `--release` / `--image` mode the fetched OpenAPI spec is rejected unless it is structurally
post-M0 (the `/api/v1/begin/{database}` 204 response carrying the `arcadedb-session-id` header).
A version string alone is not accepted as proof of a spec's content.

`buf.yaml` lives at the repository root, not under `typescript/`, because the gRPC module
describes the contract itself and a future Python or Go client reads the same module.

## Workflows

- `ci.yml` — lint, typecheck, unit tests, the drift gate, and the "exactly one .proto" check on
  Node 20; then a separate e2e job on Node 24 (testcontainers@12 needs Node >= 22.22). Its `paths`
  filters include root `buf.yaml` and `.gitignore` on purpose: both can change generated output or
  silence the drift gate while leaving `typescript/` untouched.
- `ci-python.yml` — the same shape for the Python client: lint, typecheck, and a three-part drift
  gate (regenerate and diff, catch untracked new generated files, and verify the generator skipped
  exactly the allowlisted endpoints via `scripts/check_codegen_skips.py`) on the declared floor
  Python, then unit tests; a separate e2e job runs against a real container on a newer Python.
- `contract-watch.yml` — daily, refreshes contracts from the SNAPSHOT server built off arcadedb's
  `main`. A changed contract gets an issue plus an adopt-and-regenerate PR; an unchanged contract
  with a red suite gets an issue only (it is a server regression no PR here can fix). Both are
  filed idempotently against one tracking issue and one branch. It now regenerates and verifies
  **both** clients, not just the TypeScript one.
- `publish.yml` — the only thing that talks to npm, and it is **manual workflow_dispatch only**.
  Nothing publishes on push, tag, or schedule. It re-verifies that the dispatch input, the
  package version, and the contract's `info.version` all agree before publishing. It publishes
  **one package per dispatch**, chosen by a `package` input (`driver` or `driver-grpc`), and is
  parameterised rather than duplicated into a sibling workflow for a specific reason: npm keys a
  trusted publisher on the workflow **filename**, so both packages naming this one file means one
  thing to configure and cross-check instead of two. Each package still needs its *own* trusted
  publisher, and its own bootstrap token for its first publish — npm has no equivalent of PyPI's
  pending publishers, so a package must exist before it can be trusted. Verify a publisher by
  reading back what npm stored (`npm trust list <package>`), never by eye against the web UI; npm
  validates that configuration at neither save nor dispatch time. The dist assertions differ per
  package — `driver-grpc`'s generated module carries the contract version in its filename, so the
  expected name is derived from `arcadedb.serverVersion` rather than hardcoded, and the step also
  asserts that exactly one such module exists (`tsc --build` never removes output whose source is
  gone, and `files: ["dist"]` would ship a retired one from a tree built across two contract
  versions).
- `publish-python.yml` — the npm workflow's sibling, and the only thing that talks to PyPI; also
  **manual workflow_dispatch only**, with the same dispatch-input/version/contract re-verification.
  Its bootstrap story inverts npm's: PyPI supports pending publishers, so the trusted publisher for
  `arcadedb-driver` can be configured before the package exists on the index, and the first publish
  needs no stored secret at all. See the workflow file's comments for the caveat that does carry
  over from npm (check the workflow filename in PyPI's publisher settings against this file's
  actual name whenever either changes).

## Design docs

`docs/superpowers/specs/` holds the design for each milestone and `docs/superpowers/plans/` the
implementation plan. They record why a client is shaped the way it is; read the relevant one
before reworking a client's public surface.

## Prose conventions

Both package READMEs and the code comments document failure modes and deliberate asymmetries at
length (why `truncated` matters, why `exists` cannot prove absence, why the gRPC client throws
`ConnectError` and not `ArcadeDBError`, why `bulkInsert` cannot join a `transaction()`). When you
change behaviour in one of those areas, update the prose with it — those passages are load-bearing
documentation, not decoration.
