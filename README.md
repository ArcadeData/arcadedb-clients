# arcadedb-clients

Language clients for [ArcadeDB](https://arcadedb.com)'s HTTP API, generated from one shared OpenAPI
contract and kept in sync with it by CI.

The idea: one contract, many language clients. `contracts/` holds the OpenAPI spec that every
client in every language this repository will ever host is generated from. A client's own package
never hand-edits its generated types - the contract is the single source of truth, and each
client's build regenerates from it and fails the build (a "drift gate") if the checked-in generated
code and a fresh regeneration disagree.

## Layout

- `contracts/` - the OpenAPI contract(s), fetched by `scripts/fetch-contract.sh` and committed.
- `typescript/` - `@arcadedb/client`, the TypeScript/JavaScript HTTP client. See
  `typescript/packages/client/README.md` for usage.
- `scripts/fetch-contract.sh` - fetches the contract from a released ArcadeDB version or a running
  Docker image, normalizes it, and writes it into `contracts/`.

`python/`, `go/`, and other language directories will appear here as siblings of `typescript/` as
this repository grows; none exist yet.

## The contract

`scripts/fetch-contract.sh` has two modes:

```bash
scripts/fetch-contract.sh --release <tag>    # download + checksum-verify a GitHub release asset
scripts/fetch-contract.sh --image <docker-tag>  # start the image, fetch /api/v1/openapi.json
```

Either way, the resulting spec is refused unless it is structurally provably post-M0 (checked via a
marker that cannot be true of any pre-M0 spec: the `/api/v1/begin/{database}` 204 response carrying
the `arcadedb-session-id` header). A version string alone proves nothing about a spec's content, so
the script does not trust one.

## Development

Each language client has its own toolchain and CI job; see that client's own README for build,
test, and release instructions. Nothing in this repository publishes a package automatically -
every release is a manual, human-triggered workflow dispatch.

## License

Apache-2.0.
