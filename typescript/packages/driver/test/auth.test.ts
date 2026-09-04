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

    // Hardcoded, not computed via btoa(...): computing the expectation with the same function
    // production code calls is tautological and would stay green even if basicAuth mis-encoded
    // non-ASCII input the same way btoa does on its own (see the non-ASCII test below).
    expect(finalRequest.headers.get("Authorization")).toBe("Basic cm9vdDpwbGF5d2l0aGRhdGE=");
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

      expect(finalRequest.headers.get("Authorization")).toBe("Basic cm9vdDpwbGF5d2l0aGRhdGE=");
    } finally {
      globalWithBuffer.Buffer = originalBuffer;
    }
  });

  it("encodes ASCII special characters in the credential correctly", () => {
    const middleware = basicAuth("user@example.com", "p@ss:word!");
    const request = new Request("https://example.com/api/v1/databases");

    const result = middleware.onRequest?.(callbackParams(request));
    const finalRequest = (result ?? request) as Request;

    expect(finalRequest.headers.get("Authorization")).toBe("Basic dXNlckBleGFtcGxlLmNvbTpwQHNzOndvcmQh");
  });

  it("encodes a non-ASCII (Latin-1 range) password as UTF-8, not as btoa's raw Latin-1 octets", () => {
    // btoa("root:pässwörd") on its own yields "cm9vdDpw5HNzd/ZyZA==" - the Latin-1 byte for "ä"
    // (0xE4), not its UTF-8 encoding. That is the exact bug this test guards against.
    const middleware = basicAuth("root", "pässwörd");
    const request = new Request("https://example.com/api/v1/databases");

    const result = middleware.onRequest?.(callbackParams(request));
    const finalRequest = (result ?? request) as Request;

    expect(finalRequest.headers.get("Authorization")).toBe("Basic cm9vdDpww6Rzc3fDtnJk");
  });

  it("encodes a non-ASCII (CJK) password without throwing", () => {
    // btoa("root:密码") on its own throws a DOMException - characters above U+00FF are outside
    // btoa's Latin-1 input range. basicAuth must not propagate that.
    const middleware = basicAuth("root", "密码");
    const request = new Request("https://example.com/api/v1/databases");

    const result = middleware.onRequest?.(callbackParams(request));
    const finalRequest = (result ?? request) as Request;

    expect(finalRequest.headers.get("Authorization")).toBe("Basic cm9vdDrlr4bnoIE=");
  });

  it("encodes a ~100KB credential without RangeError: Maximum call stack size exceeded", () => {
    // String.fromCharCode(...octets) spreads one argument per byte onto the call stack - a
    // credential around 100KB or larger blows it. This is what basicAuth's chunked conversion
    // guards against.
    const longPassword = "x".repeat(100_000);
    const middleware = basicAuth("root", longPassword);
    const request = new Request("https://example.com/api/v1/databases");

    const result = middleware.onRequest?.(callbackParams(request));
    const finalRequest = (result ?? request) as Request;

    const header = finalRequest.headers.get("Authorization");
    expect(header).toMatch(/^Basic /);
    const decoded = Buffer.from(header!.slice("Basic ".length), "base64").toString("utf8");
    expect(decoded).toBe(`root:${longPassword}`);
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
