import { describe, expect, it } from "vitest";
import { buildApp } from "../src/app";
import { TEST_APP_OPTIONS } from "./testHelpers";

describe("GET /health", () => {
  it("returns 200 with the shared HealthResponse shape", async () => {
    const app = await buildApp(TEST_APP_OPTIONS);
    const response = await app.inject({ method: "GET", url: "/health" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({ status: "ok", service: "gateway", version: "0.1.0" });
    await app.close();
  });
});
