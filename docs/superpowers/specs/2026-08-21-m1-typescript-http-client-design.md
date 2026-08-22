# M1: `@arcadedb/client`, the TypeScript HTTP client

**Status:** design approved, plan pending
**Date:** 2026-08-21
**Parent:** ArcadeData/arcadedb Epic #4894, milestone M1
**Predecessor:** M0, merged as `fa599b7516` (ArcadeData/arcadedb PR #6556), which made the OpenAPI
spec a correct, self-identifying, publishable contract. Its design is at
`docs/superpowers/specs/2026-08-21-spec-driven-client-generation-4894-design.md` in that repository.

## 1. Scope

M1 ships **one package**, `@arcadedb/client`, plus the shared infrastructure the whole repository
will run on: the contract pipeline, the drift gate, CI, and the release workflow.

The parent design defined M1 as both the HTTP and gRPC packages. That was narrowed deliberately.
Everything genuinely novel here is shared infrastructure, and gRPC adds a second toolchain (`buf`,
protobuf-es, Connect) plus a second e2e harness on top of a pipeline that has not proven itself.
Publishing one package end to end answers whether the pipeline works; doing two at once means
debugging the pipeline and the gRPC stack simultaneously. `@arcadedb/client-grpc` becomes **M1b**,
against proven infrastructure.

The HTTP client is also the priority deliverable on its own merits: it is the surface with zero
current footprint, while the gRPC persona already has the hand-written Java `grpc-client`.

## 2. Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | M1 scope | `@arcadedb/client` only; gRPC deferred to M1b |
| 2 | Contract bootstrap | Generate now from a locally built post-M0 image; the scheduled refresh job takes over at 26.9.1 |
| 3 | Compatibility claim | A single pinned server image for e2e, not a matrix |
| 4 | `query`/`command` return | The full envelope, so `truncated` cannot be silently dropped |
| 5 | Repository layout | Language subdirectories; `contracts/` and `scripts/` shared at the top level |

Inherited from the parent design and not revisited here: npm workspaces over pnpm, `tsc` only with
ESM-only output and no bundler, contract and generated code both committed, publishing behind a
manual `workflow_dispatch`, independent semver plus a `CONTRACT_VERSION` constant, and npm Trusted
Publishing over OIDC.

## 3. Repository layout

```
arcadedb-clients/
├── contracts/                                   # SHARED, language-agnostic
│   └── arcadedb-openapi-26.9.1-SNAPSHOT.json
├── scripts/
│   └── fetch-contract.sh                        # SHARED
├── typescript/
│   ├── package.json                             # npm workspaces root, private
│   ├── tsconfig.base.json
│   ├── packages/
│   │   └── client/                              # @arcadedb/client
│   │       └── src/generated/schema.d.ts
│   └── e2e/
├── LICENSE
└── .github/workflows/
```

`contracts/` and `scripts/` stay at the top level while everything language-specific lives under its
own directory. That is the design premise made physical: one contract, many consumers. A Python
client later reads the same contract file that TypeScript does, and `fetch-contract.sh` serves both.

Three consequences:

- The npm workspaces root is `typescript/package.json`. Workflows use `working-directory: typescript`
  and Dependabot's npm entry points at `/typescript`.
- **CI is path-filtered per language from the start.** Retrofitting filters after several languages
  exist is how a one-line README change comes to cost a full multi-language CI run.
- The drift gate is per-language. Each language regenerates from the same shared contract, which is
  the property that makes a single contract worth having.

`python/` and `go/` are not created now. An empty directory is a promise with no code behind it, and
git does not track one anyway.

### Toolchain

- **Node floor `>=20`.** Global `fetch` landed in 18, but 20 is the oldest line still in LTS
  maintenance. Browsers, Workers, Deno and Bun are unaffected.
- **GitHub Actions pinned by commit SHA**, mirroring the `arcadedb` convention, with Dependabot on
  the npm and actions ecosystems.
- **Apache 2.0 via `LICENSE` and the `license` field, no per-file headers.** The parent repository
  puts headers on every `.java` file, but that is a Java convention rather than an npm one.

## 4. Contract and codegen

**`scripts/fetch-contract.sh` has two modes**, which is what makes the bootstrap work and keeps
working afterwards:

- `--release <tag>` downloads `arcadedb-openapi-<tag>.json` from the GitHub release and verifies it
  against the published `.sha256`.
- `--image <docker-tag>` starts that image on an ephemeral host port, waits for `/api/v1/ready`, and
  fetches the spec with authentication (the endpoint requires it:
  `GetOpenApiHandler.isRequireAuthentication()` returns true).

Both write to `contracts/` and both normalise with `jq -S`, so the committed file is byte-identical
whichever route produced it. That is what makes the eventual switch from dev-built to
release-published show a diff only where the contract genuinely changed.

**`npm run generate`** runs `openapi-typescript` over the committed contract into
`typescript/packages/client/src/generated/schema.d.ts`. No network, no Docker: it reads a file in the
repository.

**The drift gate** is `npm run generate && git diff --exit-code` on every PR. It proves the committed
types match the committed contract, offline and in seconds, and it fails loudly if generated output
is hand-edited.

**The refresh job** is separate and scheduled: fetch the newest release's contract, and if it differs,
open a PR carrying the new contract, the regenerated types and the version bump. A server release
arrives as a reviewable pull request rather than a red build. This is also the mechanism that retires
the `-SNAPSHOT` bootstrap contract at 26.9.1, so the bootstrap path is exercised rather than
special-cased.

### The pre-M0 trap

**Never generate from a server older than the M0 merge.** The 26.8.1 spec lacks the
`arcadedb-session-id` header, declares 200 where the server sends 204, and leaves PromQL results
opaque. A client generated from it is exactly the broken client M0 existed to prevent, and it would
look entirely successful. `fetch-contract.sh` must refuse a contract whose `info.version` it cannot
confirm is post-M0.

### Why e2e may nonetheless run against 26.8.1

M0 changed only spec-generator classes. No handler changed, so server behaviour is identical between
26.8.1 and the post-M0 tree: the server always answered 204 and always used the session header, and
M0 made the documentation honest. A client generated from the post-M0 contract therefore works
against a 26.8.1 container.

This is safe **for this specific transition** and must not be generalised. The same arrangement would
be dangerous the moment a contract bump reflects a real behaviour change rather than a documentation
fix.

## 5. The client API

One runtime dependency, `openapi-fetch`. Everything else is types, generated by `openapi-typescript`.

The shape follows the URL structure, because the API genuinely has two scopes: server-level
operations, and operations taking a `{database}` path parameter.

```ts
import { createClient, basicAuth } from "@arcadedb/client";

const server = createClient({ baseUrl: "https://host:2480", auth: basicAuth("root", pw) });

await server.listDatabases();
await server.exists("mydb");

const db = server.db("mydb");
const { result, truncated } = await db.query({
  language: "sql",
  command: "SELECT FROM Beer LIMIT 10",
});
```

- **Server-level:** `listDatabases`, `exists`, `serverInfo`, `health`, `ready`.
- **Database-scoped:** `query`, `command`, `transaction`, plus the `ts`, `grafana` and `promql`
  namespaces. All of these take `{database}` in their paths, so the split falls out of the API rather
  than being imposed on it.

`server.db(name)` avoids threading a database string through every call.

### The query envelope

```ts
type QueryEnvelope<T = unknown> = {
  result: T[];
  limit: number;
  returned: number;
  truncated: boolean;
};
```

`query` and `command` return the whole envelope rather than just the rows. `truncated` is the reason:
it means the serializer's cap stopped serialization with rows still pending. A facade returning only
`result` would hand back a short array indistinguishable from a complete one, which is silent data
loss dressed as a successful call. This is the same principle the parent design applies to `exists`:
report what the server said and document the ambiguity rather than invent a certainty.

The cost is one destructure at every call site, forever, on the most-used method in the package. That
is the right trade.

`T` is caller-supplied and unchecked. The server returns arbitrary record shapes and the spec models
them as free-form objects; pretending otherwise would be a lie in the type system.

### Transactions

```ts
await db.transaction(async (tx) => {
  await tx.command({ language: "sql", command: "INSERT INTO Beer SET name = 'X'" });
});
```

`tx` is the same database-scoped facade with the session id bound to every request. It commits on
return and rolls back on throw, in a `finally`. This depends entirely on the header modelling M0
shipped, and it is the single strongest justification for having a facade at all.

### Errors

Any non-2xx throws `ArcadeDBError extends Error`, carrying `status` plus the server's `error`,
`exception`, `detail` and `requestId`.

**A deliberate asymmetry:** `server.raw` is the unwrapped `openapi-fetch` client, and openapi-fetch
returns `{ data, error }` rather than throwing. So the facade throws and the escape hatch does not.
`.raw` exists so that someone who knows openapi-fetch gets exactly openapi-fetch with the generated
types; wrapping it would make it something else while still calling it raw. The README must state
this plainly, because it is two error models in one package.

## 6. Testing

**Unit tests against a mocked `fetch`** cover the hand-written layer only: that `transaction` commits
on return and rolls back on throw, that it threads the session id onto every call made through `tx`,
that it releases the session in a `finally` even when the body throws, that a non-2xx becomes an
`ArcadeDBError` carrying the server's fields, and that the auth helpers produce the right header.

**e2e via Testcontainers**, pinned to a single published image: authenticate both ways, run a query
and a command, complete a transaction round-trip and observe the writes, and confirm `exists` and
`listDatabases`.

ArcadeDB has two bearer flavours: a `POST /api/v1/login` session token prefixed `AU-`, and API tokens
prefixed `at-`. The login-minted one is trivially obtainable in a test, so e2e exercises that; the
helper is identical either way, since both are `Authorization: Bearer <token>`.

**A tree-shaking check.** A fixture entry point imports only `createClient` and `query`, is bundled
with `esbuild`, and the test asserts the output contains no PromQL or Grafana marker identifiers,
plus a generous size ceiling.

Asserting absence of markers rather than only a byte budget matters: a byte budget drifts with every
dependency bump and gets loosened until it means nothing, whereas "the PromQL module is not in this
bundle" stays true or fails honestly.

**This test must be proven failable before it is trusted.** Add a PromQL import to the fixture, watch
the marker appear and the test go red, then remove it. A tree-shaking assertion that passes because
the marker string was never right is exactly the green-but-meaningless test that let the version
defect through in M0.

## 7. CI and release

**`ci.yml`, every PR**, path-filtered to `typescript/**`, `contracts/**` and `scripts/**`: `npm ci`,
typecheck, lint, unit tests, drift gate, tree-shaking check, e2e.

**`contract-refresh.yml`, scheduled**: fetch the newest release's contract assets, verify the
`.sha256`, and open a PR when they differ.

**`publish.yml`, `workflow_dispatch` only**, with a version input, gated on the committed contract
matching what the package claims, publishing via npm Trusted Publishing over OIDC.

Two caveats, both recorded rather than discovered later:

- **The first publish may need a token.** npm's documentation does not state whether a trusted
  publisher can be configured for a package that does not yet exist, and the configuration attaches
  to a package. Plan for one bootstrap publish with a short-lived granular token, then switch to
  OIDC. If OIDC works cold, that step is skipped and nothing is lost.
- **npm does not validate the trusted-publisher configuration when it is saved.** A typo in the
  workflow filename surfaces only as a failed publish, so the filename in npm's settings and the
  actual file must be deliberately checked against each other once.

## 8. Sequencing

1. Repository scaffolding: workspaces root, tsconfig, lint, LICENSE wiring, Dependabot.
2. `scripts/fetch-contract.sh` with both modes, and the bootstrap contract committed.
3. Codegen plus the drift gate, wired into CI.
4. The client: auth helpers, errors, the server and database facades, `transaction`.
5. Unit tests, then the tree-shaking check.
6. e2e via Testcontainers.
7. `publish.yml` and the README with its compatibility table.

Steps 1 to 3 are the shared infrastructure every later language inherits, so they are worth getting
right before any client code exists. Step 4 is the only substantial hand-written surface.

## 9. Non-goals

- `@arcadedb/client-grpc`, deferred to M1b.
- Any non-TypeScript language, deferred to M3+.
- Automatic release-time publishing; M1 publishes only on manual dispatch.
- A shared `@arcadedb/client-core` package. The genuinely shared surface is small today and the auth
  mechanisms differ between transports; revisit once a second language exists.
- Wrapping `server.raw` to normalise its error model. It is the escape hatch and stays vanilla.
