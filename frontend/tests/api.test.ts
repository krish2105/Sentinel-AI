import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, getToken, setToken, TOKEN_KEY } from "@/lib/api";

describe("token storage", () => {
  beforeEach(() => localStorage.clear());

  it("round-trips a token", () => {
    expect(getToken()).toBeNull();
    setToken("abc");
    expect(getToken()).toBe("abc");
    expect(localStorage.getItem(TOKEN_KEY)).toBe("abc");
  });

  it("clears with null", () => {
    setToken("abc");
    setToken(null);
    expect(getToken()).toBeNull();
  });
});

describe("api request handling", () => {
  afterEach(() => vi.restoreAllMocks());

  it("attaches a bearer token when present", async () => {
    setToken("tok-123");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: "ok", llm_provider: "mock" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await api.health();
    const headers = fetchMock.mock.calls[0][1].headers;
    expect(headers.Authorization).toBe("Bearer tok-123");
    setToken(null);
  });

  it("throws with the server-provided detail on error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
        json: async () => ({ detail: "Target not found." }),
      })
    );
    await expect(api.getTarget("missing")).rejects.toThrow("Target not found.");
  });

  it("returns undefined for 204 responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, status: 204, json: async () => ({}) })
    );
    await expect(api.deleteTarget("x")).resolves.toBeUndefined();
  });
});
