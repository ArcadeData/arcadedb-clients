import { describe, expect, it } from "vitest";
import { bearerAuth, createClient, passwordAuth } from "../src/index.js";

describe("createClient", () => {
  it("exposes the generated Connect client as raw", () => {
    const client = createClient({ baseUrl: "https://example.com:50051" });

    expect(typeof client.raw.executeCommand).toBe("function");
    expect(typeof client.raw.streamQuery).toBe("function");
  });

  it("does not throw for an https:// baseUrl with passwordAuth", () => {
    expect(() => createClient({ baseUrl: "https://example.com:50051", auth: passwordAuth("root", "pw") })).not.toThrow();
  });

  it("does not throw for an http:// baseUrl with bearerAuth (not a plaintext password)", () => {
    expect(() => createClient({ baseUrl: "http://example.com:50051", auth: bearerAuth("AU-x") })).not.toThrow();
  });

  it("does not throw for an http:// baseUrl with no auth at all", () => {
    expect(() => createClient({ baseUrl: "http://example.com:50051" })).not.toThrow();
  });

  it("throws when passwordAuth is paired with an http:// baseUrl without opting in", () => {
    expect(() => createClient({ baseUrl: "http://example.com:50051", auth: passwordAuth("root", "pw") })).toThrow(/insecure/i);
  });

  it("permits an http:// baseUrl with passwordAuth when insecure: true is passed explicitly", () => {
    expect(() =>
      createClient({ baseUrl: "http://example.com:50051", auth: passwordAuth("root", "pw"), insecure: true }),
    ).not.toThrow();
  });
});
