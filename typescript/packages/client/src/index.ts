import createOpenApiClient from "openapi-fetch";
import type { Client, Middleware } from "openapi-fetch";
import type { components, paths } from "./generated/schema.js";
import { ArcadeDBError } from "./errors.js";

export { ArcadeDBError } from "./errors.js";
export { basicAuth, bearerAuth } from "./auth.js";
export type { Middleware } from "openapi-fetch";

/** The unwrapped openapi-fetch client, typed against ArcadeDB's OpenAPI schema. */
type RawClient = Client<paths>;

/**
 * Unwraps an openapi-fetch call result: returns `data` on success, throws
 * `ArcadeDBError` on any non-2xx response. This is the one place that
 * bridges openapi-fetch's non-throwing `{ data, error }` contract to the
 * throwing facade methods on `ArcadeDBServer`/`ArcadeDBDatabase`.
 */
async function unwrap<T>(promise: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  const { data, error, response } = await promise;
  if (!response.ok) {
    throw ArcadeDBError.fromResponse(response, error);
  }
  return data as T;
}

/**
 * A single database reached through an `ArcadeDBServer`. Constructed by
 * `ArcadeDBServer.db()`; query, command, and transaction methods are added
 * to this class in later tasks.
 */
export class ArcadeDBDatabase {
  constructor(
    /** @internal Populated by query/command/transaction methods added in later tasks. */
    private readonly client: RawClient,
    readonly name: string,
  ) {}
}

/**
 * A connection to one ArcadeDB server, scoped to server-level operations
 * (listing/checking databases, server info, health/readiness) plus
 * `db()` to reach a specific database.
 */
export class ArcadeDBServer {
  /**
   * The unwrapped openapi-fetch client this facade is built on. Returns
   * `{ data, error }` and does NOT throw, unlike every method above -
   * that asymmetry is deliberate: use `raw` when you want to handle
   * `ArcadeDBError`-worthy conditions yourself instead of via try/catch.
   */
  readonly raw: RawClient;

  constructor(client: RawClient) {
    this.raw = client;
  }

  /** Lists the names of every database visible to the authenticated caller. */
  async listDatabases(): Promise<string[]> {
    const data = await unwrap(this.raw.GET("/api/v1/databases", {}));
    return data.result ?? [];
  }

  /**
   * Checks whether a database exists and is visible to the authenticated
   * caller.
   *
   * `false` cannot distinguish "the database does not exist" from "it
   * exists, but the caller is not authorized to see it" - the server does
   * not make that distinction in its response, so this client cannot
   * either. Do not treat a `false` result as proof the database is absent.
   */
  async exists(name: string): Promise<boolean> {
    const data = await unwrap(
      this.raw.GET("/api/v1/exists/{database}", {
        params: { path: { database: name } },
      }),
    );
    return data.result ?? false;
  }

  /** Retrieves server status, version, and configuration information. */
  async serverInfo(): Promise<components["schemas"]["ServerInfo"]> {
    return unwrap(this.raw.GET("/api/v1/server", {}));
  }

  /**
   * Liveness probe: resolves when the server process and HTTP layer are
   * up. Performs no database I/O and requires no authentication. Throws
   * `ArcadeDBError` if the server does not answer 204.
   */
  async health(): Promise<void> {
    await unwrap(this.raw.GET("/api/v1/health", {}));
  }

  /**
   * Readiness probe: resolves `true` when the server is ready to accept
   * requests, `false` when it has answered 503 (not finished starting, not
   * yet joined its Raft group, or still catching up on replication). Any
   * other failure still throws `ArcadeDBError`.
   */
  async ready(): Promise<boolean> {
    const { response } = await this.raw.GET("/api/v1/ready", {});
    if (response.status === 503) {
      return false;
    }
    if (!response.ok) {
      throw ArcadeDBError.fromResponse(response, undefined);
    }
    return true;
  }

  /** Scopes subsequent calls to one database, reached through this server. */
  db(name: string): ArcadeDBDatabase {
    return new ArcadeDBDatabase(this.raw, name);
  }
}

export interface CreateClientOptions {
  /** Base URL of the ArcadeDB server, e.g. `http://localhost:2480`. */
  baseUrl: string;
  /** Auth middleware, typically `basicAuth(...)` or `bearerAuth(...)`. */
  auth?: Middleware;
  /** Custom `fetch` implementation; defaults to the runtime global. */
  fetch?: typeof fetch;
}

/** Builds an `ArcadeDBServer` client scoped to one ArcadeDB server. */
export function createClient(opts: CreateClientOptions): ArcadeDBServer {
  const client = createOpenApiClient<paths>({
    baseUrl: opts.baseUrl,
    fetch: opts.fetch,
  });
  if (opts.auth) {
    client.use(opts.auth);
  }
  return new ArcadeDBServer(client);
}
