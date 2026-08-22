import type { Middleware } from "openapi-fetch";

/**
 * HTTP Basic auth middleware. Encodes `user:password` as UTF-8, then base64,
 * matching RFC 7617 and what ArcadeDB's server expects.
 *
 * `btoa` alone cannot do this: it treats its input as a binary (Latin-1)
 * string, emitting Latin-1 octets for U+0080..U+00FF and throwing a
 * `DOMException` for anything above U+00FF - a password containing
 * `ä`/`é`/`ñ` would produce a header with silently wrong bytes, and a CJK
 * password would throw from inside `basicAuth()` itself. So the
 * credential is first encoded to UTF-8 octets with `TextEncoder`, then those
 * octets (not the original string) are handed to `btoa`, which is a pure
 * binary-to-base64 step at that point. `TextEncoder` is available in the
 * same runtimes `btoa` is - Node 20+, browsers, Cloudflare Workers, Deno -
 * so this keeps the "not `Buffer`" property the tests guard: `Buffer` is
 * Node-only and this package's primary targets do not have it.
 */
export function basicAuth(user: string, password: string): Middleware {
  const octets = new TextEncoder().encode(`${user}:${password}`);
  const credential = btoa(String.fromCharCode(...octets));
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
