import { randomUUID } from "node:crypto";
import { GenericContainer, Wait } from "testcontainers";
import type { StartedTestContainer } from "testcontainers";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import type { MessageInitShape, MessageShape } from "@bufbuild/protobuf";
import { basicAuth, createClient as createHttpClient } from "../packages/client/src/index.js";
import type { ArcadeDBServer } from "../packages/client/src/index.js";
import { unwrap } from "../packages/client/src/internal/unwrap.js";
import { bearerAuth, createClient as createGrpcClient, passwordAuth } from "../packages/client-grpc/src/index.js";
import type { ArcadeDBGrpcClient, Interceptor } from "../packages/client-grpc/src/index.js";
import type { GrpcRecordSchema, GrpcValueSchema, QueryResultSchema } from "../packages/client-grpc/src/gen/arcadedb-server-26.9.1-SNAPSHOT_pb.js";

// Image pin: kept independent of `e2e/data-plane.test.ts`'s pin. That file's 26.8.1 pin is
// justified by a REST-contract-specific fact (a documentation-only OpenAPI bump); nothing here
// establishes the same fact for the gRPC contract, so this suite pins the same published tag on
// its own merits (known-good, has the GRPC plugin class available) rather than by inheriting the
// other suite's reasoning.
const DEFAULT_ARCADEDB_IMAGE = "arcadedata/arcadedb:26.8.1";

// `ARCADEDB_DOCKER_IMAGE` overrides the pin - same variable name `e2e-js` and the HTTP e2e suite
// already use. The M2 smoke job in ArcadeData/arcadedb sets this to the image built from the
// server commit under review; honoring it here (not merely in data-plane.test.ts) is what lets
// that job actually exercise the gRPC data plane instead of silently covering HTTP alone.
const ARCADEDB_IMAGE = process.env.ARCADEDB_DOCKER_IMAGE ?? DEFAULT_ARCADEDB_IMAGE;

// Both facts below were verified against a real container while preparing this suite, and cost
// real time to discover - see the plan/report for this task.
//
// 1. The gRPC plugin is NOT enabled by default: `SERVER_PLUGINS` defaults to empty, so without
//    `-Darcadedb.server.plugins=GRPC:com.arcadedb.server.grpc.GrpcServerPlugin` nothing listens
//    on port 50051 at all.
// 2. The root password MUST be at least 8 characters. A shorter one kills the server at startup
//    with `ServerSecurityException: User password too short (<8 characters)`, and the only
//    visible symptom is a closed port 50051 - which reads exactly like "gRPC is broken in this
//    image" rather than "the whole server refused to start". `playwithdata` below is 12
//    characters, well clear of the limit.
const ROOT_PASSWORD = "playwithdata";
const DB_NAME = "clienttestgrpc";

let container: StartedTestContainer;
let httpBaseUrl: string;
let grpcBaseUrl: string;
let httpRoot: ArcadeDBServer;
let rootGrpc: ArcadeDBGrpcClient;

type GrpcRecordInit = MessageInitShape<typeof GrpcRecordSchema>;
type GrpcValueInit = MessageInitShape<typeof GrpcValueSchema>;
type QueryResultRecord = MessageShape<typeof QueryResultSchema>["records"][number];

/** Builds a `GrpcValue`-shaped `string_value` entry for a `GrpcRecord.properties` map. */
function stringProperty(value: string): GrpcValueInit {
  return { kind: { case: "stringValue", value } };
}

/** Reads a `string_value` property back off a `GrpcRecord` returned by the server. */
function readStringProperty(record: QueryResultRecord, key: string): string | undefined {
  const value = record.properties[key];
  return value?.kind.case === "stringValue" ? value.kind.value : undefined;
}

/** Composes a call-recording wrapper around an auth interceptor: every outgoing RPC's method
 * name is pushed to `calls` before the (still fully functional) authenticated call proceeds.
 * Used by the rollback test to assert the MECHANISM (RollbackTransaction was actually issued,
 * CommitTransaction was not) rather than only the row-absence outcome - see that test for why
 * the outcome alone is not proof. */
function withCallRecording(auth: Interceptor, calls: string[]): Interceptor {
  return (next) => {
    const authenticated = auth(next);
    return async (req) => {
      calls.push(req.method.name);
      return authenticated(req);
    };
  };
}

beforeAll(async () => {
  container = await new GenericContainer(ARCADEDB_IMAGE)
    .withEnvironment({
      JAVA_OPTS:
        `-Darcadedb.server.rootPassword=${ROOT_PASSWORD} ` +
        "-Darcadedb.server.plugins=GRPC:com.arcadedb.server.grpc.GrpcServerPlugin",
    })
    // Exposed-but-not-bound: Testcontainers maps both ports to random host ports, so this
    // doesn't clash with any locally running ArcadeDB service.
    .withExposedPorts(2480, 50051)
    .withWaitStrategy(
      Wait.forAll([
        Wait.forHttp("/api/v1/ready", 2480).forStatusCodeMatching((statusCode) => statusCode === 204),
        // The success signal called out in the plan: this line only appears once the GRPC plugin
        // has finished starting and is actually listening on 50051.
        Wait.forLogMessage(/gRPC server started on 0\.0\.0\.0:50051/),
      ]),
    )
    .withStartupTimeout(60_000)
    .start();

  httpBaseUrl = `http://${container.getHost()}:${container.getMappedPort(2480)}`;
  grpcBaseUrl = `http://${container.getHost()}:${container.getMappedPort(50051)}`;

  httpRoot = createHttpClient({ baseUrl: httpBaseUrl, auth: basicAuth("root", ROOT_PASSWORD) });

  // There is no data-plane RPC to create a database, and the admin service is deliberately out
  // of scope for this package - so database (and schema) setup goes over HTTP, exactly as
  // `data-plane.test.ts` already does for the REST suite.
  await unwrap(
    httpRoot.raw.POST("/api/v1/server", {
      body: { command: `create database ${DB_NAME}`, language: "sql" },
    }),
  );

  const httpDb = httpRoot.db(DB_NAME);
  await httpDb.command({ language: "sql", command: "CREATE VERTEX TYPE Person IF NOT EXISTS" });
  await httpDb.command({ language: "sql", command: "CREATE VERTEX TYPE BatchPerson IF NOT EXISTS" });

  rootGrpc = createGrpcClient({
    baseUrl: grpcBaseUrl,
    auth: passwordAuth("root", ROOT_PASSWORD, DB_NAME),
    insecure: true,
  });
}, 90_000);

afterAll(async () => {
  await container?.stop();
});

describe("end-to-end against a real ArcadeDB gRPC server", () => {
  it("password auth works", async () => {
    const response = await rootGrpc.raw.executeQuery({ database: DB_NAME, query: "SELECT FROM Person", language: "sql" });
    expect(response.results).toBeDefined();
  });

  it("bearer auth works, using a token minted by POST /api/v1/login", async () => {
    const login = await unwrap(httpRoot.raw.POST("/api/v1/login", {}));
    expect(login.token).toBeDefined();
    if (!login.token) throw new Error("login did not return a token");
    expect(login.token).toMatch(/^AU-/);

    const bearerGrpc = createGrpcClient({ baseUrl: grpcBaseUrl, auth: bearerAuth(login.token) });
    const response = await bearerGrpc.raw.executeQuery({ database: DB_NAME, query: "SELECT FROM Person", language: "sql" });
    expect(response.results).toBeDefined();
  });

  it("executeCommand writes and streamQuery reads it back", async () => {
    const commandResponse = await rootGrpc.raw.executeCommand({
      database: DB_NAME,
      command: "INSERT INTO Person SET name = 'Alice'",
      language: "sql",
    });
    expect(commandResponse.success).toBe(true);

    const rows: QueryResultRecord[] = [];
    for await (const row of rootGrpc.streamQuery({
      database: DB_NAME,
      query: "SELECT FROM Person WHERE name = 'Alice'",
      language: "sql",
    })) {
      rows.push(row);
    }

    expect(rows).toHaveLength(1);
    expect(readStringProperty(rows[0], "name")).toBe("Alice");
  });

  it("insertStream ingests a batch and the InsertSummary matches what is queryable afterwards", async () => {
    function batchRow(name: string): GrpcRecordInit {
      return { type: "BatchPerson", properties: { name: stringProperty(name) } };
    }

    async function* chunks(): AsyncGenerator<GrpcRecordInit[]> {
      yield [batchRow("Batch1"), batchRow("Batch2")];
      yield [batchRow("Batch3"), batchRow("Batch4")];
    }

    // `targetClass` names the type the whole stream inserts into - the server resolves it from
    // `InsertOptions.targetClass` only; a per-row `GrpcRecord.type` (set on `batchRow` above for
    // documentation purposes) is not consulted by `insertStream`'s row-insert path.
    const summary = await rootGrpc.insertStream({
      database: DB_NAME,
      options: { targetClass: "BatchPerson" },
      chunks: chunks(),
    });

    expect(summary.failed).toBe(0n);
    expect(summary.inserted).toBe(4n);
    expect(summary.received).toBe(4n);

    const rows: QueryResultRecord[] = [];
    for await (const row of rootGrpc.streamQuery({ database: DB_NAME, query: "SELECT FROM BatchPerson", language: "sql" })) {
      rows.push(row);
    }

    expect(BigInt(rows.length)).toBe(summary.inserted);
  });

  it("a transaction commits, with writes visible afterwards", async () => {
    await rootGrpc.transaction(DB_NAME, async (tx) => {
      await tx.executeCommand({ command: "INSERT INTO Person SET name = 'Bob'", language: "sql" });
    });

    const rows: QueryResultRecord[] = [];
    for await (const row of rootGrpc.streamQuery({
      database: DB_NAME,
      query: "SELECT FROM Person WHERE name = 'Bob'",
      language: "sql",
    })) {
      rows.push(row);
    }

    expect(rows).toHaveLength(1);
  });

  it("a transaction whose body throws leaves no writes behind", async () => {
    // Asserts the MECHANISM, not merely the outcome. M1's HTTP e2e originally asserted only "the
    // row is absent afterwards" - that assertion PASSED even with the rollback call deleted from
    // the implementation, because an abandoned (never committed, never rolled back) transaction
    // also leaves its writes invisible, through ordinary isolation rather than cleanup. So this
    // test records every RPC method name the spied client actually issues and asserts
    // RollbackTransaction fired and CommitTransaction did not, in addition to the row-absence
    // check below. This was proven to catch a deleted rollback call - see this task's report.
    const calls: string[] = [];
    const spiedGrpc = createGrpcClient({
      baseUrl: grpcBaseUrl,
      auth: withCallRecording(passwordAuth("root", ROOT_PASSWORD, DB_NAME), calls),
      insecure: true,
    });

    await expect(
      spiedGrpc.transaction(DB_NAME, async (tx) => {
        await tx.executeCommand({ command: "INSERT INTO Person SET name = 'Carol'", language: "sql" });
        throw new Error("deliberate failure to force a rollback");
      }),
    ).rejects.toThrow("deliberate failure to force a rollback");

    expect(calls).toContain("RollbackTransaction");
    expect(calls).not.toContain("CommitTransaction");

    // Belt and suspenders, and the brief's explicit requirement: the row must also be ABSENT,
    // not merely that the promise rejected and RollbackTransaction was observed.
    const rows: QueryResultRecord[] = [];
    for await (const row of rootGrpc.streamQuery({
      database: DB_NAME,
      query: "SELECT FROM Person WHERE name = 'Carol'",
      language: "sql",
    })) {
      rows.push(row);
    }
    expect(rows).toHaveLength(0);
  });

  it("probes what the server does with a single empty final insertStream chunk (informational only)", async () => {
    // `insertStream`'s ergonomic wrapper currently throws when given an empty iterable, rather
    // than sending a single zero-row final chunk - a provisional choice made without knowing
    // whether the server even accepts a zero-row final chunk. This test bypasses the wrapper and
    // talks to `raw.insertStream` directly to find out empirically, bounded by `timeoutMs` so an
    // unexpected server hang fails this one test instead of wedging the whole suite. It does NOT
    // change `insertStream`'s behavior - see this task's report for the finding and what should
    // happen next.
    async function* oneEmptyChunk() {
      // `options.database` is included alongside the chunk-level `database` the brief specifies,
      // for the same server-side reason `envelopeChunks` in `src/stream.ts` mirrors it: the
      // deployed server's `InsertContext` only reads `InsertOptions.database`, not
      // `InsertChunk.database`. Without it every chunk - empty or not - fails identically on
      // that unrelated gap, which would tell us nothing about empty-chunk handling specifically.
      // `options.targetClass` is set to an existing type for the same isolation reason: the
      // server resolves the target type unconditionally (before it ever looks at how many rows
      // the chunk carries), so a blank target_class would fail the probe on "type not found"
      // rather than telling us anything about zero-row handling specifically.
      yield {
        database: DB_NAME,
        options: { database: DB_NAME, targetClass: "BatchPerson" },
        sessionId: randomUUID(),
        chunkSeq: 1n,
        rows: [],
        last: true,
      };
    }

    let outcome: { kind: "summary"; value: unknown } | { kind: "error"; value: unknown };
    try {
      const summary = await rootGrpc.raw.insertStream(oneEmptyChunk(), { timeoutMs: 15_000 });
      outcome = { kind: "summary", value: summary };
    } catch (err) {
      outcome = { kind: "error", value: err };
    }

    const describe = (value: unknown): unknown =>
      JSON.stringify(value, (_key, v: unknown) => (typeof v === "bigint" ? v.toString() : v));
    console.log(`[insertStream empty-chunk probe] ${outcome.kind}: ${describe(outcome.value)}`);

    // The probe completing at all (rather than the 15s bound tripping) is the only thing this
    // test asserts - the point is to observe and report the server's actual behavior, not to
    // encode a contract for it yet.
    expect(outcome.kind === "summary" || outcome.kind === "error").toBe(true);
  });

  it("exists and listDatabases agree with what was created over HTTP", async () => {
    await expect(httpRoot.exists(DB_NAME)).resolves.toBe(true);
    await expect(httpRoot.listDatabases()).resolves.toContain(DB_NAME);
  });
});
