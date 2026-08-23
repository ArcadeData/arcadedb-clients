# M1b: `@arcadedb/client-grpc`, the TypeScript gRPC client

**Status:** design approved, plan pending
**Date:** 2026-08-22
**Parent:** ArcadeData/arcadedb Epic #4894, milestone M1b
**Predecessors:** M1 (`@arcadedb/client`, merged as `54b84091e1`) and M2 (the smoke job, merged as
`b6cfc6e0e1` plus `cd29d8a308` and `e26375d582` in `ArcadeData/arcadedb`).

## 1. Scope

M1b ships `@arcadedb/client-grpc`: a thin Connect-ES client over ArcadeDB's gRPC proto, covering the
data plane only.

M1 deliberately shipped the HTTP client alone so the shared infrastructure - contract pipeline, drift
gate, CI, release - could be proven by one package before a second toolchain arrived. That
infrastructure now exists and has been exercised end to end, including a full contract refresh. M1b
adds `buf`, protobuf-es and Connect on top of it.

## 2. Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Facade width | Streaming and transactions only; unary calls go through the generated clients |
| 2 | Admin service | Excluded from the hand-written surface; reachable via the generated stub |
| 3 | Streaming wrappers | `StreamQuery` and `InsertStream` only |
| 4 | Code sharing with `@arcadedb/client` | None; no `client-core` package |

Inherited from M1 and not revisited: Node/Bun/Deno targets with no browser support, generated code
committed and drift-gated, publishing behind a manual `workflow_dispatch`, independent semver with a
recorded contract version.

## 3. Why the facade is this narrow

The proto declares 23 RPCs across two services: 14 on `ArcadeDbService` and 9 on
`ArcadeDbAdminService`. The generated Connect clients already handle a unary call perfectly well, so
the hand-written layer covers only what they handle badly.

**Transactions are the reason this is not a zero-facade package.** `BeginTransaction` returns a
`transaction_id` that must be threaded into the `TransactionContext` of every subsequent request and
ended on both the success and failure paths. That is the same footgun the HTTP facade exists to
remove, and this codebase's history says it bites hard here: the 2026-07 gRPC audit filed
transaction hijack, silent data loss and leaked transactions as #5040 through #5042, all since fixed.
A client that made transactions easy to get wrong would reintroduce that class by ergonomics.

**The admin service is excluded** for three reasons. `@arcadedb/client` already covers discovery and
lifecycle over HTTP, so an ergonomic gRPC admin path duplicates a working capability. Its
authentication is a genuinely different mechanism (below). And its destructive RPCs are exactly where
this surface has been dangerous: the audit's first finding was that admin RPCs authenticated but
never authorized, so any user could drop any database (#5039). Nothing is blocked - `buf` still
generates the admin client and a caller can use it directly. What is withheld is the implication that
we designed and tested a path for `DeleteUser`.

**`InsertBidirectional` and `GraphBatchLoad` are left to the generated clients.** A bidirectional
stream has no natural async-iterable shape, since the caller produces and consumes at once, and
flattening it would hide backpressure the caller needs. `GraphBatchLoad` is the same
client-streaming shape as `InsertStream`, so adding it later is mechanical if demand appears.
`BulkInsert` is unary and needs nothing.

## 4. Two server facts the client must accommodate

Neither is a design choice. Both were established by reading the server, and both are easy to get
wrong from the proto alone.

**The two services authenticate differently.** `GrpcAuthInterceptor:87` branches on the method name:
`ArcadeDbAdminService` authenticates from a `DatabaseCredentials credentials` field **in the request
message**, while the data plane authenticates from **metadata** (`authorization: Bearer`, or
`x-arcade-user` and `x-arcade-password`). A single interceptor cannot serve both. This reinforces
decision 2: supporting admin properly would mean two auth mechanisms in one package.

**`TransactionContext` supports two transaction models.** Besides `transaction_id`, it carries
`begin`, `commit` and `rollback` flags, so a single request can open and commit a transaction inline.
The facade wraps only the explicit model. The inline flags remain reachable by setting the field
directly; wrapping both would offer two ways to do one thing with different failure modes, and the
explicit one is what needs the safety.

## 5. Package and toolchain

```
buf.yaml                               # repo root: the proto module, shared
contracts/
├── arcadedb-openapi-<ver>.json
└── arcadedb-server-<ver>.proto        # added by M1b
typescript/
├── buf.gen.yaml                       # TypeScript codegen config
└── packages/
    ├── client/                        # @arcadedb/client (HTTP)
    └── client-grpc/                   # @arcadedb/client-grpc
        └── src/gen/                   # committed, from buf generate
```

`buf.yaml` sits at the repository root beside `contracts/` because the proto module is
language-agnostic; `buf.gen.yaml` is TypeScript's. A future Python or Go gRPC client adds its own
generator config and reads the same module, which is the layout's whole point.

Runtime dependencies: `@bufbuild/protobuf` 2.14.0 (Apache-2.0 AND BSD-3-Clause), `@connectrpc/connect`
and `@connectrpc/connect-node` 2.1.2 (Apache-2.0). Dev-only: `@bufbuild/buf` 1.72.0 and
`@bufbuild/protoc-gen-es` 2.14.0 (both Apache-2.0). Every one is on the project's allow-list.

**Node, Bun and Deno; not browsers.** `GrpcServerPlugin` builds on `NettyServerBuilder` with no
gRPC-Web handler, no Connect protocol and no servlet adapter, so a browser cannot reach it at all.
Node is what CI gates on; Bun and Deno are exercised and claimed only if they pass.

## 6. Contract and codegen

The proto needs a bootstrap path the OpenAPI file did not, because a running server does not serve
it. `scripts/fetch-contract.sh` gains a third mode:

- `--release <tag>` downloads both artifacts and verifies both `.sha256` files. Written in M1, still
  never exercised, because no release ships the assets yet.
- `--image <tag>` fetches the spec from a running container. Unchanged, and cannot supply the proto.
- `--proto-from <path>` copies `grpc/src/main/proto/arcadedb-server.proto` from a local `arcadedb`
  checkout. This is the bootstrap, for the same reason M1 needed `--image`.

`npm run generate` runs both generators, and the existing drift gate covers both without change: it
already regenerates everything and diffs.

**The proto carries no staleness guard, and cannot have one.** The OpenAPI guard works because M0 left
a structural marker in the spec - the session header under `begin`'s 204. The proto has no
before-and-after marker because it has not changed. The protection is that it is committed and
diffed, not fetched implicitly. Stating that is better than inventing a check that looks like
protection and is not.

## 7. The API

```ts
const client = createClient({ baseUrl: "https://host:50051", auth: passwordAuth("root", pw) });
```

`createGrpcTransport` from `@connectrpc/connect-node`, real gRPC over HTTP/2. `passwordAuth` sets
`x-arcade-user`, `x-arcade-password` and an optional `x-arcade-database`; `bearerAuth` sets
`authorization`. `passwordAuth` refuses an insecure channel unless the caller explicitly opts in,
because gRPC metadata is plaintext and plaintext credential exposure was a finding in #5048.

**`streamQuery`** is a thin async iterable over the server stream, flattening `QueryResult` batches
into individual rows. It takes one request object (mirroring the generated RPC's own shape), not a
separate `database` positional argument:

```ts
for await (const row of client.streamQuery({ database: "mydb", query: "SELECT FROM Beer", language: "sql" })) { }
```

`retrievalMode` and `batchSize` pass through rather than being chosen for the caller. `CURSOR`,
`MATERIALIZE_ALL` and `PAGED` have materially different memory and consistency behaviour, and picking
one silently would be the facade deciding something only the caller knows.

**`insertStream`** is where the wrapper earns its place. It also takes one request object; `chunks`
is an `AsyncIterable` of *row batches* (`GrpcRecord[]`), not a flat `AsyncIterable<GrpcRecord>` - the
caller decides how many rows go in each wire chunk, and each element of `chunks` becomes exactly one
`InsertChunk`:

```ts
const summary = await client.insertStream({
  database: "mydb",
  options: { targetClass: "Beer" },
  chunks: rows,   // rows: AsyncIterable<GrpcRecord[]>
});
```

`InsertChunk` carries protocol bookkeeping a caller should not hand-roll: a client-generated
`session_id`, a monotonic `chunk_seq`, a `last` flag, and `database` required on the first chunk only.
The wrapper owns all of it and awaits the `InsertSummary`. #5041 found the server side of this had
wrong half-close semantics and silent data loss, so the close-and-await path is tested by asserting
the summary matches what is actually queryable afterwards, not merely that the call returned. A
server-side gap (#6597, fixed but not yet released) meant `InsertChunk.database` went unread on every
released server, so the wrapper also mirrors `database` into `options.database` on the first chunk;
that mirroring is harmless once #6597 ships, since a fixed server treats the chunk field as
authoritative when present and the two values are always identical here.

**`transaction(fn)`** mirrors the HTTP client:

```ts
await client.transaction("mydb", async (tx) => {
  await tx.executeCommand({ command: "INSERT INTO Beer SET name = 'X'" });
});
```

It calls `BeginTransaction` and validates the response before trusting it - a missing or blank
transaction id throws immediately, rather than running the callback against a handle whose every
call would silently fall back to the server's auto-transaction path. It threads the id into every
request made through `tx`, commits on return, and rolls back on throw. A resolved
`CommitTransaction` call is not treated as proof of a commit: the server can answer a transaction id
it no longer recognises (e.g. reaped after an idle timeout) with `success=true, committed=false` and
no error status, so `transaction` reads `committed` and throws - with the server's own message -
instead of reporting success for a transaction whose writes were lost.

`TransactionHandle` deliberately excludes `bulkInsert` and `insertStream`: both RPCs build their own
`InsertContext`, resolve their own `Database`, and commit independently of any transaction context in
the request, on every server as of this writing (`ArcadeData/arcadedb#6607`, filed against this and
still open). Binding them into `tx` would silently lie about durability - their writes would survive
a rollback. Both stay reachable outside a transaction (`client.insertStream`, `client.raw.bulkInsert`).

**Errors** surface as Connect's `ConnectError`, not as `ArcadeDBError`. The two packages genuinely
differ here: `ArcadeDBError` is built from the OpenAPI `ErrorResponse` schema, while gRPC carries a
status code and details, and audit finding COR-1 recorded that engine exceptions collapse to a status
plus a string over this transport and are not reconstructable client-side. A shared error type would
have to be the union of two things carrying different information.

## 8. Testing

**Unit tests against a mocked transport.** Connect-ES makes a transport an interface, so these need
no server and no Docker. They cover the hand-written layer only: that `transaction` threads the id
into every request and ends on both paths; that `insertStream` generates one `session_id`, increments
`chunk_seq` from 1, sets `database` on the first chunk only and marks `last`; that the auth
interceptors set the right metadata.

**e2e via Testcontainers**, with two settings established by probing rather than assumption:

```
JAVA_OPTS: -Darcadedb.server.rootPassword=<at least 8 characters>
           -Darcadedb.server.plugins=GRPC:com.arcadedb.server.grpc.GrpcServerPlugin
withExposedPorts(2480, 50051)
```

The gRPC plugin is **not** enabled by default: `SERVER_PLUGINS` defaults to empty. And the root
password must be **at least 8 characters** or the server exits at startup with
`ServerSecurityException`, which presents as a closed port and reads exactly like "gRPC is broken".
A probe using a 7-character password produced precisely that false signal while preparing this
design.

The suite creates its database over HTTP, since there is no data-plane RPC for it and admin is out of
scope, then covers: both auth mechanisms; `executeCommand` writing and `streamQuery` reading back;
`insertStream` ingesting a batch whose summary matches what is queryable afterwards; a `transaction`
committing with visible writes; and a `transaction` whose body throws leaving no writes behind.

**That last test must assert the mechanism, not the outcome.** M1's e2e proved that asserting a row is
absent after a failed transaction is vacuous - an abandoned transaction also leaves writes invisible,
through ordinary isolation rather than cleanup. The test asserts that `RollbackTransaction` was called
and `CommitTransaction` was not.

## 9. CI, release and sequencing

**CI** extends the existing jobs rather than adding new ones. The drift gate already regenerates and
diffs everything, so `buf generate` joins it; lint, typecheck and unit tests are workspace-wide; e2e
gains a second suite in the job that already has Docker and Node 24.

**The M2 smoke job needs no change at all.** It runs `npm run e2e` in this repository, so the gRPC
suite runs against the server built from the commit under review as soon as it exists, provided the
suite enables the plugin itself. That falls out of how M2 was wired.

**Release** reuses `publish.yml` unchanged: `workflow_dispatch`, version input, contract-match gate,
OIDC with provenance, publishing the workspace. Adding a second package is configuration. The same
SNAPSHOT-pinning decision gates the first publish of either package.

**Sequencing:**

1. `buf.yaml`, `buf.gen.yaml` and `fetch-contract.sh --proto-from`, with the proto committed
2. `buf generate` wired into the drift gate
3. Package scaffold, transport, auth interceptors, unit tests
4. `streamQuery`, then `insertStream` with its bookkeeping
5. `transaction(fn)`
6. e2e
7. README and the compatibility table

Steps 1 and 2 are the shared infrastructure a future Python or Go gRPC client inherits, so they are
worth getting right before any client code exists.

## 10. Non-goals

- The admin service as a supported ergonomic path.
- `InsertBidirectional`, `GraphBatchLoad` and the unary CRUD RPCs as hand-written wrappers.
- The inline `begin`/`commit` transaction flags as a wrapped API.
- Browser support, which the server cannot provide without a gRPC-Web or Connect layer.
- A shared `client-core` package.
- Publishing. M1b builds and gates; the first publish of either package waits on the 26.9.1 release
  and the contract refresh.
