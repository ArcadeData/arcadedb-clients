import { GenericContainer, Wait } from "testcontainers";
import type { StartedTestContainer } from "testcontainers";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { basicAuth, bearerAuth, createClient } from "../packages/client/src/index.js";
import type { ArcadeDBServer } from "../packages/client/src/index.js";
import { unwrap } from "../packages/client/src/internal/unwrap.js";

// Image pin: `arcadedata/arcadedb:26.8.1` is correct here even though the OpenAPI contract this
// client is generated from is newer (26.9.1-SNAPSHOT). The upstream fixes the newer contract
// carries changed only spec-generator classes (M0) - no request handler changed. The server has
// always answered 204 on the transaction endpoints and has always used the
// `arcadedb-session-id` header; the spec was simply wrong about it. `CommandRequest.language` was
// the same story: the contract now marks it required (upstream fix #6562), and the 26.8.1 SERVER
// already required it too - the spec previously omitted a field the server always demanded. So a
// client generated from the newer contract works unmodified against a 26.8.1 server.
//
// DO NOT GENERALISE THIS. It holds only because this particular contract bump was a
// documentation fix. The moment a contract bump reflects a real wire change, this pin must move
// with it.
const ARCADEDB_IMAGE = "arcadedata/arcadedb:26.8.1";

const ROOT_PASSWORD = "playwithdata";
const DB_NAME = "clienttest";

let container: StartedTestContainer;
let rootServer: ArcadeDBServer;
let baseUrl: string;

beforeAll(async () => {
  container = await new GenericContainer(ARCADEDB_IMAGE)
    .withEnvironment({ JAVA_OPTS: `-Darcadedb.server.rootPassword=${ROOT_PASSWORD}` })
    // Exposed-but-not-bound: Testcontainers maps 2480 to a random host port. This machine already
    // has an ArcadeDB service listening on host port 2480, so binding directly would clash.
    .withExposedPorts(2480)
    .withWaitStrategy(Wait.forHttp("/api/v1/ready", 2480).forStatusCodeMatching((statusCode) => statusCode === 204))
    .withStartupTimeout(60_000)
    .start();

  baseUrl = `http://${container.getHost()}:${container.getMappedPort(2480)}`;
  rootServer = createClient({ baseUrl, auth: basicAuth("root", ROOT_PASSWORD) });

  // No dedicated "create database" REST endpoint exists; database creation goes through the
  // generic server-command endpoint (POST /api/v1/server, body { command, language }), the same
  // one root-only administrative commands (drop database, create user, ...) share.
  await unwrap(
    rootServer.raw.POST("/api/v1/server", {
      body: { command: `create database ${DB_NAME}`, language: "sql" },
    }),
  );

  await rootServer.db(DB_NAME).command({ language: "sql", command: "CREATE VERTEX TYPE Person IF NOT EXISTS" });
}, 90_000);

afterAll(async () => {
  await container?.stop();
});

describe("end-to-end against a real ArcadeDB server", () => {
  it("basic auth works", async () => {
    await expect(rootServer.exists(DB_NAME)).resolves.toBe(true);
  });

  it("bearer auth works, using a token minted by POST /api/v1/login", async () => {
    const login = await unwrap(rootServer.raw.POST("/api/v1/login", {}));
    expect(login.token).toBeDefined();
    if (!login.token) throw new Error("login did not return a token");
    expect(login.token).toMatch(/^AU-/);

    const bearerServer = createClient({ baseUrl, auth: bearerAuth(login.token) });
    await expect(bearerServer.exists(DB_NAME)).resolves.toBe(true);
  });

  it("command inserts and query reads it back", async () => {
    const db = rootServer.db(DB_NAME);

    await db.command({ language: "sql", command: "INSERT INTO Person SET name = 'Alice'" });

    const envelope = await db.query<{ name: string }>({
      language: "sql",
      command: "SELECT FROM Person WHERE name = 'Alice'",
    });

    expect(envelope.result).toHaveLength(1);
    expect(envelope.result[0].name).toBe("Alice");
  });

  it("a transaction commits and its writes are visible afterwards", async () => {
    const db = rootServer.db(DB_NAME);

    await db.transaction(async (tx) => {
      await tx.command({ language: "sql", command: "INSERT INTO Person SET name = 'Bob'" });
    });

    const envelope = await db.query({ language: "sql", command: "SELECT FROM Person WHERE name = 'Bob'" });
    expect(envelope.result).toHaveLength(1);
  });

  it("a transaction whose body throws leaves no writes behind", async () => {
    // Wraps the real fetch to record which endpoints were actually hit, while every request still
    // goes to the live container. This is needed because absence of the row alone is not proof of
    // a correct rollback: an abandoned session that is never committed OR rolled back also leaves
    // the write invisible (ordinary transactional isolation), so that assertion by itself cannot
    // tell "rolled back" apart from "leaked". Confirmed by temporarily deleting the
    // `rollbackTransaction` call from `ArcadeDBDatabase.transaction` - the row-absence-only version
    // of this test still passed, for the wrong reason.
    const calls: { path: string; status: number }[] = [];
    const spiedServer = createClient({
      baseUrl,
      auth: basicAuth("root", ROOT_PASSWORD),
      fetch: async (request) => {
        const response = await fetch(request);
        calls.push({ path: new URL(request.url).pathname, status: response.status });
        return response;
      },
    });
    const db = spiedServer.db(DB_NAME);

    await expect(
      db.transaction(async (tx) => {
        await tx.command({ language: "sql", command: "INSERT INTO Person SET name = 'Carol'" });
        throw new Error("deliberate failure to force a rollback");
      }),
    ).rejects.toThrow("deliberate failure to force a rollback");

    const rollbackCall = calls.find((c) => c.path === `/api/v1/rollback/${DB_NAME}`);
    expect(rollbackCall).toBeDefined();
    expect(rollbackCall?.status).toBe(204);
    expect(calls.some((c) => c.path === `/api/v1/commit/${DB_NAME}`)).toBe(false);

    // Belt and suspenders, and the brief's explicit requirement: the row must also be ABSENT, not
    // merely that the promise rejected and rollback was called.
    const envelope = await db.query({ language: "sql", command: "SELECT FROM Person WHERE name = 'Carol'" });
    expect(envelope.result).toHaveLength(0);
  });

  it("exists and listDatabases agree with what was created", async () => {
    await expect(rootServer.exists(DB_NAME)).resolves.toBe(true);
    await expect(rootServer.listDatabases()).resolves.toContain(DB_NAME);
  });
});
