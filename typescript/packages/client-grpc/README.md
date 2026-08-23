# @arcadedb/client-grpc

A TypeScript/JavaScript gRPC client for ArcadeDB's data plane, generated from ArcadeDB's Protobuf
contract with [Connect-ES](https://connectrpc.com/).

**This package is not yet published to npm.** Publishing waits on the 26.9.1 release and a
contract refresh, so the first publish isn't permanently pinned to a SNAPSHOT contract. Until
then, consume it from this repository (workspace link or `npm pack`).

If you want an HTTP client instead - including from a browser - see
[`@arcadedb/client`](../client/README.md).

## Requirements

- Node.js `>=20`, Bun, or Deno. See "Runtime targets" below for what that means in practice.
- ESM only. The package has no CommonJS build and no `require()` entry point; import it with
  `import`, not `require`.

## Installation

```bash
npm install @arcadedb/client-grpc
```

## Runtime targets: Node, Bun, Deno - not browsers

This package targets Node, Bun, and Deno. The underlying transport,
[`@connectrpc/connect-node`](https://www.npmjs.com/package/@connectrpc/connect-node), is built on
Node's `node:http2` module, which Bun and Deno both also implement well enough to run it. Node is
what this repository's CI actually exercises today; Bun and Deno are intended targets that have
not (yet) got a CI job of their own, so treat them as likely-to-work rather than verified.

There is no browser build, and there will not be one until the server changes. This is a server
capability question, not a packaging one: ArcadeDB's `GrpcServerPlugin` is plain grpc-java over
HTTP/2, built on Netty's `NettyServerBuilder`, with no gRPC-Web handler, no Connect protocol, and
no servlet adapter in front of it. A browser cannot speak raw HTTP/2 gRPC framing at all - there
is no protocol translation layer for it to go through - so no client library, however written,
can reach this server from a browser. Anyone who needs a browser client uses
[`@arcadedb/client`](../client/README.md) over HTTP instead.

## Quick start

```ts
import { createClient, passwordAuth } from "@arcadedb/client-grpc";

const grpc = createClient({
  baseUrl: "https://localhost:50051",
  auth: passwordAuth("root", "playwithdata", "mydb"),
});

const response = await grpc.raw.executeQuery({
  database: "mydb",
  query: "SELECT FROM Person WHERE age > 21",
  language: "sql",
});
```

`raw` is the generated Connect client for `ArcadeDbService` (the data plane) - every RPC the
`.proto` contract declares is callable through it. `createClient` adds three ergonomic wrappers
on top for the RPCs the generated client alone handles badly: `streamQuery`, `insertStream`, and
`transaction`. Everything else - the unary CRUD calls, `insertBidirectional`, `graphBatchLoad` -
is used directly through `raw`.

## Authentication

Two helpers build an `Interceptor` to pass as `auth`:

```ts
import { bearerAuth, passwordAuth } from "@arcadedb/client-grpc";

bearerAuth("AU-..."); // sets `authorization: Bearer <token>` metadata
passwordAuth("root", "playwithdata", "mydb"); // sets x-arcade-user / x-arcade-password / x-arcade-database metadata
```

`passwordAuth` sends the password in plaintext gRPC metadata, so `createClient` **refuses** to
pair it with a non-TLS (`http://`) `baseUrl` unless you pass `insecure: true` explicitly:

```ts
createClient({ baseUrl: "http://localhost:50051", auth: passwordAuth("root", "pw") });
// throws: refusing to send a plaintext password over insecure baseUrl "http://localhost:50051"

createClient({ baseUrl: "http://localhost:50051", auth: passwordAuth("root", "pw"), insecure: true });
// fine - you opted in
```

Be aware of the limits of this check: it recognizes interceptors that `passwordAuth` itself
produced (via an internal marker), not any interceptor that happens to set the same headers. A
hand-rolled interceptor that sets `x-arcade-password` directly is not caught by this guard - the
refusal is a safety net for the helper this package ships, not a general scan of outgoing
metadata.

## Streaming queries: `streamQuery`

```ts
for await (const row of grpc.streamQuery({
  database: "mydb",
  query: "SELECT FROM Person",
  language: "sql",
})) {
  console.log(row.rid, row.properties);
}
```

`streamQuery` flattens the server's stream of row batches into one row at a time, so the calling
code never has to unwrap `QueryResult.records` itself. That is the only thing it does - it does
not choose `retrievalMode` or `batchSize` for you. `retrievalMode` is deliberately the caller's
choice, because the three modes the `.proto` contract defines differ materially in memory and
consistency behavior:

- `CURSOR` (the default) - runs the query once and streams results as you iterate.
- `MATERIALIZE_ALL` - loads the entire result set on the server first, then emits it in batches.
- `PAGED` - re-issues the query with `LIMIT`/`SKIP` per batch.

Pick `CURSOR` for a large result set you want to bound memory on; `MATERIALIZE_ALL` when you need
a stable snapshot and can afford to hold it server-side; `PAGED` when you want each batch's
consistency independent of the others. This wrapper does not, and should not, guess which one a
given query needs.

## Streaming inserts: `insertStream`

```ts
async function* rows() {
  yield [{ type: "Person", properties: { name: { kind: { case: "stringValue", value: "Alice" } } } }];
  yield [{ type: "Person", properties: { name: { kind: { case: "stringValue", value: "Bob" } } } }];
}

const summary = await grpc.insertStream({
  database: "mydb",
  options: { targetClass: "Person" },
  chunks: rows(),
});

console.log(summary.inserted, summary.failed);
```

`chunks` is an `AsyncIterable` of row batches - one element becomes exactly one wire
`InsertChunk`. The caller decides how many rows go in each batch and when to yield the next one;
`insertStream` owns only the envelope bookkeeping around those batches, which it would otherwise
be easy to get wrong by hand:

- one `session_id` (a fresh UUID), stable for the whole stream
- `chunk_seq` starting at 1 and incrementing by 1 per chunk
- `database` set on the first chunk only (the server caches it for the rest of the session)
- `last: true` on the final chunk only

An empty `chunks` iterable is not an error. A filter that matched nothing is a legitimate reason
to have zero rows to insert, and this package should not turn that into an exception - the same
principle `@arcadedb/client`'s README documents for `truncated`. `insertStream` sends a single
chunk with zero rows and `last: true`, and returns whatever `InsertSummary` the server gives back
for it (verified against a real server: this is accepted cleanly, in under 100ms, and comes back
as an all-zero summary) - it does not invent a summary itself.

### The `InsertOptions.database` workaround

`insertStream` also sets `options.database` to the same value as the first chunk's `database`.
This is a workaround, not part of the wire contract as documented: `InsertChunk.database` is
marked `// REQUIRED` on the first chunk in `arcadedb-server.proto`, but the server's
`InsertContext` construction only reads `InsertOptions.database` - it never looks at
`InsertChunk.database` at all. Without this mirroring, every stream fails at the deferred commit
with `Invalid database name: name is required`, even though `database` was sent exactly as the
contract specifies. See [ArcadeData/arcadedb#6597](https://github.com/ArcadeData/arcadedb/issues/6597).
This mirroring is removable once that issue is fixed server-side; until then, it is what makes
`insertStream` work against the server as it actually behaves today, not as the `.proto` alone
promises.

## Transactions: `transaction`

```ts
const totalRow = await grpc.transaction("mydb", async (tx) => {
  await tx.executeCommand({ command: "INSERT INTO Account SET balance = 100", language: "sql" });
  const { results } = await tx.executeQuery({ query: "SELECT sum(balance) as total FROM Account", language: "sql" });
  return results[0]?.records[0];
});
```

`transaction` begins a server-side transaction, hands the callback a `TransactionHandle` whose
calls (`executeQuery`, `executeCommand`, `createRecord`, `updateRecord`, `deleteRecord`,
`lookupByRid`, `bulkInsert`, `streamQuery`, `insertStream`) all carry the transaction's id
automatically, and ends the transaction on both the success and failure paths: the callback
resolving commits, the callback throwing or rejecting rolls back and re-throws the callback's own
error. This is the safety net against forgetting, dropping, or mismatching a transaction id by
hand - the exact class of defect a 2026 gRPC audit found three times in ad hoc transaction code.

`beginTransaction`, `commitTransaction`, and `rollbackTransaction` are the calls `transaction`
manages for you; the `.proto` contract also lets a request carry inline `begin` / `commit` flags
on individual RPCs, so a call can begin or end a transaction as a side effect without a separate
`BeginTransaction`/`CommitTransaction` round trip. This wrapper deliberately does not wrap those
flags - they are reachable through `grpc.raw` for callers who want that shape, but `transaction`
only ever manages transactions the explicit way.

## The admin service is not a supported path

The `.proto` contract also defines `ArcadeDbAdminService` (`Ping`, `GetServerInfo`,
`ListDatabases`, `ExistsDatabase`, `CreateDatabase`, `DropDatabase`, `GetDatabaseInfo`,
`CreateUser`, `DeleteUser`). `createClient` does not wire up a client for it, and this package
does not export one. It is generated from the same contract as the data plane
(`contracts/arcadedb-server-<version>.proto`), so it remains reachable - generate your own
Connect client against that `.proto` the same way this package's own `raw` client is generated -
but it is not something this package hands you.

The reason is its auth model, not an oversight: every `ArcadeDbAdminService` RPC authenticates
from a `credentials` field inside the request message itself, rather than from gRPC metadata the
way every data-plane call in this package does. Wrapping it here would mean this package's
`auth` option meant one thing for `raw` and `streamQuery`/`insertStream`/`transaction`, and
something else again for admin calls. `@arcadedb/client` already covers the admin service's
actual job - server discovery and database lifecycle (`listDatabases`, `exists`, create/drop) -
over HTTP, so there is no gap this package needs to fill.

## Errors: `ConnectError`, not `ArcadeDBError`

A failed call throws Connect's own `ConnectError`, not the `ArcadeDBError` that
`@arcadedb/client`'s facade methods throw:

```ts
import { ConnectError } from "@connectrpc/connect";

try {
  await grpc.raw.executeQuery({ database: "mydb", query: "SELECT FROM NoSuchType", language: "sql" });
} catch (err) {
  if (err instanceof ConnectError) {
    console.error(err.code, err.message, err.details);
  }
}
```

This is a deliberate asymmetry with `@arcadedb/client`, not an inconsistency to be fixed later.
The two transports carry genuinely different error information - a gRPC status code and details
message versus an HTTP status and a JSON error body - and translating one into the other's shape
would either drop information or invent fields the underlying transport never provided. Each
client surfaces the error its own transport actually gives it.

## Contract version and compatibility

This package was generated from `contracts/arcadedb-server-26.9.1-SNAPSHOT.proto`, recorded in
`package.json` as `arcadedb.serverVersion`:

```json
{
  "arcadedb": {
    "serverVersion": "26.9.1-SNAPSHOT"
  }
}
```

| `@arcadedb/client-grpc` | ArcadeDB server |
| --- | --- |
| 0.1.0 | 26.9.1-SNAPSHOT |

Pointing it at a server on a materially different release may work for the RPCs both versions
share, but is not tested or supported.

## License

Apache-2.0.
