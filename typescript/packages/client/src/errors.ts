/**
 * Fields ArcadeDB's error responses may carry. The server does not guarantee
 * any of them are present, so every field is optional and parsing never
 * throws: a body that is missing, `null`, or not an object simply yields an
 * error with no extra detail beyond the HTTP status.
 */
interface ArcadeDBErrorBody {
  error?: string;
  exception?: string;
  detail?: string;
  requestId?: string;
}

function stringOrUndefined(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function parseBody(body: unknown): ArcadeDBErrorBody {
  if (body === null || body === undefined || typeof body !== "object") {
    return {};
  }
  const record = body as Record<string, unknown>;
  return {
    error: stringOrUndefined(record.error),
    exception: stringOrUndefined(record.exception),
    detail: stringOrUndefined(record.detail),
    requestId: stringOrUndefined(record.requestId),
  };
}

/**
 * Thrown by every `ArcadeDBServer`/`ArcadeDBDatabase` facade method when the
 * server answers with a non-2xx status. Carries the HTTP status plus
 * whatever the server's JSON error body contributed; every field beyond
 * `status` is optional because the body may be absent, unparsable, or
 * missing individual fields.
 *
 * `raw`, the unwrapped openapi-fetch client, never throws this (or anything
 * else) - it returns `{ data, error }` instead. That asymmetry is
 * deliberate: `ArcadeDBError` is a facade-only concern.
 */
export class ArcadeDBError extends Error {
  readonly status: number;
  readonly error?: string;
  readonly exception?: string;
  readonly detail?: string;
  readonly requestId?: string;

  constructor(status: number, body?: unknown, requestId?: string) {
    const parsed = parseBody(body);
    const resolvedRequestId = requestId ?? parsed.requestId;
    super(parsed.error ?? parsed.detail ?? `ArcadeDB request failed with status ${status}`);
    this.name = "ArcadeDBError";
    this.status = status;
    this.error = parsed.error;
    this.exception = parsed.exception;
    this.detail = parsed.detail;
    this.requestId = resolvedRequestId;
    // Restore the prototype chain: extending built-ins gets clobbered when
    // the target is transpiled to ES5, and costs nothing when it isn't.
    Object.setPrototypeOf(this, ArcadeDBError.prototype);
  }

  /**
   * Builds an `ArcadeDBError` from a fetch `Response` and the (already
   * read) body openapi-fetch produced for a non-2xx result. Reads the
   * `X-Request-Id` response header as a fallback correlation id when the
   * body itself did not carry one.
   */
  static fromResponse(response: Response, body: unknown): ArcadeDBError {
    return new ArcadeDBError(response.status, body, response.headers.get("X-Request-Id") ?? undefined);
  }
}
