import { describe, expect, it, vi } from "vitest";
import { ArcadeDBError, basicAuth, bearerAuth, createClient } from "../src/index.js";

function jsonResponse(body: unknown, status: number, extraHeaders: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...extraHeaders },
  });
}

function textResponse(body: string, status: number): Response {
  return new Response(body, { status, headers: { "content-type": "text/plain" } });
}

describe("createClient / ArcadeDBServer", () => {
  it("maps a 404 JSON error body to ArcadeDBError carrying status, error, exception, detail, requestId", async () => {
    const fetchMock = vi.fn(
      async () =>
        jsonResponse(
          {
            error: "Database not found",
            exception: "com.arcadedb.exception.DatabaseOperationException",
            detail: "Database 'foo' was not found",
          },
          404,
          { "X-Request-Id": "req-999" },
        ),
    );
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    let caught: unknown;
    try {
      await server.listDatabases();
    } catch (err) {
      caught = err;
    }

    expect(caught).toBeInstanceOf(ArcadeDBError);
    const err = caught as ArcadeDBError;
    expect(err.status).toBe(404);
    expect(err.error).toBe("Database not found");
    expect(err.exception).toBe("com.arcadedb.exception.DatabaseOperationException");
    expect(err.detail).toBe("Database 'foo' was not found");
    expect(err.requestId).toBe("req-999");
  });

  it("maps a non-2xx non-JSON body to ArcadeDBError with the right status, without itself throwing a parse error", async () => {
    const fetchMock = vi.fn(async () => textResponse("Bad Gateway from upstream proxy", 502));
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    let caught: unknown;
    try {
      await server.listDatabases();
    } catch (err) {
      caught = err;
    }

    expect(caught).toBeInstanceOf(ArcadeDBError);
    expect((caught as ArcadeDBError).status).toBe(502);
    expect((caught as ArcadeDBError).name).toBe("ArcadeDBError");
  });

  it("exists() returns the server's boolean, both true and false", async () => {
    const fetchTrue = vi.fn(async () => jsonResponse({ result: true }, 200));
    const serverTrue = createClient({ baseUrl: "https://example.com", fetch: fetchTrue as unknown as typeof fetch });
    await expect(serverTrue.exists("mydb")).resolves.toBe(true);

    const fetchFalse = vi.fn(async () => jsonResponse({ result: false }, 200));
    const serverFalse = createClient({
      baseUrl: "https://example.com",
      fetch: fetchFalse as unknown as typeof fetch,
    });
    await expect(serverFalse.exists("mydb")).resolves.toBe(false);
  });

  it("listDatabases() returns the server's list of names", async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ result: ["db1", "db2"] }, 200));
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });
    await expect(server.listDatabases()).resolves.toEqual(["db1", "db2"]);
  });

  it("health() resolves on 204 and throws ArcadeDBError otherwise", async () => {
    const fetchOk = vi.fn(async () => new Response(null, { status: 204 }));
    const serverOk = createClient({ baseUrl: "https://example.com", fetch: fetchOk as unknown as typeof fetch });
    await expect(serverOk.health()).resolves.toBeUndefined();

    const fetchDown = vi.fn(async () => textResponse("down", 503));
    const serverDown = createClient({ baseUrl: "https://example.com", fetch: fetchDown as unknown as typeof fetch });
    await expect(serverDown.health()).rejects.toBeInstanceOf(ArcadeDBError);
  });

  it("ready() resolves true on 204, false on 503, and throws ArcadeDBError on other failures", async () => {
    const fetchReady = vi.fn(async () => new Response(null, { status: 204 }));
    await expect(
      createClient({ baseUrl: "https://example.com", fetch: fetchReady as unknown as typeof fetch }).ready(),
    ).resolves.toBe(true);

    const fetchNotReady = vi.fn(async () => new Response(null, { status: 503 }));
    await expect(
      createClient({ baseUrl: "https://example.com", fetch: fetchNotReady as unknown as typeof fetch }).ready(),
    ).resolves.toBe(false);

    const fetchBroken = vi.fn(async () => textResponse("server error", 500));
    await expect(
      createClient({ baseUrl: "https://example.com", fetch: fetchBroken as unknown as typeof fetch }).ready(),
    ).rejects.toBeInstanceOf(ArcadeDBError);
  });

  it("db() returns an ArcadeDBDatabase carrying the given name", () => {
    const server = createClient({ baseUrl: "https://example.com", fetch: vi.fn() as unknown as typeof fetch });
    const db = server.db("mydb");
    expect(db.name).toBe("mydb");
  });

  it("raw is the unwrapped client: it returns {data, error} and does not throw", async () => {
    const fetchMock = vi.fn(async () => textResponse("boom", 500));
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    const { data, error } = await server.raw.GET("/api/v1/databases", {});
    expect(data).toBeUndefined();
    expect(error).toBeDefined();
  });

  it("registers basicAuth middleware supplied to createClient", async () => {
    let capturedAuthHeader: string | null = null;
    const fetchMock = vi.fn(async (request: Request) => {
      capturedAuthHeader = request.headers.get("Authorization");
      return jsonResponse({ result: [] }, 200);
    });
    const server = createClient({
      baseUrl: "https://example.com",
      auth: basicAuth("root", "playwithdata"),
      fetch: fetchMock as unknown as typeof fetch,
    });

    await server.listDatabases();
    expect(capturedAuthHeader).toBe(`Basic ${btoa("root:playwithdata")}`);
  });

  it("registers bearerAuth middleware supplied to createClient", async () => {
    let capturedAuthHeader: string | null = null;
    const fetchMock = vi.fn(async (request: Request) => {
      capturedAuthHeader = request.headers.get("Authorization");
      return jsonResponse({ result: [] }, 200);
    });
    const server = createClient({
      baseUrl: "https://example.com",
      auth: bearerAuth("AU-xyz"),
      fetch: fetchMock as unknown as typeof fetch,
    });

    await server.listDatabases();
    expect(capturedAuthHeader).toBe("Bearer AU-xyz");
  });
});
