import createOpenApiClient from "openapi-fetch";
import type { Client, Middleware } from "openapi-fetch";
import type { components, paths } from "./generated/schema.js";
import { ArcadeDBError } from "./errors.js";
import { beginTransaction, commitTransaction, executeCommand, executeQuery, rollbackTransaction } from "./facade/data.js";
import type { QueryEnvelope, QueryOptions } from "./facade/data.js";
import type {
  GrafanaQueryOptions,
  GrafanaQueryResponse,
  PromQLDataResponse,
  PromQLLabelsResponse,
  PromQLQueryOptions,
  PromQLQueryRangeOptions,
  PromQLSeriesOptions,
  PromQLSeriesResponse,
} from "./facade/dashboards.js";
import type { TimeSeriesQueryOptions, TimeSeriesQueryResult, TimeSeriesWriteOptions } from "./facade/timeseries.js";

export { ArcadeDBError } from "./errors.js";
export { basicAuth, bearerAuth } from "./auth.js";
export type { Middleware } from "openapi-fetch";
export type { QueryEnvelope, QueryLanguage, QueryOptions } from "./facade/data.js";
export type {
  GrafanaQueryOptions,
  GrafanaQueryResponse,
  PromQLDataResponse,
  PromQLLabelsResponse,
  PromQLMatrixSeries,
  PromQLQueryOptions,
  PromQLQueryRangeOptions,
  PromQLResult,
  PromQLSeriesOptions,
  PromQLSeriesResponse,
  PromQLVectorSample,
} from "./facade/dashboards.js";
export type { TimeSeriesQueryOptions, TimeSeriesQueryResult, TimeSeriesWriteOptions } from "./facade/timeseries.js";

/** The unwrapped openapi-fetch client, typed against ArcadeDB's OpenAPI schema. */
type RawClient = Client<paths>;

/**
 * Unwraps an openapi-fetch call result: returns `data` on success, throws
 * `ArcadeDBError` on any non-2xx response. This is the one place that
 * bridges openapi-fetch's non-throwing `{ data, error }` contract to the
 * throwing facade methods on `ArcadeDBServer`/`ArcadeDBDatabase`.
 */
export async function unwrap<T>(promise: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
  const { data, error, response } = await promise;
  if (!response.ok) {
    throw ArcadeDBError.fromResponse(response, error);
  }
  return data as T;
}

/**
 * Ingests and queries samples in a time-series type - the `db.ts` namespace.
 *
 * Each method dynamically imports `facade/timeseries.js` on first call rather than `index.ts`
 * statically importing `TimeSeriesNamespace`. `db.ts`/`db.grafana`/`db.promql` are dashboard/ingest
 * namespaces, not the data plane (`query`/`command`/`transaction`); every method here was already
 * `Promise`-returning, so deferring the import to inside the method body is invisible to callers -
 * `db.ts` itself stays a synchronous property access, only the first call pays the import cost. This
 * is what lets a bundler that supports code-splitting keep `facade/timeseries.js` out of a chunk that
 * only reaches `query`/`command`/`transaction`; see `test/treeshake.test.ts`.
 */
class LazyTimeSeriesNamespace {
  constructor(
    private readonly client: RawClient,
    private readonly database: string,
  ) {}

  /** Ingests samples in InfluxDB Line Protocol. */
  async write(opts: TimeSeriesWriteOptions): Promise<void> {
    const { writeTimeSeries } = await import("./facade/timeseries.js");
    return writeTimeSeries(this.client, this.database, opts);
  }

  /** Queries samples, optionally aggregated into buckets. */
  async query(opts: TimeSeriesQueryOptions): Promise<TimeSeriesQueryResult> {
    const { queryTimeSeries } = await import("./facade/timeseries.js");
    return queryTimeSeries(this.client, this.database, opts);
  }
}

/**
 * Grafana panel queries over a time-series type - the `db.grafana` namespace.
 *
 * Lazily imports `facade/dashboards.js`; see `LazyTimeSeriesNamespace`'s doc comment for why.
 */
class LazyGrafanaNamespace {
  constructor(
    private readonly client: RawClient,
    private readonly database: string,
  ) {}

  /** Executes one query per `targets` entry, returning DataFrames keyed by `refId`. */
  async query(opts: GrafanaQueryOptions): Promise<GrafanaQueryResponse> {
    const { queryGrafana } = await import("./facade/dashboards.js");
    return queryGrafana(this.client, this.database, opts);
  }
}

/**
 * A Prometheus-compatible query surface over a time-series type - the `db.promql` namespace.
 *
 * Lazily imports `facade/dashboards.js`; see `LazyTimeSeriesNamespace`'s doc comment for why.
 */
class LazyPromQLNamespace {
  constructor(
    private readonly client: RawClient,
    private readonly database: string,
  ) {}

  /** Evaluates a PromQL expression at one instant. */
  async query(opts: PromQLQueryOptions): Promise<PromQLDataResponse> {
    const { queryPromQL } = await import("./facade/dashboards.js");
    return queryPromQL(this.client, this.database, opts);
  }

  /** Evaluates a PromQL expression at every step across a range. */
  async queryRange(opts: PromQLQueryRangeOptions): Promise<PromQLDataResponse> {
    const { queryRangePromQL } = await import("./facade/dashboards.js");
    return queryRangePromQL(this.client, this.database, opts);
  }

  /** Lists every label name present in the database, sorted, always including `__name__`. */
  async labels(): Promise<PromQLLabelsResponse> {
    const { labelsPromQL } = await import("./facade/dashboards.js");
    return labelsPromQL(this.client, this.database);
  }

  /** Returns the label sets of the series matching the given `match[]` selectors. */
  async series(opts: PromQLSeriesOptions): Promise<PromQLSeriesResponse> {
    const { seriesPromQL } = await import("./facade/dashboards.js");
    return seriesPromQL(this.client, this.database, opts);
  }
}

/**
 * A single database reached through an `ArcadeDBServer`. Constructed by
 * `ArcadeDBServer.db()`.
 *
 * When held via `transaction()`'s callback parameter, `sessionId` is set and
 * every `query`/`command` call made through this instance carries it on the
 * `arcadedb-session-id` header, which is what keeps those calls inside the
 * transaction rather than auto-committing individually.
 */
export class ArcadeDBDatabase {
  private _ts: LazyTimeSeriesNamespace | undefined;
  private _grafana: LazyGrafanaNamespace | undefined;
  private _promql: LazyPromQLNamespace | undefined;

  constructor(
    private readonly client: RawClient,
    readonly name: string,
    private readonly sessionId?: string,
  ) {}

  /** Ingests and queries samples in a time-series type. Loaded on first use; see `LazyTimeSeriesNamespace`. */
  get ts(): LazyTimeSeriesNamespace {
    return (this._ts ??= new LazyTimeSeriesNamespace(this.client, this.name));
  }

  /** Grafana panel queries over a time-series type. Loaded on first use; see `LazyGrafanaNamespace`. */
  get grafana(): LazyGrafanaNamespace {
    return (this._grafana ??= new LazyGrafanaNamespace(this.client, this.name));
  }

  /** A Prometheus-compatible query surface over a time-series type. Loaded on first use; see `LazyPromQLNamespace`. */
  get promql(): LazyPromQLNamespace {
    return (this._promql ??= new LazyPromQLNamespace(this.client, this.name));
  }

  /** Executes a read-or-write query and returns the whole result envelope - not just `result`. */
  async query<T = unknown>(opts: QueryOptions): Promise<QueryEnvelope<T>> {
    return executeQuery<T>(this.client, this.name, this.sessionId, opts);
  }

  /** Executes a command and returns the whole result envelope - not just `result`. */
  async command<T = unknown>(opts: QueryOptions): Promise<QueryEnvelope<T>> {
    return executeCommand<T>(this.client, this.name, this.sessionId, opts);
  }

  /**
   * Runs `fn` inside a server-side transaction. `fn` is handed a database
   * handle scoped to the transaction's session id, so every call it makes
   * through that handle - not the outer `this` - takes part in the
   * transaction. Commits when `fn` resolves and returns its value; rolls
   * back and re-throws the original error when `fn` throws or rejects,
   * synchronously or otherwise.
   */
  async transaction<T>(fn: (tx: ArcadeDBDatabase) => Promise<T>): Promise<T> {
    const sessionId = await beginTransaction(this.client, this.name);
    const tx = new ArcadeDBDatabase(this.client, this.name, sessionId);
    let result: T;
    try {
      result = await fn(tx);
    } catch (err) {
      await rollbackTransaction(this.client, this.name, sessionId);
      throw err;
    }
    await commitTransaction(this.client, this.name, sessionId);
    return result;
  }
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
