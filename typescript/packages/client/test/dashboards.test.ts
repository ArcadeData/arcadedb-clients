import { describe, expect, it, vi } from "vitest";
import { createClient } from "../src/index.js";

function jsonResponse(body: unknown, status: number, extraHeaders: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...extraHeaders },
  });
}

describe("db.grafana.query", () => {
  it("POSTs targets to /api/v1/ts/{database}/grafana/query and returns results keyed by refId", async () => {
    let capturedBody: unknown;
    const fetchMock = vi.fn(async (request: Request) => {
      capturedBody = await request.clone().json();
      return jsonResponse(
        { results: { A: { frames: [{ schema: { fields: [{ name: "time", type: "time" }] }, data: { values: [[1700000000]] } }] } } },
        200,
      );
    });
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    const response = await server.db("mydb").grafana.query({ targets: [{ refId: "A", type: "cpu" }] });

    expect(new URL(fetchMock.mock.calls[0][0].url).pathname).toBe("/api/v1/ts/mydb/grafana/query");
    expect(capturedBody).toEqual({ targets: [{ refId: "A", type: "cpu" }] });
    expect(response.results?.A?.frames?.[0]?.data?.values).toEqual([[1700000000]]);
  });
});

describe("db.promql.query", () => {
  it("narrows to instant samples, without a cast, when resultType is vector", async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse(
        { status: "success", data: { resultType: "vector", result: [{ metric: { __name__: "up" }, value: [1700000000, "1"] }] } },
        200,
      ),
    );
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    const response = await server.db("mydb").promql.query({ query: "up" });
    const data = response.data;

    if (data !== undefined && data.resultType === "vector") {
      // No cast: `data.result` is typed as `PromQLVectorSample[]` here purely from the
      // `resultType === "vector"` narrowing.
      expect(data.result[0].metric).toEqual({ __name__: "up" });
      expect(data.result[0].value).toEqual([1700000000, "1"]);
    } else {
      throw new Error("expected the vector branch");
    }
  });

  it("narrows to range series, without a cast, when resultType is matrix", async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse(
        {
          status: "success",
          data: {
            resultType: "matrix",
            result: [{ metric: { __name__: "up" }, values: [[1700000000, "1"], [1700000060, "1"]] }],
          },
        },
        200,
      ),
    );
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    const response = await server.db("mydb").promql.queryRange({ query: "up", start: "0", end: "60", step: "60" });
    const data = response.data;

    if (data !== undefined && data.resultType === "matrix") {
      // No cast: `data.result` is typed as `PromQLMatrixSeries[]` here purely from the
      // `resultType === "matrix"` narrowing.
      expect(data.result[0].metric).toEqual({ __name__: "up" });
      expect(data.result[0].values).toEqual([[1700000000, "1"], [1700000060, "1"]]);
    } else {
      throw new Error("expected the matrix branch");
    }
  });

  it("narrows to a single [timestamp, value] pair, without a cast, when resultType is scalar", async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ status: "success", data: { resultType: "scalar", result: [1700000000, "42"] } }, 200));
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    const response = await server.db("mydb").promql.query({ query: "scalar(up)" });
    const data = response.data;

    if (data !== undefined && data.resultType === "scalar") {
      // No cast: `data.result` is typed as `unknown[]` here purely from the
      // `resultType === "scalar"` narrowing.
      expect(data.result).toEqual([1700000000, "42"]);
    } else {
      throw new Error("expected the scalar branch");
    }
  });

  it("sends query, time and lookback_delta as query parameters", async () => {
    let capturedUrl: URL | undefined;
    const fetchMock = vi.fn(async (request: Request) => {
      capturedUrl = new URL(request.url);
      return jsonResponse({ status: "success", data: { resultType: "vector", result: [] } }, 200);
    });
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    await server.db("mydb").promql.query({ query: "up", time: "1700000000", lookback_delta: "5m" });

    expect(capturedUrl?.pathname).toBe("/api/v1/ts/mydb/prom/api/v1/query");
    expect(capturedUrl?.searchParams.get("query")).toBe("up");
    expect(capturedUrl?.searchParams.get("time")).toBe("1700000000");
    expect(capturedUrl?.searchParams.get("lookback_delta")).toBe("5m");
  });
});

describe("db.promql.labels", () => {
  it("GETs /api/v1/ts/{database}/prom/api/v1/labels and returns sorted label names", async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ status: "success", data: ["__name__", "host"] }, 200));
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    const response = await server.db("mydb").promql.labels();

    expect(new URL(fetchMock.mock.calls[0][0].url).pathname).toBe("/api/v1/ts/mydb/prom/api/v1/labels");
    expect(response.data).toEqual(["__name__", "host"]);
  });
});

describe("db.promql.series", () => {
  it("GETs /api/v1/ts/{database}/prom/api/v1/series with repeated match[] parameters", async () => {
    let capturedUrl: URL | undefined;
    const fetchMock = vi.fn(async (request: Request) => {
      capturedUrl = new URL(request.url);
      return jsonResponse({ status: "success", data: [{ __name__: "up", host: "a" }] }, 200);
    });
    const server = createClient({ baseUrl: "https://example.com", fetch: fetchMock as unknown as typeof fetch });

    const response = await server.db("mydb").promql.series({ "match[]": ["up", "cpu"] });

    expect(capturedUrl?.pathname).toBe("/api/v1/ts/mydb/prom/api/v1/series");
    expect(capturedUrl?.searchParams.getAll("match[]")).toEqual(["up", "cpu"]);
    expect(response.data).toEqual([{ __name__: "up", host: "a" }]);
  });
});
