import type { Client } from "openapi-fetch";
import type { components, paths } from "../generated/schema.js";
import { ArcadeDBError } from "../errors.js";
import { unwrap } from "../index.js";

/** The unwrapped openapi-fetch client, typed against ArcadeDB's OpenAPI schema. */
type RawClient = Client<paths>;

/** Request header carrying the session id that scopes a call to one transaction. */
const SESSION_HEADER = "arcadedb-session-id";

/** Query/command language, as accepted by the `/query` and `/command` endpoints. */
export type QueryLanguage = "sql" | "cypher" | "gremlin" | "graphql" | "mongo";

export interface QueryOptions {
  language: QueryLanguage;
  command: string;
  params?: Record<string, unknown>;
}

/**
 * The whole result envelope `query`/`command` return - not just the rows.
 * `truncated` means the serializer's row cap stopped mid-serialization with
 * rows still pending, so `result` is incomplete: callers that only read
 * `result` and ignore `truncated` can silently work off a partial answer.
 */
export type QueryEnvelope<T = unknown> = {
  result: T[];
  limit: number;
  returned: number;
  truncated: boolean;
};

function toEnvelope<T>(data: components["schemas"]["QueryResponse"]): QueryEnvelope<T> {
  return {
    result: (data.result ?? []) as T[],
    limit: data.limit ?? -1,
    returned: data.returned ?? 0,
    truncated: data.truncated ?? false,
  };
}

/**
 * Builds the JSON body shared by `/query` and `/command`. `params` is typed
 * `Record<string, never>` in the generated schema (an openapi-typescript
 * artifact for "untyped object", not a real restriction), so it is cast at
 * the call site rather than here.
 */
function buildBody(opts: QueryOptions): { command: string; language: string; params?: Record<string, unknown> } {
  return { command: opts.command, language: opts.language, params: opts.params };
}

/** Attaches the session header when `sessionId` is set; omits it otherwise. */
function sessionHeader(sessionId: string | undefined): { [SESSION_HEADER]?: string } | undefined {
  return sessionId === undefined ? undefined : { [SESSION_HEADER]: sessionId };
}

/** Executes `POST /api/v1/query/{database}`. Returns the whole result envelope, unaltered. */
export async function executeQuery<T = unknown>(
  client: RawClient,
  database: string,
  sessionId: string | undefined,
  opts: QueryOptions,
): Promise<QueryEnvelope<T>> {
  const data = await unwrap(
    client.POST("/api/v1/query/{database}", {
      params: { path: { database }, header: sessionHeader(sessionId) },
      body: buildBody(opts) as components["schemas"]["QueryRequest"],
    }),
  );
  return toEnvelope<T>(data);
}

/**
 * Executes `POST /api/v1/command/{database}`. Returns the whole result envelope, unaltered.
 *
 * `CommandRequest.language` is a required field in the generated schema,
 * matching the server's `PostCommandHandler`, which rejects a request
 * without it (`requireStringField(requestMap, "language")`).
 */
export async function executeCommand<T = unknown>(
  client: RawClient,
  database: string,
  sessionId: string | undefined,
  opts: QueryOptions,
): Promise<QueryEnvelope<T>> {
  const data = await unwrap(
    client.POST("/api/v1/command/{database}", {
      params: { path: { database }, header: sessionHeader(sessionId) },
      body: buildBody(opts) as components["schemas"]["CommandRequest"],
    }),
  );
  return toEnvelope<T>(data);
}

/**
 * Begins a transaction and returns its session id, read from the
 * `arcadedb-session-id` response header (the endpoint answers 204, with no
 * body). Threading that id onto every subsequent call is what keeps those
 * calls inside the transaction; the actual threading happens in the caller.
 */
export async function beginTransaction(client: RawClient, database: string): Promise<string> {
  const { error, response } = await client.POST("/api/v1/begin/{database}", {
    params: { path: { database } },
  });
  if (!response.ok) {
    throw ArcadeDBError.fromResponse(response, error);
  }
  const sessionId = response.headers.get(SESSION_HEADER);
  if (!sessionId) {
    throw new ArcadeDBError(response.status, { error: "beginTransaction did not return a session id" });
  }
  return sessionId;
}

/** Commits the transaction identified by `sessionId`. The endpoint answers 204 with no body. */
export async function commitTransaction(client: RawClient, database: string, sessionId: string): Promise<void> {
  await unwrap(
    client.POST("/api/v1/commit/{database}", {
      params: { path: { database }, header: { [SESSION_HEADER]: sessionId } },
    }),
  );
}

/** Rolls back the transaction identified by `sessionId`. The endpoint answers 204 with no body. */
export async function rollbackTransaction(client: RawClient, database: string, sessionId: string): Promise<void> {
  await unwrap(
    client.POST("/api/v1/rollback/{database}", {
      params: { path: { database }, header: { [SESSION_HEADER]: sessionId } },
    }),
  );
}
