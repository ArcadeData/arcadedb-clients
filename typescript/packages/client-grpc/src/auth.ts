import type { Interceptor } from "@connectrpc/connect";

/**
 * Marks an {@link Interceptor} produced by {@link passwordAuth} as one that sends a plaintext
 * password in gRPC metadata. `createClient` checks for this marker to refuse a plaintext
 * password over a non-TLS `baseUrl` unless the caller opts in with `insecure: true`. Not part of
 * this package's public surface: it exists only to let `index.ts` distinguish a password
 * interceptor from any other (e.g. `bearerAuth`, which carries no plaintext password and is not
 * marked).
 */
export const PLAINTEXT_PASSWORD = Symbol("arcadedb.grpc.plaintextPassword");

/** An {@link Interceptor} that may carry the {@link PLAINTEXT_PASSWORD} marker. */
export type MarkedInterceptor = Interceptor & { [PLAINTEXT_PASSWORD]?: true };

/** True when `auth` is an interceptor produced by {@link passwordAuth}. */
export function sendsPlaintextPassword(auth: Interceptor | undefined): boolean {
  return auth !== undefined && (auth as MarkedInterceptor)[PLAINTEXT_PASSWORD] === true;
}

/**
 * Authenticates against ArcadeDB's gRPC data plane with a bearer token, setting
 * `authorization: Bearer <token>` on every outgoing call's metadata.
 */
export function bearerAuth(token: string): Interceptor {
  return (next) => async (req) => {
    req.header.set("authorization", `Bearer ${token}`);
    return next(req);
  };
}

/**
 * Authenticates against ArcadeDB's gRPC data plane with a username and password, setting
 * `x-arcade-user`, `x-arcade-password`, and (when given) `x-arcade-database` on every outgoing
 * call's metadata.
 *
 * The password is sent in plaintext metadata. `createClient` refuses to pair this interceptor
 * with a non-TLS (`http://`) `baseUrl` unless `insecure: true` is passed explicitly - see
 * `index.ts`.
 */
export function passwordAuth(user: string, password: string, database?: string): Interceptor {
  const interceptor: MarkedInterceptor = (next) => async (req) => {
    req.header.set("x-arcade-user", user);
    req.header.set("x-arcade-password", password);
    if (database !== undefined) req.header.set("x-arcade-database", database);
    return next(req);
  };
  interceptor[PLAINTEXT_PASSWORD] = true;
  return interceptor;
}
