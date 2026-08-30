# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Language clients for ArcadeDB's HTTP and gRPC APIs. One contract per API in `contracts/`, many
language clients generated from it. Today the only language directory is `typescript/`;
`python/`, `go/` and others will appear as its siblings.

The organising rule: **generated code is never hand-edited.** The contract is the single source of
truth, and CI's *drift gate* regenerates from the committed contract and fails if the result
differs from what is checked in. If a generated file looks wrong, fix the contract or the
generator config — editing the output only makes CI red.

See `typescript/CLAUDE.md` for the TypeScript workspace (commands, package layout, conventions).

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
- `contract-watch.yml` — daily, refreshes contracts from the SNAPSHOT server built off arcadedb's
  `main`. A changed contract gets an issue plus an adopt-and-regenerate PR; an unchanged contract
  with a red suite gets an issue only (it is a server regression no PR here can fix). Both are
  filed idempotently against one tracking issue and one branch.
- `publish.yml` — the only thing that talks to npm, and it is **manual workflow_dispatch only**.
  Nothing publishes on push, tag, or schedule. It re-verifies that the dispatch input, the
  package version, and the contract's `info.version` all agree before publishing.

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
