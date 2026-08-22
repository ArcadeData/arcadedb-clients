import { ArcadeDBError } from "../errors.js";

/**
 * Unwraps an openapi-fetch call result: returns `data` on success, throws
 * `ArcadeDBError` on any non-2xx response. This is the one place that
 * bridges openapi-fetch's non-throwing `{ data, error }` contract to the
 * throwing facade methods on `ArcadeDBServer`/`ArcadeDBDatabase`.
 *
 * Internal-only: not exported from `index.ts`. It exists so `index.ts` and
 * `facade/*.ts` can share one implementation without either statically
 * importing the other - `index.ts` builds `ArcadeDBServer`/`ArcadeDBDatabase`
 * out of the `facade/*.ts` functions, and `facade/*.ts` needs `unwrap` too,
 * so a plain re-export from `index.ts` would put those two modules in an
 * import cycle. Moving `unwrap` here breaks that cycle instead of merely
 * tolerating it.
 */
export async function unwrap<T>(promise: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  const { data, error, response } = await promise;
  if (!response.ok) {
    throw ArcadeDBError.fromResponse(response, error);
  }
  return data as T;
}
