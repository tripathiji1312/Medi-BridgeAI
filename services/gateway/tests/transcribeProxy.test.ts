import { AddressInfo } from "node:net";
import { WebSocket, WebSocketServer } from "ws";
import { afterEach, describe, expect, it } from "vitest";
import type { FastifyInstance } from "fastify";
import { buildApp } from "../src/app";

let app: FastifyInstance | undefined;
let upstream: WebSocketServer | undefined;

afterEach(async () => {
  await app?.close();
  upstream?.close();
  app = undefined;
  upstream = undefined;
});

function listen(server: WebSocketServer): Promise<number> {
  return new Promise((resolve) => {
    server.on("listening", () => resolve((server.address() as AddressInfo).port));
  });
}

describe("gateway /ws/transcribe proxy", () => {
  it("forwards binary client audio to the upstream speech-pipeline service", async () => {
    upstream = new WebSocketServer({ port: 0 });
    const upstreamPort = await listen(upstream);
    const received: Buffer[] = [];
    upstream.on("connection", (socket) => {
      socket.on("message", (data) => received.push(Buffer.from(data as ArrayBuffer)));
    });

    app = await buildApp({
      jwtSecret: "test-secret",
      speechPipelineWsUrl: `ws://127.0.0.1:${upstreamPort}`,
    });
    const gatewayAddress = await app.listen({ port: 0, host: "127.0.0.1" });

    const client = new WebSocket(`${gatewayAddress.replace("http", "ws")}/ws/transcribe`);
    await new Promise((resolve) => client.on("open", resolve));
    client.send(Buffer.from([1, 2, 3]));

    await new Promise((resolve) => setTimeout(resolve, 100));
    client.close();

    expect(received).toHaveLength(1);
    expect(Array.from(received[0]!)).toEqual([1, 2, 3]);
  });

  it("forwards upstream transcript events back to the client verbatim", async () => {
    upstream = new WebSocketServer({ port: 0 });
    const upstreamPort = await listen(upstream);
    upstream.on("connection", (socket) => {
      socket.send(JSON.stringify({ type: "final", utterance_id: "abc", segment: null, latency_ms: 12.3 }));
    });

    app = await buildApp({
      jwtSecret: "test-secret",
      speechPipelineWsUrl: `ws://127.0.0.1:${upstreamPort}`,
    });
    const gatewayAddress = await app.listen({ port: 0, host: "127.0.0.1" });

    const client = new WebSocket(`${gatewayAddress.replace("http", "ws")}/ws/transcribe`);
    const message = await new Promise<string>((resolve) => {
      client.on("message", (data) => resolve(data.toString()));
    });

    expect(JSON.parse(message)).toEqual({
      type: "final",
      utterance_id: "abc",
      segment: null,
      latency_ms: 12.3,
    });
    client.close();
  });

  it("sends a client-visible error and closes when the upstream is unreachable, instead of hanging silently", async () => {
    app = await buildApp({
      jwtSecret: "test-secret",
      // Nothing listens here -- simulates speech-pipeline being down.
      speechPipelineWsUrl: "ws://127.0.0.1:1/ws/transcribe",
    });
    const gatewayAddress = await app.listen({ port: 0, host: "127.0.0.1" });

    const client = new WebSocket(`${gatewayAddress.replace("http", "ws")}/ws/transcribe`);
    const message = await new Promise<string>((resolve) => {
      client.on("message", (data) => resolve(data.toString()));
    });
    const parsed = JSON.parse(message);

    expect(parsed.type).toBe("error");
    expect(parsed.error).toContain("speech-pipeline unavailable");

    await new Promise((resolve) => client.on("close", resolve));
  });
});
