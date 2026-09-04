import { describe, expect, it } from "vitest";
import { createContextValues } from "@connectrpc/connect";
import type { Interceptor, UnaryRequest, UnaryResponse } from "@connectrpc/connect";
import { bearerAuth, passwordAuth } from "../src/auth.js";

type Next = Parameters<Interceptor>[0];

/** `next` for these tests never needs to do anything: assertions read the mutated `header`
 * object directly, not `next`'s return value. */
const next: Next = async () => ({}) as unknown as UnaryResponse;

/** Minimal fake `UnaryRequest`: only `header` is exercised by `bearerAuth`/`passwordAuth`, so
 * every other field is an inert placeholder. */
function fakeRequest(header: Headers): UnaryRequest {
  return {
    stream: false,
    header,
    signal: new AbortController().signal,
    contextValues: createContextValues(),
  } as unknown as UnaryRequest;
}

describe("bearerAuth", () => {
  it("sets authorization to Bearer <token>", async () => {
    const header = new Headers();
    const interceptor = bearerAuth("AU-x");

    await interceptor(next)(fakeRequest(header));

    expect(header.get("authorization")).toBe("Bearer AU-x");
  });
});

describe("passwordAuth", () => {
  it("sets x-arcade-user, x-arcade-password and x-arcade-database", async () => {
    const header = new Headers();
    const interceptor = passwordAuth("root", "pw", "mydb");

    await interceptor(next)(fakeRequest(header));

    expect(header.get("x-arcade-user")).toBe("root");
    expect(header.get("x-arcade-password")).toBe("pw");
    expect(header.get("x-arcade-database")).toBe("mydb");
  });

  it("omits x-arcade-database when database is not passed", async () => {
    const header = new Headers();
    const interceptor = passwordAuth("root", "pw");

    await interceptor(next)(fakeRequest(header));

    expect(header.get("x-arcade-user")).toBe("root");
    expect(header.get("x-arcade-password")).toBe("pw");
    expect(header.has("x-arcade-database")).toBe(false);
  });
});
