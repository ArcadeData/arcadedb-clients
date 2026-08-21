import type { Middleware } from "openapi-fetch";

/**
 * HTTP Basic auth middleware. Encodes `user:password` with `btoa`, not
 * `Buffer` - `Buffer` is Node-only and this package's primary targets
 * (browsers, Cloudflare Workers, Deno) do not have it, whereas `btoa` is
 * available everywhere this package runs, including Node 20+.
 */
export function basicAuth(user: string, password: string): Middleware {
  const credential = btoa(`${user}:${password}`);
  return {
    onRequest({ request }) {
      request.headers.set("Authorization", `Basic ${credential}`);
      return request;
    },
  };
}

/**
 * Bearer token auth middleware, for session tokens returned by `/api/v1/login`
 * (prefixed `AU-`) or any other bearer credential.
 */
export function bearerAuth(token: string): Middleware {
  return {
    onRequest({ request }) {
      request.headers.set("Authorization", `Bearer ${token}`);
      return request;
    },
  };
}
