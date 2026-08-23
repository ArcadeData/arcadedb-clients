# arcadedb-clients

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![CI](https://github.com/ArcadeData/arcadedb-clients/actions/workflows/ci.yml/badge.svg)](https://github.com/ArcadeData/arcadedb-clients/actions/workflows/ci.yml)
[![Contract Watch](https://github.com/ArcadeData/arcadedb-clients/actions/workflows/contract-watch.yml/badge.svg)](https://github.com/ArcadeData/arcadedb-clients/actions/workflows/contract-watch.yml)

Language clients for [ArcadeDB](https://arcadedb.com)'s HTTP and gRPC APIs, generated from shared
OpenAPI and Protobuf contracts and kept in sync with them by CI.

The idea: one contract per API, many language clients. `contracts/` holds the OpenAPI spec and the
Protobuf `.proto` that every client in every language this repository will ever host is generated
from. A client's own package never hand-edits its generated types - the contract is the single
source of truth, and each client's build regenerates from it and fails the build (a "drift gate")
if the checked-in generated code and a fresh regeneration disagree.

## Layout

- `contracts/` - the OpenAPI and Protobuf contracts, fetched by `scripts/fetch-contract.sh` and
  committed.
- `typescript/` - two TypeScript/JavaScript clients, sharing one toolchain and one CI job:
  - `@arcadedb/client`, the HTTP client. See `typescript/packages/client/README.md` for usage.
  - `@arcadedb/client-grpc`, the gRPC client. See `typescript/packages/client-grpc/README.md` for
    usage, including why it has no browser build.
- `scripts/fetch-contract.sh` - fetches the OpenAPI contract from a released ArcadeDB version or a
  running Docker image, or copies the Protobuf contract out of a local `arcadedb` checkout, and
  writes the result into `contracts/`. See "The contracts" below.

`python/`, `go/`, and other language directories will appear here as siblings of `typescript/` as
this repository grows; none exist yet.

## The contracts

`scripts/fetch-contract.sh` has three modes:

```bash
scripts/fetch-contract.sh --release <tag>          # download + checksum-verify a GitHub release asset (OpenAPI)
scripts/fetch-contract.sh --image <image-reference> # start the image, fetch /api/v1/openapi.json (OpenAPI)
scripts/fetch-contract.sh --proto-from <checkout> [<version>]  # copy arcadedb-server.proto out of a local arcadedb checkout
```

In the `--release` and `--image` modes, the resulting OpenAPI spec is refused unless it is
structurally provably post-M0 (checked via a marker that cannot be true of any pre-M0 spec: the
`/api/v1/begin/{database}` 204 response carrying the `arcadedb-session-id` header). A version
string alone proves nothing about a spec's content, so the script does not trust one. The `.proto`
contract has no equivalent marker to check against - a running server has no endpoint that serves
it, so `--proto-from` is a straight file copy out of a local `arcadedb` checkout rather than a
download.

## Development

Each language client has its own toolchain and CI job; see that client's own README for build,
test, and release instructions. Nothing in this repository publishes a package automatically -
every release is a manual, human-triggered workflow dispatch.

## License

Apache-2.0.
