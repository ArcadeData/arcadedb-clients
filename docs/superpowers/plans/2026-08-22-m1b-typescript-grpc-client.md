# M1b: `@arcadedb/client-grpc` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `@arcadedb/client-grpc`, a thin Connect-ES client over ArcadeDB's gRPC proto covering the data plane, plus the `buf` codegen infrastructure a future Python or Go gRPC client will reuse.

**Architecture:** A second package in the existing npm workspace. `buf.yaml` at the repository root declares the shared proto module beside `contracts/`; `typescript/buf.gen.yaml` is TypeScript's codegen config. Generated code is committed and covered by the existing drift gate. A thin hand-written layer wraps only streaming and transactions; everything else goes through the generated Connect clients.

**Tech Stack:** TypeScript 5.9.3 (pinned), ESM-only, `@bufbuild/buf` 1.72.0, `@bufbuild/protoc-gen-es` 2.14.0, `@bufbuild/protobuf` 2.14.0, `@connectrpc/connect` and `@connectrpc/connect-node` 2.1.2. All Apache-2.0 (protobuf is Apache-2.0 AND BSD-3-Clause); all allow-listed.

**Spec:** `docs/superpowers/specs/2026-08-22-m1b-typescript-grpc-client-design.md`

## Global Constraints

- **Do not commit without the maintainer's go-ahead** (`CLAUDE.md` in the server repository). Confirm before the first commit.
- **Never add Claude as an author.** No `Co-Authored-By` trailer.
- **No em dash characters** in any file.
- **ESM only**; relative imports carry explicit `.js` extensions under NodeNext.
- **Do NOT bump TypeScript** (5.9.3, pinned deliberately: npm `latest` is 7.0.2 and `typescript-eslint` rejects it) or the existing `openapi-fetch` pin.
- **No per-file license headers** on `.ts` files.
- **Every new dependency must be Apache-2.0 compatible.** The five above are verified; check anything else with `npm view <pkg> license` and record it.
- **NEVER hand-edit generated output.** `packages/client-grpc/src/gen/` is `buf` output.
- **Commit with explicit `git add <path>`**, never `git add -A`.
- **Do not publish anything.**

## Verified facts, do not re-derive

**Connect-ES v2 API**, read from the installed type definitions and the official docs:

```ts
import { createGrpcTransport } from "@connectrpc/connect-node";
import { createClient } from "@connectrpc/connect";
import type { Interceptor } from "@connectrpc/connect";

const transport = createGrpcTransport({ baseUrl: "https://host:50051", interceptors: [] });
const client = createClient(SomeService, transport);

// Server-streaming: the call returns an AsyncIterable.
for await (const res of client.someServerStreamingMethod({ ... })) { }

// Interceptor. `Interceptor = (next: AnyFn) => AnyFn`, and the request carries
// `readonly header: Headers`, so `.set()` is how a header is added.
const auth: Interceptor = (next) => async (req) => {
  req.header.set("x-arcade-user", user);
  return next(req);
};
```

**NOT verified, and the implementer must confirm before relying on it:** the exact shape for calling a
CLIENT-streaming method (`InsertStream`). The docs did not show it. Read the generated client's type
signature for `insertStream` and follow what it actually declares. Do not assume it takes an
`AsyncIterable`; confirm it.

**Server facts**, established by reading the source and by probing a real container:

- The gRPC plugin is NOT enabled by default (`SERVER_PLUGINS` defaults to empty). Enable with
  `-Darcadedb.server.plugins=GRPC:com.arcadedb.server.grpc.GrpcServerPlugin`.
- The gRPC port is **50051**.
- **The root password must be at least 8 characters.** A shorter one kills the server at startup with
  `ServerSecurityException: User password too short (<8 characters)`, which presents as a closed port
  and reads exactly like "gRPC is broken". A probe with a 7-character password produced precisely
  that false signal while this plan was being written.
- The two services authenticate DIFFERENTLY (`GrpcAuthInterceptor:87` branches on method name):
  `ArcadeDbAdminService` reads a `DatabaseCredentials credentials` field from the request MESSAGE;
  the data plane reads METADATA (`authorization: Bearer`, or `x-arcade-user` / `x-arcade-password`,
  plus optional `x-arcade-database`).

**Proto shape** (`contracts/arcadedb-server-<ver>.proto`, 702 lines, 23 RPCs, 2 services):

```proto
message TransactionContext {
  string transaction_id = 1; string database = 2;
  bool begin = 3; bool commit = 4; bool rollback = 5;
  int64 timeout_ms = 6; bool read_only = 7;
}
message InsertChunk {
  string database = 1;            // REQUIRED on the first chunk, optional after (server caches)
  DatabaseCredentials credentials = 2;
  InsertOptions options = 3;
  TransactionContext transaction = 4;
  string session_id = 5;          // client-generated, stable for the stream
  int64 chunk_seq = 6;            // 1, 2, 3, ...
  repeated GrpcRecord rows = 7;
  bool last = 8;
}
```

`BeginTransactionResponse` carries `string transaction_id`.

---

## File Map

| Path | Responsibility | Task |
|---|---|---|
| `buf.yaml` | Repo-root proto module, shared across languages | 1 |
| `typescript/buf.gen.yaml` | TypeScript codegen config | 1 |
| `scripts/fetch-contract.sh` | New `--proto-from` mode | 1 |
| `contracts/arcadedb-server-<ver>.proto` | The committed proto | 1 |
| `typescript/package.json` | `generate` runs both generators | 2 |
| `typescript/packages/client-grpc/src/gen/` | Generated, committed, never hand-edited | 2 |
| `typescript/packages/client-grpc/package.json` | Package manifest | 3 |
| `.../src/auth.ts` | `bearerAuth`, `passwordAuth` interceptors | 3 |
| `.../src/index.ts` | `createClient`, transport wiring | 3 |
| `.../src/stream.ts` | `streamQuery`, `insertStream` | 4 |
| `.../src/transaction.ts` | `transaction(fn)` | 5 |
| `typescript/e2e/grpc.test.ts` | e2e suite | 6 |
| `.../README.md` | Package docs | 7 |

---

## Task 1: buf setup and the proto bootstrap

**Context:** Everything downstream generates from the file this task commits. `buf.yaml` goes at the repository ROOT, not under `typescript/`, because the proto module is language-agnostic exactly like `contracts/`.

**Files:**
- Create: `buf.yaml`, `typescript/buf.gen.yaml`, `contracts/arcadedb-server-<ver>.proto`
- Modify: `scripts/fetch-contract.sh`

**Interfaces:**
- Consumes: nothing.
- Produces: the committed proto path, and a working `buf generate`. Record the exact filename; Task 2 references it.

- [ ] **Step 1: Add the `--proto-from` mode to `scripts/fetch-contract.sh`**

A running server does not serve the proto, so `--image` cannot supply it. Add a third mode that copies `grpc/src/main/proto/arcadedb-server.proto` from a local `arcadedb` checkout:

```bash
./scripts/fetch-contract.sh --proto-from /Users/frank/projects/arcade/arcadedb
```

Name the output `contracts/arcadedb-server-<version>.proto`, using the same version the OpenAPI contract carries, so the pair stays legible as one contract. Keep `set -euo pipefail`. Do not disturb the existing `--release` and `--image` modes.

- [ ] **Step 2: Run it and sanity-check the proto**

```bash
./scripts/fetch-contract.sh --proto-from <path-to-arcadedb>
wc -l contracts/arcadedb-server-*.proto
grep -c "^  rpc " contracts/arcadedb-server-*.proto
grep -c "^service " contracts/arcadedb-server-*.proto
```

Expected: about 702 lines, 23 rpcs, 2 services. Report the actual numbers. If they differ substantially, stop and report rather than proceeding: the proto is not what this plan was written against.

- [ ] **Step 3: Create `buf.yaml` at the repository root**

A `v2` module pointing at `contracts/`. Consult `buf --version` (1.72.0) and the current buf schema rather than copying an older `v1` example; buf changed its config format at v1.32 and a `v1` file will still work but is not what a new module should use.

- [ ] **Step 4: Create `typescript/buf.gen.yaml`**

Generate with `protoc-gen-es` into `packages/client-grpc/src/gen`. protobuf-es v2's `protoc-gen-es` emits BOTH message types and service descriptors, so no second plugin is needed - this is the reason the spec chose it.

Verify the plugin invocation against protoc-gen-es 2.14.0's own documentation rather than assuming the v1 shape; the `opt: target=ts` and `local:` versus `remote:` conventions both changed between major versions.

- [ ] **Step 5: Generate and inspect**

```bash
cd typescript && npx buf generate --template buf.gen.yaml ..
```

Adjust the invocation to whatever the config actually requires. Then READ the generated output and record in your report:
- the exported name of the `ArcadeDbService` schema, which Task 3 passes to `createClient`
- the generated method names for `StreamQuery`, `InsertStream`, `ExecuteCommand`, `BeginTransaction`, `CommitTransaction`, `RollbackTransaction`
- **the exact type signature of the generated `insertStream` method**, which is the one API this plan could not verify in advance

Tasks 3 through 5 are FORBIDDEN from guessing these and will read your report.

- [ ] **Step 6: Commit**

```bash
git add buf.yaml typescript/buf.gen.yaml scripts/fetch-contract.sh contracts/
git commit -m "feat: add the gRPC proto contract and buf codegen configuration"
```

---

## Task 2: Wire `buf generate` into the drift gate

**Context:** The existing gate regenerates everything and diffs. It must now cover both generators, so a proto change that is not regenerated fails CI.

**Files:**
- Modify: `typescript/package.json`
- Create (generated): `typescript/packages/client-grpc/src/gen/`

- [ ] **Step 1: Make `generate` run both generators**

The current script runs `openapi-typescript`. Extend it so one `npm run generate` produces both outputs. Keep them as separate sub-scripts (`generate:http`, `generate:grpc`) called by one `generate`, so a failure names which generator broke.

- [ ] **Step 2: Confirm the gate now covers the generated gRPC code**

```bash
cd typescript && npm run generate
git diff --exit-code -- packages/client-grpc/src/gen
```

Expected: exits 0 on a clean tree.

- [ ] **Step 3: PROVE the gate fires for the gRPC output**

Append a stray line to a file under `packages/client-grpc/src/gen/`, run `npm run generate && git diff --exit-code -- packages/client-grpc/src/gen`, and confirm it exits NON-ZERO. Restore and confirm zero. Capture both outputs.

The HTTP half of this gate was proved in M1; the gRPC half is new and unproven until you watch it fail. A gate never observed failing is not a gate.

- [ ] **Step 4: Commit**

```bash
git add typescript/package.json typescript/packages/client-grpc/src/gen
git commit -m "feat: generate the gRPC bindings and gate them against drift"
```

---

## Task 3: Package scaffold, transport, and auth

**Files:**
- Create: `packages/client-grpc/{package.json,tsconfig.json}`, `src/{auth.ts,index.ts}`, and their tests

**Interfaces:**
- Consumes: the generated service schema name from Task 1's report.
- Produces, and Tasks 4 and 5 depend on these exact signatures:
  - `bearerAuth(token: string): Interceptor`
  - `passwordAuth(user: string, password: string, database?: string): Interceptor`
  - `createClient(opts: { baseUrl: string; auth?: Interceptor; insecure?: boolean }): ArcadeDBGrpcClient`
  - `ArcadeDBGrpcClient` exposing `raw` (the generated Connect client) plus the methods added in 4 and 5

- [ ] **Step 1: Write the failing auth tests**

Against a mocked transport, assert that `passwordAuth("root", "pw", "mydb")` sets `x-arcade-user`, `x-arcade-password` and `x-arcade-database`, and that `bearerAuth("AU-x")` sets `authorization` to `Bearer AU-x`. Run them and confirm they fail with "not defined".

- [ ] **Step 2: Implement `auth.ts`**

```ts
import type { Interceptor } from "@connectrpc/connect";

export function passwordAuth(user: string, password: string, database?: string): Interceptor {
  return (next) => async (req) => {
    req.header.set("x-arcade-user", user);
    req.header.set("x-arcade-password", password);
    if (database !== undefined) req.header.set("x-arcade-database", database);
    return next(req);
  };
}
```

`bearerAuth` is the same shape setting `authorization`.

- [ ] **Step 3: Refuse plaintext credentials unless opted in**

`passwordAuth` sends a password as plaintext metadata. When `createClient` is given a non-TLS `baseUrl` (an `http://` scheme) AND a password interceptor, it must throw unless `insecure: true` was passed explicitly. Plaintext credential exposure was a finding in the closed hardening issue #5048; failing loudly beats leaking quietly.

Add a test asserting the throw, and one asserting `insecure: true` permits it.

- [ ] **Step 4: Implement `index.ts`**

`createGrpcTransport({ baseUrl, interceptors: auth ? [auth] : [] })`, then `createClient(<the generated service schema>, transport)`. Expose the generated client as `raw`.

- [ ] **Step 5: Verify and commit**

```bash
cd typescript && npm run lint && npm run typecheck && npm test
```

```bash
git commit -m "feat: add the gRPC transport and auth interceptors"
```

---

## Task 4: `streamQuery` and `insertStream`

**Context:** The two wrappers that justify the package having a facade at all.

**Files:**
- Create: `packages/client-grpc/src/stream.ts` and its tests
- Modify: `src/index.ts` to attach both

- [ ] **Step 1: Re-read the generated signature for `insertStream`**

Task 1's report records it. Follow what the generated code declares. If it disagrees with anything in this plan, the generated code wins and you say so in your report.

- [ ] **Step 2: Write the failing tests**

For `streamQuery`: that it yields each row from the server stream, and that `retrievalMode` and `batchSize` reach the request unchanged rather than being defaulted by the wrapper.

For `insertStream`, against a mocked transport that records the chunks sent:
- exactly ONE `session_id` is used for the whole stream, and it is non-empty
- `chunk_seq` starts at 1 and increments by 1
- `database` is set on the FIRST chunk only
- the final chunk has `last` true
- the returned value is the server's `InsertSummary`

The chunk bookkeeping tests are the point of this task. Run them and confirm each fails for the right reason.

- [ ] **Step 3: Implement**

Keep `streamQuery` thin - it is `for await` over the generated call, with options passed through. `insertStream` owns the `session_id`, `chunk_seq`, first-chunk-`database` and `last` bookkeeping described above.

- [ ] **Step 4: Verify and commit**

```bash
git commit -m "feat: add the streaming query and insert wrappers"
```

---

## Task 5: `transaction(fn)`

**Context:** The wrapper that removes the footgun the 2026-07 audit found three times (#5040, #5041, #5042).

**Files:**
- Create: `packages/client-grpc/src/transaction.ts` and its tests
- Modify: `src/index.ts`

**Interfaces:**
- Produces: `transaction<T>(database: string, fn: (tx: TransactionHandle) => Promise<T>): Promise<T>`,
  where `TransactionHandle` exposes the data-plane calls with the transaction context bound.

- [ ] **Step 1: Write the failing tests**

Against a mocked transport recording every request:
- `BeginTransaction` is called first, and its returned `transaction_id` appears in the `TransactionContext` of EVERY subsequent request made through `tx`
- `CommitTransaction` is called on normal return, and `RollbackTransaction` is not
- `RollbackTransaction` is called when the body throws, `CommitTransaction` is not, and the ORIGINAL error is what propagates
- rollback also happens when the body throws SYNCHRONOUSLY, not only on a rejected promise
- a failing commit issues a best-effort rollback and surfaces the commit error

The last two are the ones M1's equivalent got wrong initially and that its final review caught. Do not skip them.

- [ ] **Step 2: Implement**

Note the transaction id travels in a request MESSAGE field (`TransactionContext transaction`), not a header - unlike the HTTP client's session, which is a header. The handle merges the context into each request it forwards.

Do NOT wrap the inline `begin`/`commit`/`rollback` flags. They are a separate per-call model, reachable through `raw`.

- [ ] **Step 3: Verify and commit**

```bash
git commit -m "feat: add the gRPC transaction wrapper"
```

---

## Task 6: End-to-end against a real server

**Files:**
- Create: `typescript/e2e/grpc.test.ts`
- Modify: `typescript/e2e/` config if a second suite needs registering

- [ ] **Step 1: Stand up the container**

```
GenericContainer(<image>)
  .withEnvironment({ JAVA_OPTS:
      "-Darcadedb.server.rootPassword=<AT LEAST 8 CHARS> " +
      "-Darcadedb.server.plugins=GRPC:com.arcadedb.server.grpc.GrpcServerPlugin" })
  .withExposedPorts(2480, 50051)
```

Both facts are verified against a real container. **The password must be at least 8 characters** or the server exits at startup and port 50051 is simply closed, which looks exactly like a gRPC failure. Put that reason in a comment in the test file.

Honor `ARCADEDB_DOCKER_IMAGE` exactly as the HTTP suite does, so the M2 smoke job in `ArcadeData/arcadedb` picks this suite up with no change on its side.

- [ ] **Step 2: Write the suite**

Create the database over HTTP (there is no data-plane RPC for it and admin is out of scope), then cover: both auth mechanisms; `executeCommand` writing and `streamQuery` reading it back; `insertStream` ingesting a batch whose summary matches what is queryable afterwards; a `transaction` committing with visible writes; and a `transaction` whose body throws leaving no writes behind.

**The rollback test must assert the MECHANISM, not the outcome.** M1's e2e proved that asserting a row is absent is vacuous here: an abandoned transaction leaves writes invisible too, through ordinary isolation rather than cleanup. Assert that `RollbackTransaction` was actually called and `CommitTransaction` was not.

- [ ] **Step 3: Prove the rollback test can fail**

Delete the rollback call from the implementation, re-run, and confirm the test goes RED. Restore and confirm green. Capture both. M1's equivalent test passed with the rollback deleted until it was strengthened; do not ship the weak version again.

- [ ] **Step 4: Verify and commit**

```bash
cd typescript && npm run e2e
git commit -m "test: exercise the gRPC client end to end against a real server"
```

---

## Task 7: Documentation

**Files:**
- Create: `packages/client-grpc/README.md`
- Modify: root `README.md`, `packages/client/README.md` cross-reference

- [ ] **Step 1: Write the package README**

Cover: installation and the Node/Bun/Deno target set; **why there is no browser support** (the server speaks plain gRPC over HTTP/2 with no gRPC-Web or Connect layer, so this is a server capability question, not a packaging one); both auth helpers and the plaintext refusal; `streamQuery` with a note that `retrievalMode` is the caller's choice; `insertStream` and what bookkeeping it owns; `transaction`; that the admin service is reachable through the generated client but is not a supported path, and why; that errors surface as Connect's `ConnectError` rather than `ArcadeDBError`, and that this asymmetry with `@arcadedb/client` is deliberate.

- [ ] **Step 2: Cross-reference from the other READMEs**

The root README gains the second package. `@arcadedb/client`'s README gains a line pointing at this one for the throughput persona.

- [ ] **Step 3: Commit**

```bash
git commit -m "docs: document the gRPC client package"
```

---

## Done criteria

- [ ] `npm run generate && git diff --exit-code` clean, and the gRPC half of the gate has been OBSERVED failing on a hand-edited generated file
- [ ] `npm run lint && npm run typecheck && npm test` green, with the unit count risen
- [ ] `npm run e2e` green for both suites
- [ ] The e2e rollback test has been OBSERVED failing with the rollback call removed
- [ ] Nothing published

## Deliberately not in this plan

- The admin service as a supported path, `InsertBidirectional`, `GraphBatchLoad`, the unary CRUD RPCs, and the inline transaction flags. All reachable through the generated client.
- Publishing either package. That waits on the 26.9.1 release and the contract refresh, so the first publish is not permanently pinned to a SNAPSHOT contract.
