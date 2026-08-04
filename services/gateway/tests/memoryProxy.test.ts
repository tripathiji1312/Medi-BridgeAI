import { createServer, type Server } from "node:http";
import { AddressInfo } from "node:net";
import { afterEach, describe, expect, it } from "vitest";
import type { FastifyInstance } from "fastify";
import { buildApp } from "../src/app";

let app: FastifyInstance | undefined;
let upstream: Server | undefined;

afterEach(async () => {
  await app?.close();
  upstream?.close();
  app = undefined;
  upstream = undefined;
});

function listen(server: Server): Promise<number> {
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve((server.address() as AddressInfo).port));
  });
}

describe("gateway memory proxy", () => {
  it("forwards GET /sessions/:id/memory to orchestrator verbatim", async () => {
    upstream = createServer((req, res) => {
      expect(req.url).toBe("/sessions/s1/memory");
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ session_id: "s1", utterances: [], case_memory: [] }));
    });
    const upstreamPort = await listen(upstream);

    app = await buildApp({
      jwtSecret: "test-secret",
      speechPipelineWsUrl: "ws://localhost:0",
      orchestratorUrl: `http://127.0.0.1:${upstreamPort}`,
    });

    const response = await app.inject({ method: "GET", url: "/sessions/s1/memory" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({ session_id: "s1", utterances: [], case_memory: [] });
  });

  it("returns 503 with a reason when orchestrator is unreachable, not a silent empty panel", async () => {
    app = await buildApp({
      jwtSecret: "test-secret",
      speechPipelineWsUrl: "ws://localhost:0",
      orchestratorUrl: "http://127.0.0.1:1", // nothing listens here
    });

    const response = await app.inject({ method: "GET", url: "/sessions/s1/memory" });

    expect(response.statusCode).toBe(503);
    expect(response.json().error).toBe("orchestrator_unavailable");
  });

  it("forwards DELETE case-memory entry requests and status codes verbatim", async () => {
    upstream = createServer((req, res) => {
      expect(req.method).toBe("DELETE");
      expect(req.url).toBe("/sessions/s1/case-memory/entry-1");
      res.writeHead(204);
      res.end();
    });
    const upstreamPort = await listen(upstream);

    app = await buildApp({
      jwtSecret: "test-secret",
      speechPipelineWsUrl: "ws://localhost:0",
      orchestratorUrl: `http://127.0.0.1:${upstreamPort}`,
    });

    const response = await app.inject({ method: "DELETE", url: "/sessions/s1/case-memory/entry-1" });

    expect(response.statusCode).toBe(204);
  });

  it("forwards a 404 from orchestrator (e.g. unknown entry) rather than masking it", async () => {
    upstream = createServer((_req, res) => {
      res.writeHead(404, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ detail: "No case-memory entry found: bogus" }));
    });
    const upstreamPort = await listen(upstream);

    app = await buildApp({
      jwtSecret: "test-secret",
      speechPipelineWsUrl: "ws://localhost:0",
      orchestratorUrl: `http://127.0.0.1:${upstreamPort}`,
    });

    const response = await app.inject({ method: "DELETE", url: "/sessions/s1/case-memory/bogus" });

    expect(response.statusCode).toBe(404);
  });
});
