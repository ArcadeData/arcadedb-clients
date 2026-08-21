import { describe, expect, it } from "vitest";
import type { MiddlewareCallbackParams } from "openapi-fetch";
import { basicAuth, bearerAuth } from "../src/auth.js";

/** Builds the params object openapi-fetch passes to `onRequest`. */
function callbackParams(request: Request): MiddlewareCallbackParams {
  return {
    request,
    schemaPath: "/test",
    params: {},
    id: "test-id",
    options: {
      baseUrl: "https://example.com",
      parseAs: "json",
      querySerializer: () => "",
      bodySerializer: (body: unknown) => JSON.stringify(body),
      pathSerializer: (pathname: string) => pathname,
      fetch: globalThis.fetch,
    },
  };
}

describe("basicAuth", () => {
  it("sets an Authorization: Basic header with the base64 of user:password", () => {
    const middleware = basicAuth("root", "playwithdata");
    const request = new Request("https://example.com/api/v1/databases");

    const result = middleware.onRequest?.(callbackParams(request));
    const finalRequest = (result ?? request) as Request;

    expect(finalRequest.headers.get("Authorization")).toBe(`Basic ${btoa("root:playwithdata")}`);
  });

  it("does not depend on Buffer: still works when Buffer is unavailable on globalThis", () => {
    // Buffer is Node-only and absent in browsers, Cloudflare Workers, and Deno -
    // this package's primary targets. A `Buffer.from(...).toString("base64")`
    // implementation would throw `ReferenceError: Buffer is not defined` the
    // moment Buffer is removed from globalThis, which is exactly what this test
    // simulates. `btoa` is available in every one of those runtimes, so the
    // correct implementation keeps working here.
    const globalWithBuffer = globalThis as { Buffer?: unknown };
    const originalBuffer = globalWithBuffer.Buffer;
    expect(originalBuffer).toBeDefined(); // sanity check: Buffer really was present in this Node test run

    delete globalWithBuffer.Buffer;
    try {
      const middleware = basicAuth("root", "playwithdata");
      const request = new Request("https://example.com/api/v1/databases");

      const result = middleware.onRequest?.(callbackParams(request));
      const finalRequest = (result ?? request) as Request;

      expect(finalRequest.headers.get("Authorization")).toBe(`Basic ${btoa("root:playwithdata")}`);
    } finally {
      globalWithBuffer.Buffer = originalBuffer;
    }
  });

  it("encodes special characters in the credential the same way btoa does", () => {
    const middleware = basicAuth("user@example.com", "p@ss:word!");
    const request = new Request("https://example.com/api/v1/databases");

    const result = middleware.onRequest?.(callbackParams(request));
    const finalRequest = (result ?? request) as Request;

    expect(finalRequest.headers.get("Authorization")).toBe(`Basic ${btoa("user@example.com:p@ss:word!")}`);
  });
});

describe("bearerAuth", () => {
  it("sets an Authorization: Bearer header with the raw token", () => {
    const middleware = bearerAuth("AU-abc123");
    const request = new Request("https://example.com/api/v1/databases");

    const result = middleware.onRequest?.(callbackParams(request));
    const finalRequest = (result ?? request) as Request;

    expect(finalRequest.headers.get("Authorization")).toBe("Bearer AU-abc123");
  });
});
