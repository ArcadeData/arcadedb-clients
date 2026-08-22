# M1: `@arcadedb/client` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `@arcadedb/client`, a thin `fetch`-native TypeScript client generated from ArcadeDB's published OpenAPI contract, plus the shared repository infrastructure every future language client will reuse.

**Architecture:** A language-partitioned monorepo. `contracts/` and `scripts/` are shared and language-agnostic; `typescript/` is an npm workspaces root holding the one package. Types are generated from a committed contract by `openapi-typescript`; a thin hand-written facade sits over `openapi-fetch`. Nothing publishes except by manual dispatch.

**Tech Stack:** TypeScript (ESM-only, `tsc` only, no bundler), Node >=20, npm workspaces, `openapi-typescript` 7.13.0, `openapi-fetch` 0.17.0 (both MIT), Vitest or Jest for unit tests, Testcontainers for e2e, `esbuild` for the tree-shaking check only.

**Spec:** `docs/superpowers/specs/2026-08-21-m1-typescript-http-client-design.md`

## Global Constraints

- **Do not commit without the maintainer's go-ahead.** The parent project's `CLAUDE.md` says "do not commit on git, I will do it after a review." Confirm before the first commit, then follow whatever cadence is set.
- **Never add Claude as an author** of any code or commit. No `Co-Authored-By` trailer.
- **No em dash characters (`—`)** in any file. Use a normal dash, a comma, or rephrase.
- **Node floor is `>=20`.** Declare it in `engines`.
- **ESM only.** `"type": "module"`, an `exports` map, no CJS build, no bundler in the published output.
- **`sideEffects: false`** on the package, so bundlers may tree-shake.
- **Apache 2.0.** `LICENSE` at the repo root and a `license` field per package. NO per-file license headers on TypeScript files.
- **Dependencies must be Apache-2.0 compatible.** `openapi-typescript` and `openapi-fetch` are both MIT and verified. Any further dependency needs the same check before it is added; when in doubt, do not add it.
- **`openapi-fetch` is pre-1.0 (0.17.0).** Pin it exactly rather than with a caret, and treat a minor bump as a potentially breaking change.
- **GitHub Actions pinned by commit SHA**, never by tag.
- **NEVER hand-edit generated files.** `typescript/packages/client/src/generated/` is output. The drift gate exists to catch exactly that.
- **Do not invent generated type names.** The contract does not exist until Task 2. From Task 4 onward, read `typescript/packages/client/src/generated/schema.d.ts` and use the operation keys and types it actually contains. If a name in this plan disagrees with the generated file, the generated file wins - say so in your report.

---

## File Map

| Path | Responsibility | Task |
|---|---|---|
| `.gitignore`, `typescript/package.json`, `typescript/tsconfig.base.json` | Workspace root, TS config, lint config | 1 |
| `.github/dependabot.yml`, `.github/workflows/ci.yml` | Dependency updates; lint and typecheck gate | 1 |
| `scripts/fetch-contract.sh` | Two-mode contract fetch, with the pre-M0 refusal | 2 |
| `contracts/arcadedb-openapi-<ver>.json` | The committed contract | 2 |
| `typescript/packages/client/package.json` | The published package manifest | 3 |
| `typescript/packages/client/src/generated/schema.d.ts` | Generated types (committed, never hand-edited) | 3 |
| `typescript/packages/client/src/errors.ts` | `ArcadeDBError` | 4 |
| `typescript/packages/client/src/auth.ts` | `basicAuth`, `bearerAuth` middleware | 4 |
| `typescript/packages/client/src/index.ts` | `createClient`, server-scoped facade, `.db()`, `.raw` | 4 |
| `typescript/packages/client/src/facade/data.ts` | `query`, `command`, `transaction` | 5 |
| `typescript/packages/client/src/facade/{timeseries,dashboards}.ts` | `ts`, `grafana`, `promql` namespaces | 6 |
| `typescript/packages/client/test/treeshake.test.ts` | Bundle-content assertion | 7 |
| `typescript/e2e/` | Testcontainers suite | 8 |
| `.github/workflows/publish.yml`, `README.md` | Manual-dispatch release; compatibility table | 9 |

---

## Task 1: Scaffold the repository

**Context:** Nothing exists but `LICENSE`. This task creates the workspace skeleton and a CI gate that can only lint and typecheck, because there is no code to test yet. Everything later builds on this shape.

**Files:**
- Create: `.gitignore`, `typescript/package.json`, `typescript/tsconfig.base.json`, `.github/dependabot.yml`, `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: nothing.
- Produces: an npm workspaces root at `typescript/` with workspace glob `packages/*`; scripts `lint`, `typecheck` at that root. Later tasks add `generate`, `test`, `e2e` to the same root.

- [ ] **Step 1: Create `.gitignore`**

```
node_modules/
dist/
*.tsbuildinfo
.DS_Store
coverage/
```

- [ ] **Step 2: Create `typescript/package.json`**

```json
{
  "name": "@arcadedb/clients-root",
  "private": true,
  "type": "module",
  "workspaces": ["packages/*"],
  "engines": { "node": ">=20" },
  "scripts": {
    "typecheck": "tsc --build",
    "lint": "eslint ."
  }
}
```

- [ ] **Step 3: Create `typescript/tsconfig.base.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "skipLibCheck": true
  }
}
```

- [ ] **Step 4: Add a linter**

Install ESLint with `typescript-eslint` and a minimal config. Keep the ruleset small: this is a library with one hand-written module set, and an opinionated ruleset will generate churn without catching defects. Verify both packages' licences are Apache-2.0 compatible before adding them (both are MIT at time of writing; confirm).

- [ ] **Step 5: Create `.github/dependabot.yml`**

Two ecosystems: `npm` at directory `/typescript`, and `github-actions` at `/`. Weekly, grouped minor and patch updates.

- [ ] **Step 6: Create `.github/workflows/ci.yml`**

Path-filtered to `typescript/**`, `contracts/**`, `scripts/**` and the workflow itself. One job: checkout (pinned SHA), setup-node 20 with npm cache keyed on `typescript/package-lock.json`, `npm ci`, `npm run lint`, `npm run typecheck`. Later tasks add steps to this job.

Path filtering is not premature: this repository will hold several languages, and an unfiltered workflow means a Python change runs the TypeScript suite forever after.

- [ ] **Step 7: Verify**

```bash
cd typescript && npm install && npm run lint && npm run typecheck
```

Expected: both succeed against an empty workspace. `tsc --build` with no packages is a no-op success, not an error.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "chore: scaffold the clients monorepo with a typescript workspace"
```

---

## Task 2: The contract fetch script and the bootstrap contract

**Context:** This is the single most consequential task in the plan. Every generated client in every future language derives from the file this task commits. Getting a **pre-M0** contract here silently produces the exact broken client that milestone M0 existed to prevent.

**Files:**
- Create: `scripts/fetch-contract.sh`
- Create: `contracts/arcadedb-openapi-<version>.json`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: a committed contract at `contracts/arcadedb-openapi-<version>.json`, normalised with `jq -S`. Task 3 generates from it. Record the exact filename in your report; later tasks reference it.

- [ ] **Step 1: Build a post-M0 ArcadeDB image**

No published image contains the M0 spec fixes yet: the newest release is 26.8.1 (2026-08-03) and M0 merged afterwards as `fa599b7516`. So the contract must come from a locally built image.

From a checkout of `ArcadeData/arcadedb` on `main` (a sibling directory, NOT inside this repository):

```bash
git -C <path-to-arcadedb> checkout main && git -C <path-to-arcadedb> pull
cd <path-to-arcadedb> && ./mvnw install -DskipTests          # FULL reactor FIRST, see below
cd <path-to-arcadedb>/package && ../mvnw install -Pdocker -DskipTests
docker images arcadedata/arcadedb
```

**The full-reactor `install` first is not optional.** Building only the `package` module resolves
`arcadedb-engine` and friends from `~/.m2`, which may hold jars older than the source just pulled.
The resulting image TAGS SUCCESSFULLY and then dies at container startup with a `NoSuchFieldError`,
because the assembled jars disagree with each other. `docker images` showing the tag proves nothing
about whether the image runs. This is the stale-artifact trap `CLAUDE.md` documents for `-pl` without
`-am`, one layer out.

**Verify the image boots before using it:** start it, wait for `/api/v1/ready` to answer 204, and only
then treat the build as successful.

Use the tag `docker images` actually reports. Do NOT assume `latest` exists: the `-Pdocker` profile tags by project version, so the tag will look like `26.9.1-SNAPSHOT`.

- [ ] **Step 2: Write `scripts/fetch-contract.sh`**

Two modes, both writing a `jq -S` normalised file into `contracts/`:

- `--release <tag>`: download `arcadedb-openapi-<tag>.json` from the GitHub release with `gh release download`, and verify it against the published `.sha256`.
- `--image <docker-tag>`: `docker run` that image on an **ephemeral host port**, poll `/api/v1/ready` for a 204, then fetch `/api/v1/openapi.json` with `curl --fail -u root:<pw>`.

Two details that are not optional:

The spec endpoint **requires authentication** (`GetOpenApiHandler.isRequireAuthentication()` returns true), so the script sets the root password on the container it starts and uses it.

Bind an ephemeral host port, not 2480. A developer machine may already have ArcadeDB listening on 2480 and the container bind would fail.

Use `set -euo pipefail`.

- [ ] **Step 3: Add the pre-M0 refusal**

The script MUST refuse a contract it cannot confirm is post-M0, and the check must be structural rather than a version-string comparison, because a version string proves nothing about content:

```bash
if ! jq -e '.paths."/api/v1/begin/{database}".post.responses."204".headers."arcadedb-session-id"' \
     "$OUT" > /dev/null; then
  echo "REFUSING: this spec predates the M0 contract fixes." >&2
  echo "It lacks the arcadedb-session-id response header on beginTransaction, which means it also" >&2
  echo "declares 200 where the server sends 204 and leaves PromQL results untyped." >&2
  echo "A client generated from it cannot use transactions. Use a server at or after fa599b7516." >&2
  exit 1
fi
```

This marker is chosen deliberately: M0 both moved begin's success to 204 and attached the session header to it, so the presence of that header under the 204 key cannot be true of any pre-M0 spec.

- [ ] **Step 4: Prove the refusal fires**

Run the script against the **published 26.8.1 image**, which predates M0:

```bash
./scripts/fetch-contract.sh --image arcadedata/arcadedb:26.8.1
```

Expected: the script REFUSES with the message above and exits non-zero. If it succeeds, the guard is broken and the whole safeguard is worthless. Capture the output.

- [ ] **Step 5: Generate the real contract**

```bash
./scripts/fetch-contract.sh --image arcadedata/arcadedb:<tag-from-step-1>
```

Expected: succeeds and writes `contracts/arcadedb-openapi-26.9.1-SNAPSHOT.json` (or whatever the built version is).

- [ ] **Step 6: Sanity-check the contract**

```bash
jq -r '.info.version' contracts/arcadedb-openapi-*.json
jq '.paths | keys | length' contracts/arcadedb-openapi-*.json
jq -r '[.paths[] | keys[]] | length' contracts/arcadedb-openapi-*.json
jq -e '.paths."/api/v1/begin/{database}".post.responses."409"' contracts/arcadedb-openapi-*.json
```

Expected: the version is NOT `1.0.0` and contains no `" (build "` substring; 52 paths; 63 operations; the 409 on begin resolves. Report the actual numbers. If paths is not 52 or operations is not 63, stop and report rather than proceeding: the contract is not what M0 shipped.

- [ ] **Step 7: Commit**

```bash
git add scripts/fetch-contract.sh contracts/
git commit -m "feat: fetch and commit the ArcadeDB OpenAPI contract"
```

---

## Task 3: Codegen and the drift gate

**Context:** Turns the committed contract into committed TypeScript types, and adds the gate that keeps the two in step. Everything after this reads the generated file.

**Files:**
- Create: `typescript/packages/client/package.json`, `typescript/packages/client/tsconfig.json`
- Create (generated): `typescript/packages/client/src/generated/schema.d.ts`
- Modify: `typescript/package.json` (add `generate`), `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: the contract filename from Task 2.
- Produces: `schema.d.ts` exporting the root type **`paths`**, imported by every later task as
  `import type { paths } from "./generated/schema.js";`

- [ ] **Step 1: Create the package manifest**

`typescript/packages/client/package.json`: name `@arcadedb/client`, `"type": "module"`, `"sideEffects": false`, `engines.node >=20`, `license` Apache-2.0, an `exports` map pointing at the built ESM entry and its types, `files` limited to `dist`, and `openapi-fetch` pinned **exactly** (`"0.17.0"`, no caret) as the only runtime dependency.

Add an `arcadedb` field recording the contract this package was generated from, per the spec's versioning decision:

```json
"arcadedb": { "serverVersion": "<the contract's info.version>" }
```

- [ ] **Step 2: Add the generate script**

In `typescript/package.json`:

```json
"generate": "openapi-typescript ../contracts/arcadedb-openapi-<version>.json -o packages/client/src/generated/schema.d.ts"
```

Add `openapi-typescript` as a devDependency at the workspace root.

- [ ] **Step 3: Generate and inspect**

```bash
cd typescript && npm run generate
```

Then READ the head of the generated file and record in your report: the exact name of the root exported type (expected `paths`), and the exact key strings for the operations this client will use, for example `"/api/v1/query/{database}"` and `"/api/v1/begin/{database}"`. Later tasks depend on these exact strings and must not guess them.

- [ ] **Step 4: Add the drift gate to CI**

Append to the CI job, after `npm ci`:

```yaml
      - name: Regenerate types and verify no drift
        working-directory: typescript
        run: |
          npm run generate
          git diff --exit-code -- packages/client/src/generated
```

This proves the committed types match the committed contract, offline and in seconds.

- [ ] **Step 5: Prove the drift gate fires**

Append a stray line to `schema.d.ts`, run `npm run generate && git diff --exit-code -- packages/client/src/generated`, and confirm it exits NON-ZERO. Restore the file and confirm it exits zero. A gate never observed failing is not a gate. Capture both outputs.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: generate typed OpenAPI bindings and gate them against drift"
```

---

## Task 4: Errors, auth, and the server-scoped client

**Context:** The first hand-written code. Everything here is small, and all of it is covered by unit tests against a mocked `fetch` with no server involved.

**Files:**
- Create: `src/errors.ts`, `src/auth.ts`, `src/index.ts` (all under `typescript/packages/client/`)
- Create: matching unit tests
- Modify: `typescript/package.json` (add `test`), `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `paths` from Task 3.
- Produces, and later tasks depend on these exact signatures:
  - `class ArcadeDBError extends Error` with `status: number`, `error?: string`, `exception?: string`, `detail?: string`, `requestId?: string`
  - `basicAuth(user: string, password: string): Middleware`
  - `bearerAuth(token: string): Middleware`
  - `createClient(opts: { baseUrl: string; auth?: Middleware; fetch?: typeof fetch }): ArcadeDBServer`
  - `ArcadeDBServer` with `listDatabases()`, `exists(name)`, `serverInfo()`, `health()`, `ready()`, `db(name): ArcadeDBDatabase`, and `raw` (the unwrapped openapi-fetch client)
  - `ArcadeDBDatabase` is created here but populated in Tasks 5 and 6

- [ ] **Step 1: Write the failing tests first**

Cover, with a mocked `fetch` (no server):
- a 404 JSON body becomes an `ArcadeDBError` carrying `status`, `error`, `exception`, `detail` and `requestId`
- a non-2xx with a non-JSON body still throws `ArcadeDBError` with the right `status` and does not itself throw a parse error
- `basicAuth("root", "pw")` sets `Authorization: Basic ` + base64 of `root:pw`
- `bearerAuth("AU-x")` sets `Authorization: Bearer AU-x`
- `exists` returns the boolean the server sent

Run them and confirm they fail with "not defined" rather than an assertion mismatch.

- [ ] **Step 2: Implement `errors.ts`**

`ArcadeDBError extends Error`, constructed from a status plus the parsed body, tolerating a body that is absent or not JSON.

- [ ] **Step 3: Implement `auth.ts`**

openapi-fetch middleware. The verified shape is:

```ts
import type { Middleware } from "openapi-fetch";

export function bearerAuth(token: string): Middleware {
  return {
    onRequest({ request }) {
      request.headers.set("Authorization", `Bearer ${token}`);
      return request;
    },
  };
}
```

`basicAuth` is the same with a base64 `Basic` credential. Use a cross-runtime base64: `btoa` exists in browsers, Workers, Deno, Bun and Node 20, whereas `Buffer` does not exist outside Node. Using `Buffer` here would break the package's primary target.

- [ ] **Step 4: Implement `index.ts`**

`createClient` builds an `openapi-fetch` client with `createClient<paths>({ baseUrl, fetch })`, registers the auth middleware via `client.use(...)`, and returns the server facade. Each facade method calls the raw client, and a shared helper converts `{ data, error }` into either `data` or a thrown `ArcadeDBError`.

Expose the raw client as `raw`. It stays vanilla: it returns `{ data, error }` and does NOT throw. That asymmetry is deliberate and is documented in Task 9's README.

`exists` returns the server's boolean and its doc comment must record that a `false` cannot distinguish "absent" from "not authorised for this caller".

- [ ] **Step 5: Run the tests, then add `test` to CI**

Confirm green, then add `npm test` to the CI job.

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: add error mapping, auth helpers, and the server-scoped client"
```

---

## Task 5: The data plane

**Context:** `query`, `command` and `transaction`. The transaction wrapper is the single strongest justification for having a facade at all, and it depends on the header modelling M0 shipped.

**Files:**
- Create: `src/facade/data.ts` and its unit tests
- Modify: `src/index.ts` to attach these to `ArcadeDBDatabase`

**Interfaces:**
- Consumes: `ArcadeDBError`, `createClient`, `ArcadeDBDatabase` from Task 4.
- Produces:
  ```ts
  type QueryEnvelope<T = unknown> = {
    result: T[]; limit: number; returned: number; truncated: boolean;
  };
  query<T>(opts: { language: "sql"|"cypher"|"gremlin"|"graphql"|"mongo"; command: string;
                   params?: Record<string, unknown> }): Promise<QueryEnvelope<T>>;
  command<T>(opts: same): Promise<QueryEnvelope<T>>;
  transaction<T>(fn: (tx: ArcadeDBDatabase) => Promise<T>): Promise<T>;
  ```
  Confirm the request-body property names against the generated `QueryRequest` and `CommandRequest`
  schemas rather than assuming; the generated file is authoritative.

- [ ] **Step 1: Write the failing tests first**

Against a mocked `fetch`, asserting on the requests actually issued:
- `query` returns the whole envelope, including `truncated`, and does not unwrap to `result`
- `transaction` issues `begin`, then the body's calls, then `commit`
- **every call inside the body carries the `arcadedb-session-id` header returned by begin**
- `transaction` issues `rollback`, not `commit`, when the body throws, and re-throws the original error
- the rollback happens even when the body throws synchronously
- a failing `commit` surfaces as an `ArcadeDBError`

The session-threading and rollback-on-throw tests are the ones that matter. Verify each fails before implementation, and for the rollback test confirm it fails because rollback was not called, not because the mock was misconfigured.

- [ ] **Step 2: Implement**

`begin` returns the session id in the `arcadedb-session-id` **response header** (openapi-fetch exposes the raw `Response`, so read it from there). Thread it as a request header on every call made through the handle passed to `fn`, and end with commit on return or rollback on throw, in a `finally`.

Note the transaction operations answer **204**, so there is no body to parse; treat a 204 as success rather than looking for JSON.

- [ ] **Step 3: Run tests, confirm green, commit**

```bash
git commit -m "feat: add query, command, and the transaction wrapper"
```

---

## Task 6: Time series and dashboard namespaces

**Context:** `ts`, `grafana` and `promql`. Mostly thin passthroughs; the PromQL one needs care because its result is a three-shape union.

**Files:**
- Create: `src/facade/timeseries.ts`, `src/facade/dashboards.ts` and their unit tests
- Modify: `src/index.ts`

**Interfaces:**
- Consumes: the same helpers as Task 5.
- Produces: `db.ts.write()`, `db.ts.query()`, `db.grafana.query()`, `db.promql.query()`,
  `db.promql.queryRange()`, `db.promql.labels()`, `db.promql.series()`.

- [ ] **Step 1: Read the generated types for these operations first**

The PromQL result is an `anyOf` over three shapes: an array of instant samples when `resultType` is `vector`, an array of range series when `matrix`, and a single `[timestamp, value]` pair when `scalar`. The time-series query response is a `oneOf` between an aggregated and a raw shape.

Read what `openapi-typescript` actually emitted for both before writing any narrowing code. Record the emitted type names in your report.

- [ ] **Step 2: Write failing tests**

For PromQL, one test per `resultType`, asserting the caller can narrow on `resultType` and reach the right shape without a cast. For time series, one test per branch of the `oneOf`.

- [ ] **Step 3: Implement**

Keep these thin. Expose the discriminator (`resultType`) rather than hiding it: the server tells the caller which shape it sent, and a facade that swallows that forces the caller to guess.

- [ ] **Step 4: Run tests, confirm green, commit**

```bash
git commit -m "feat: add the time series and dashboard namespaces"
```

---

## Task 7: The tree-shaking check

**Context:** An explicit acceptance criterion from the original issue: importing the data plane must not pull the PromQL and Grafana modules into a consumer's bundle.

**Files:**
- Create: `typescript/packages/client/test/treeshake.test.ts` and a fixture entry point
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the test**

A fixture entry imports only `createClient` and calls `query`. Bundle it with `esbuild` (a devDependency, never a runtime one) at production settings, then assert:
- the output does NOT contain a marker identifier unique to the PromQL module
- the output does NOT contain a marker identifier unique to the Grafana module
- the output is below a generous size ceiling

Choose markers that survive minification, for example a distinctive exported function name that appears as a property or string, and say in a comment why that marker was chosen. A marker that minification renames makes the assertion vacuously true.

- [ ] **Step 2: PROVE the test can fail**

Add `import { ... } from ".../promql"` and a call to the fixture, rebuild, and confirm the marker assertion goes RED. Then remove it and confirm green. Capture both outputs.

This step is not optional. A tree-shaking assertion that passes because the marker was never present in the first place is precisely the green-but-meaningless test that let a Critical defect through in M0.

- [ ] **Step 3: Wire into CI, then commit**

```bash
git commit -m "test: assert the data plane tree-shakes free of the dashboard modules"
```

---

## Task 8: End-to-end against a real server

**Context:** The first test that puts the generated types on a real wire.

**Files:**
- Create: `typescript/e2e/` suite and its config
- Modify: `typescript/package.json`, `.github/workflows/ci.yml`

- [ ] **Step 1: Stand up the container**

Testcontainers with a pinned published image. **`arcadedata/arcadedb:26.8.1` is correct here even though the contract is newer.** M0 changed only spec-generator classes; no handler changed, so the server always answered 204 and always used the session header. M0 made the documentation honest, and a client generated from the post-M0 contract works against a 26.8.1 server.

Do not generalise this. It holds only because this particular contract bump was a documentation fix. The moment a bump reflects a real wire change, the pinned e2e image must move with it.

Follow the pattern already used in `ArcadeData/arcadedb`'s `e2e-js`: a `GenericContainer` with `JAVA_OPTS` setting `arcadedb.server.rootPassword`, exposed port 2480, and a wait strategy polling `/api/v1/ready` for a 204.

- [ ] **Step 2: Write the suite**

Create a database, then: basic auth works; bearer auth works using a token minted by `POST /api/v1/login` (prefixed `AU-`); `command` inserts and `query` reads it back; a `transaction` commits and its writes are visible afterwards; a `transaction` whose body throws leaves no writes behind; `exists` and `listDatabases` agree with what was created.

The rollback case is the most valuable test in this suite, because it exercises session threading, the 204 handling and the `finally` in one path.

- [ ] **Step 3: Run, wire into CI, commit**

Give the e2e job a longer timeout than the unit job and run it as a separate CI job so a container failure is distinguishable from a unit failure at a glance.

```bash
git commit -m "test: exercise the client end to end against a real server"
```

---

## Task 9: Release workflow and README

**Context:** Makes the package publishable on demand. Nothing publishes automatically.

**Files:**
- Create: `.github/workflows/publish.yml`, `typescript/packages/client/README.md`, root `README.md`

- [ ] **Step 1: Write `publish.yml`**

`workflow_dispatch` only, with a version input. Steps: checkout at a pinned SHA, setup-node, `npm ci`, run the full test suite, verify the package's recorded `arcadedb.serverVersion` matches the committed contract's `info.version`, then publish with provenance. Grant `id-token: write` for OIDC.

- [ ] **Step 2: Record the two npm caveats in the workflow's comments**

npm's documentation does not state whether a trusted publisher can be configured for a package that does not yet exist, so the first publish may need a short-lived granular token before OIDC takes over. And npm does not validate the trusted-publisher configuration when it is saved, so the workflow filename in npm's settings must be checked against this file's actual name once, deliberately.

- [ ] **Step 3: Write the READMEs**

The package README must state: installation, a `createClient` example, the envelope return shape and **why `truncated` matters**, the `transaction` example, that `.raw` returns `{ data, error }` and does not throw while the facade throws, the `CONTRACT_VERSION` and which server release it was generated from, and a compatibility table.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: add the manual release workflow and package documentation"
```

---

## Done criteria

- [ ] `npm ci && npm run lint && npm run typecheck && npm test` green from `typescript/`.
- [ ] The drift gate has been observed FAILING on a hand-edited generated file, and passing after restore.
- [ ] `fetch-contract.sh` has been observed REFUSING the 26.8.1 image.
- [ ] The tree-shaking test has been observed FAILING with a PromQL import present.
- [ ] The e2e suite passes against a pinned published image, including the rollback case.
- [ ] Nothing has been published to npm.

## Deliberately not in this plan

- `@arcadedb/client-grpc` (M1b) and every non-TypeScript language (M3+).
- Automatic release-time publishing.
- A shared `client-core` package.
- The M2 smoke job, which lives in `ArcadeData/arcadedb` and depends on this repository's e2e suite existing first.
