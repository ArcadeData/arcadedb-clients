# @arcadedb/client

A TypeScript/JavaScript HTTP client for [ArcadeDB](https://arcadedb.com), generated from ArcadeDB's
OpenAPI contract.

**This package is not yet published to npm.** The instructions below describe how it will be
installed and used once a release is made; until then, consume it from this repository (workspace
link or `npm pack`).

## Requirements

- Node.js `>=20`.
- ESM only. The package has no CommonJS build and no `require()` entry point; import it with
  `import`, not `require`.

## Installation

```bash
npm install @arcadedb/client
```

## Quick start

```ts
import { createClient, basicAuth } from "@arcadedb/client";

const server = createClient({
  baseUrl: "http://localhost:2480",
  auth: basicAuth("root", "playwithdata"),
});

const db = server.db("mydb");
const { result } = await db.query({
  language: "sql",
  command: "SELECT FROM Person WHERE age > ?",
  params: { 1: 21 },
});
```

A bearer token (for example, a session token returned by `/api/v1/login`) works the same way:

```ts
import { createClient, bearerAuth } from "@arcadedb/client";

const server = createClient({
  baseUrl: "http://localhost:2480",
  auth: bearerAuth("AU-..."),
});
```

## The result envelope, and why `truncated` matters

`query` and `command` do not return bare rows. They return the whole response envelope:

```ts
interface QueryEnvelope<T> {
  result: T[];
  limit: number;
  returned: number;
  truncated: boolean;
}
```

`truncated` is `true` when the server's serializer hit its row cap while a query still had more
rows to write - `result` is then a partial answer, not a short-but-complete one. A client that
returned only `result` would hand back an array a caller cannot tell apart from a complete result
set; the array looks the same shape either way. Always check `truncated` before treating `result`
as the whole answer, and re-query with a narrower filter or a higher limit when it is `true`.

## Transactions

```ts
const total = await db.transaction(async (tx) => {
  await tx.command({ language: "sql", command: "INSERT INTO Account SET balance = 100" });
  const { result } = await tx.query({ language: "sql", command: "SELECT sum(balance) as total FROM Account" });
  return result[0].total;
});
```

Every call made through the `tx` handle passed into the callback - not the outer `db` - takes part
in the transaction. `transaction` commits when the callback resolves and returns its value; it
rolls back and re-throws when the callback throws or rejects, synchronously or otherwise.

## Two error models

The facade methods (`query`, `command`, `transaction`, `listDatabases`, `exists`, `serverInfo`,
`health`, `ready`, ...) throw `ArcadeDBError` on any non-2xx response:

```ts
import { ArcadeDBError } from "@arcadedb/client";

try {
  await db.query({ language: "sql", command: "SELECT FROM NoSuchType" });
} catch (err) {
  if (err instanceof ArcadeDBError) {
    console.error(err.status, err.error, err.detail, err.requestId);
  }
}
```

`server.raw`, the underlying [openapi-fetch](https://openapi-ts.dev/openapi-fetch/) client, does
**not** throw. It returns `{ data, error }` and leaves handling the error to the caller:

```ts
const { data, error, response } = await server.raw.GET("/api/v1/server", {});
if (error) {
  // handle it yourself; server.raw never throws
}
```

These are two deliberately different contracts in one package. Use the facade for the ergonomics
of try/catch; use `raw` when you want to branch on `{ data, error }` without exceptions. Mixing
assumptions about which one you're calling is the most common way to end up with an unhandled
rejection or a silently ignored error.

## `exists` cannot prove absence

```ts
const present = await server.exists("mydb");
```

`exists` returns `false` both when the database genuinely does not exist and when it exists but
the authenticated caller is not authorized to see it - the server's response does not distinguish
the two cases, so this client cannot either. Do not treat `false` as proof that a database is
absent; it only means "not visible to this caller right now."

## Contract version and compatibility

This package was generated from `contracts/arcadedb-openapi-26.9.1-SNAPSHOT.json`, recorded in
`package.json` as `arcadedb.serverVersion`:

```json
{
  "arcadedb": {
    "serverVersion": "26.9.1-SNAPSHOT"
  }
}
```

| `@arcadedb/client` | ArcadeDB server |
| --- | --- |
| 0.1.0 | 26.9.1-SNAPSHOT |

The client speaks ArcadeDB's HTTP API as described by that contract. Pointing it at a server on a
materially different release may work for the endpoints both versions share, but is not tested or
supported.

## Bundling and tree-shaking

`db.ts`, `db.grafana`, and `db.promql` each load their implementation with a dynamic `import()`
rather than a static one. On a bundler that supports code splitting - Vite, webpack, Rollup, or
esbuild run with `--splitting` - code that only calls `query`, `command`, and `transaction` gets a
chunk that excludes the time-series, Grafana, and PromQL modules; they load only if and when
`db.ts`, `db.grafana`, or `db.promql` is actually reached. Without code splitting, a bundler
inlines those dynamic imports into the single output file, and all three modules ship regardless
of whether they're used. This is verified by `test/treeshake.test.ts`, which bundles a
data-plane-only entry point with esbuild's `splitting` option on and asserts the PromQL and
Grafana route markers are absent from the chunk reachable via static imports alone - it does not
claim, and this README does not claim, that the package sheds unused code under every bundler
configuration.

## License

Apache-2.0.
