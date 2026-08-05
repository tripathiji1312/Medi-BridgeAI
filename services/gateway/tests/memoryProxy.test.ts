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

  it("forwards POST dismissed-alerts requests with the body verbatim", async () => {
    upstream = createServer((req, res) => {
      expect(req.method).toBe("POST");
      expect(req.url).toBe("/sessions/s1/dismissed-alerts");
      let raw = "";
      req.on("data", (chunk) => (raw += chunk));
      req.on("end", () => {
        expect(JSON.parse(raw)).toEqual({ reason: "false positive" });
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ id: "d1", reason: "false positive", source_utterance_id: null }));
      });
    });
    const upstreamPort = await listen(upstream);

    app = await buildApp({
      jwtSecret: "test-secret",
      speechPipelineWsUrl: "ws://localhost:0",
      orchestratorUrl: `http://127.0.0.1:${upstreamPort}`,
    });

    const response = await app.inject({
      method: "POST",
      url: "/sessions/s1/dismissed-alerts",
      payload: { reason: "false positive" },
    });

    expect(response.statusCode).toBe(200);
    expect(response.json().reason).toBe("false positive");
  });

  it("returns 503 with a reason when orchestrator is unreachable for a dismissed-alert POST", async () => {
    app = await buildApp({
      jwtSecret: "test-secret",
      speechPipelineWsUrl: "ws://localhost:0",
      orchestratorUrl: "http://127.0.0.1:1",
    });

    const response = await app.inject({
      method: "POST",
      url: "/sessions/s1/dismissed-alerts",
      payload: { reason: "false positive" },
    });

    expect(response.statusCode).toBe(503);
    expect(response.json().error).toBe("orchestrator_unavailable");
  });

  it("forwards POST summary/generate to orchestrator and returns the structured summary", async () => {
    upstream = createServer((req, res) => {
      expect(req.method).toBe("POST");
      expect(req.url).toBe("/sessions/s1/summary/generate");
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ model_name: "stub", complaints: [] }));
    });
    const upstreamPort = await listen(upstream);

    app = await buildApp({
      jwtSecret: "test-secret",
      speechPipelineWsUrl: "ws://localhost:0",
      orchestratorUrl: `http://127.0.0.1:${upstreamPort}`,
    });

    const response = await app.inject({ method: "POST", url: "/sessions/s1/summary/generate" });

    expect(response.statusCode).toBe(200);
    expect(response.json().model_name).toBe("stub");
  });

  it("returns 503 with a reason when orchestrator is unreachable for summary/generate", async () => {
    app = await buildApp({
      jwtSecret: "test-secret",
      speechPipelineWsUrl: "ws://localhost:0",
      orchestratorUrl: "http://127.0.0.1:1",
    });

    const response = await app.inject({ method: "POST", url: "/sessions/s1/summary/generate" });

    expect(response.statusCode).toBe(503);
    expect(response.json().error).toBe("orchestrator_unavailable");
  });

  it("forwards POST summary/approve and its 204 status verbatim", async () => {
    upstream = createServer((req, res) => {
      expect(req.method).toBe("POST");
      expect(req.url).toBe("/sessions/s1/summary/approve");
      res.writeHead(204);
      res.end();
    });
    const upstreamPort = await listen(upstream);

    app = await buildApp({
      jwtSecret: "test-secret",
      speechPipelineWsUrl: "ws://localhost:0",
      orchestratorUrl: `http://127.0.0.1:${upstreamPort}`,
    });

    const response = await app.inject({ method: "POST", url: "/sessions/s1/summary/approve" });

    expect(response.statusCode).toBe(204);
  });

  it("forwards a 409 from orchestrator when approving with no draft summary", async () => {
    upstream = createServer((_req, res) => {
      res.writeHead(409, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ detail: "No draft summary to approve -- generate one first" }));
    });
    const upstreamPort = await listen(upstream);

    app = await buildApp({
      jwtSecret: "test-secret",
      speechPipelineWsUrl: "ws://localhost:0",
      orchestratorUrl: `http://127.0.0.1:${upstreamPort}`,
    });

    const response = await app.inject({ method: "POST", url: "/sessions/s1/summary/approve" });

    expect(response.statusCode).toBe(409);
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
