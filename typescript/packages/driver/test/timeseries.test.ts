import { describe, expect, it, vi } from "vitest";
import { createClient } from "../src/index.js";

function jsonResponse(body: unknown, status: number, extraHeaders: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...extraHeaders },
  });
}

function noContent(status = 204, extraHeaders: Record<string, string> = {}): Response {
  return new Response(null, { status, headers: extraHeaders });
}

describe("db.ts.write", () => {
  it("POSTs the line protocol body as text/plain, not JSON, to /api/v1/ts/{database}/write", async () => {
    let capturedRequest: Request | undefined;
    const fetchMock = vi.fn(async (request: Request) => {
      capturedRequest = request;
      return noContent();
    });
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    await server.db("mydb").ts.write({ lineProtocol: "cpu,host=a value=1 1700000000000000000" });

    expect(capturedRequest?.method).toBe("POST");
    expect(new URL(capturedRequest!.url).pathname).toBe("/api/v1/ts/mydb/write");
    expect(capturedRequest?.headers.get("content-type")).toBe("text/plain");
    await expect(capturedRequest!.clone().text()).resolves.toBe("cpu,host=a value=1 1700000000000000000");
  });

  it("sends precision as a query parameter when supplied", async () => {
    let capturedRequest: Request | undefined;
    const fetchMock = vi.fn(async (request: Request) => {
      capturedRequest = request;
      return noContent();
    });
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    await server.db("mydb").ts.write({ lineProtocol: "cpu value=1 1700000000", precision: "s" });

    expect(new URL(capturedRequest!.url).searchParams.get("precision")).toBe("s");
  });
});

describe("db.ts.query", () => {
  it("narrows to the raw shape via the `rows` property, without a cast, when the response carries rows", async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse({ type: "cpu", columns: ["time", "value"], count: 1, rows: [[1700000000, 42]] }, 200),
    );
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    const result = await server.db("mydb").ts.query({ type: "cpu" });

    if ("rows" in result) {
      expect(result.rows).toEqual([[1700000000, 42]]);
      expect(result.columns).toEqual(["time", "value"]);
    } else {
      throw new Error("expected the raw (rows) branch, got the aggregated branch");
    }
  });

  it("narrows to the aggregated shape via the `buckets` property, without a cast, when the response carries buckets", async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse(
        { type: "cpu", aggregations: ["value_avg"], count: 1, buckets: [{ timestamp: 1700000000, values: [21] }] },
        200,
      ),
    );
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    const result = await server.db("mydb").ts.query({
      type: "cpu",
      aggregation: { bucketInterval: 60, requests: [{ field: "value", type: "AVG" }] },
    });

    if ("buckets" in result) {
      expect(result.buckets).toEqual([{ timestamp: 1700000000, values: [21] }]);
      expect(result.aggregations).toEqual(["value_avg"]);
    } else {
      throw new Error("expected the aggregated (buckets) branch, got the raw branch");
    }
  });

  it("POSTs the query definition as JSON to /api/v1/ts/{database}/query", async () => {
    let capturedRequest: Request | undefined;
    let capturedBody: unknown;
    const fetchMock = vi.fn(async (request: Request) => {
      capturedRequest = request;
      capturedBody = await request.clone().json();
      return jsonResponse({ type: "cpu", columns: [], count: 0, rows: [] }, 200);
    });
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    await server.db("mydb").ts.query({ type: "cpu", from: 1, to: 2 });

    expect(capturedRequest?.method).toBe("POST");
    expect(new URL(capturedRequest!.url).pathname).toBe("/api/v1/ts/mydb/query");
    expect(capturedBody).toEqual({ type: "cpu", from: 1, to: 2 });
  });
});
