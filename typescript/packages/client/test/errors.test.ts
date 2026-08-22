import { describe, expect, it } from "vitest";
import { ArcadeDBError } from "../src/errors.js";

describe("ArcadeDBError", () => {
  it("carries status, error, exception, and detail from a parsed JSON body", () => {
    const err = new ArcadeDBError(404, {
      error: "Database not found",
      exception: "com.arcadedb.exception.DatabaseOperationException",
      detail: "Database 'foo' was not found",
    });

    expect(err).toBeInstanceOf(Error);
    expect(err.status).toBe(404);
    expect(err.error).toBe("Database not found");
    expect(err.exception).toBe("com.arcadedb.exception.DatabaseOperationException");
    expect(err.detail).toBe("Database 'foo' was not found");
  });

  it("carries help and exceptionArgs from a parsed JSON body", () => {
    const err = new ArcadeDBError(400, {
      error: "Invalid parameter",
      help: "See the SQL reference for valid syntax",
      exceptionArgs: "arg0, arg1",
    });

    expect(err.help).toBe("See the SQL reference for valid syntax");
    expect(err.exceptionArgs).toBe("arg0, arg1");
  });

  it("leaves help and exceptionArgs undefined when the body does not carry them", () => {
    const err = new ArcadeDBError(404, { error: "Database not found" });

    expect(err.help).toBeUndefined();
    expect(err.exceptionArgs).toBeUndefined();
  });

  it("carries requestId when supplied out of band (from the X-Request-Id response header)", () => {
    const err = new ArcadeDBError(404, { error: "Database not found" }, "req-abc-123");

    expect(err.requestId).toBe("req-abc-123");
  });

  it("falls back to a body-supplied requestId when none is passed explicitly", () => {
    const err = new ArcadeDBError(404, { error: "Database not found", requestId: "body-req-456" });

    expect(err.requestId).toBe("body-req-456");
  });

  it("tolerates an absent body without throwing", () => {
    const err = new ArcadeDBError(500);

    expect(err.status).toBe(500);
    expect(err.error).toBeUndefined();
    expect(err.exception).toBeUndefined();
    expect(err.detail).toBeUndefined();
    expect(err.requestId).toBeUndefined();
    expect(err.message).toContain("500");
  });

  it("discards a non-JSON (string) body entirely, falling back to the default message", () => {
    // A string body is not "object", so parseBody's `typeof body !== "object"` guard drops it
    // wholesale rather than reading properties off it. This assertion does NOT prove the guard
    // is load-bearing, though: none of the six fields parseBody extracts (error, exception,
    // detail, requestId, help, exceptionArgs) collides with a name on String.prototype, so
    // reading `body.error` off the raw string primitive - which is exactly what happens when a
    // property is read on a primitive; JS auto-boxes it rather than throwing - would also come
    // back `undefined` for every field. Removing the guard entirely leaves this test byte-for-byte
    // green. It is kept for defensive clarity (and to avoid running six property reads against a
    // primitive), not because this test demonstrates it changes the outcome.
    const err = new ArcadeDBError(502, "Bad Gateway from upstream proxy");

    expect(err.status).toBe(502);
    expect(err.error).toBeUndefined();
    expect(err.exception).toBeUndefined();
    expect(err.detail).toBeUndefined();
    expect(err.requestId).toBeUndefined();
    expect(err.message).toBe("ArcadeDB request failed with status 502");
  });

  it("tolerates a null body without throwing", () => {
    const err = new ArcadeDBError(503, null);

    expect(err.status).toBe(503);
    expect(err.error).toBeUndefined();
  });

  it("is named ArcadeDBError and survives instanceof checks through a throw/catch round trip", () => {
    try {
      throw new ArcadeDBError(400, { error: "Bad request" });
    } catch (caught) {
      expect(caught).toBeInstanceOf(ArcadeDBError);
      expect((caught as ArcadeDBError).name).toBe("ArcadeDBError");
    }
  });
});
