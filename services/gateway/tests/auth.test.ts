import { describe, expect, it } from "vitest";
import { buildApp } from "../src/app";
import { signSessionToken } from "../src/auth/jwt";
import { TEST_APP_OPTIONS } from "./testHelpers";

const SECRET = "test-secret";

describe("auth stub", () => {
  it("rejects requests with no Authorization header", async () => {
    const app = await buildApp({ ...TEST_APP_OPTIONS, jwtSecret: SECRET });
    const response = await app.inject({ method: "GET", url: "/session/whoami" });

    expect(response.statusCode).toBe(401);
    expect(response.json()).toEqual({ error: "missing_token" });
    await app.close();
  });

  it("rejects an invalid/expired token rather than silently treating it as anonymous", async () => {
    const app = await buildApp({ ...TEST_APP_OPTIONS, jwtSecret: SECRET });
    const response = await app.inject({
      method: "GET",
      url: "/session/whoami",
      headers: { authorization: "Bearer not-a-real-token" },
    });

    expect(response.statusCode).toBe(401);
    expect(response.json()).toEqual({ error: "invalid_token" });
    await app.close();
  });

  it("accepts a validly signed token and exposes the decoded session claims", async () => {
    const app = await buildApp({ ...TEST_APP_OPTIONS, jwtSecret: SECRET });
    const token = signSessionToken({ sub: "doctor-1", role: "doctor" }, SECRET, "15m");

    const response = await app.inject({
      method: "GET",
      url: "/session/whoami",
      headers: { authorization: `Bearer ${token}` },
    });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toMatchObject({ sub: "doctor-1", role: "doctor" });
    await app.close();
  });
});
