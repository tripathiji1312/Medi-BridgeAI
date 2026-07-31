import { describe, expect, it, vi } from "vitest";
import { TranscriptSocket } from "../src/services/transcriptSocket";

class FakeWebSocket {
  static OPEN = 1;
  static instances: FakeWebSocket[] = [];
  readyState = FakeWebSocket.OPEN;
  binaryType = "";
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  sent: unknown[] = [];

  constructor(public url: string) {
    FakeWebSocket.instances.push(this);
  }

  send(data: unknown): void {
    this.sent.push(data);
  }

  close(): void {
    this.onclose?.();
  }

  emitMessage(data: string): void {
    this.onmessage?.({ data });
  }

  emitOpen(): void {
    this.onopen?.();
  }
}

describe("TranscriptSocket", () => {
  it("parses and forwards valid transcript events", () => {
    const onEvent = vi.fn();
    const socket = new TranscriptSocket({
      url: "ws://localhost:4000/ws/transcribe",
      onEvent,
      WebSocketImpl: FakeWebSocket as unknown as typeof WebSocket,
    });

    socket.connect();
    const fake = FakeWebSocket.instances.at(-1)!;
    fake.emitMessage(
      JSON.stringify({ type: "final", utterance_id: "u1", segment: null, error: null, latency_ms: 42 }),
    );

    expect(onEvent).toHaveBeenCalledWith({
      type: "final",
      utterance_id: "u1",
      segment: null,
      error: null,
      latency_ms: 42,
    });
  });

  it("surfaces a visible error event for malformed server messages instead of throwing/dropping them", () => {
    const onEvent = vi.fn();
    const socket = new TranscriptSocket({
      url: "ws://localhost:4000/ws/transcribe",
      onEvent,
      WebSocketImpl: FakeWebSocket as unknown as typeof WebSocket,
    });

    socket.connect();
    const fake = FakeWebSocket.instances.at(-1)!;

    expect(() => fake.emitMessage("not json")).not.toThrow();
    expect(onEvent).toHaveBeenCalledWith(
      expect.objectContaining({ type: "error", error: expect.stringContaining("malformed") }),
    );
  });

  it("only sends chunks while the socket is open", () => {
    const socket = new TranscriptSocket({
      url: "ws://localhost:4000/ws/transcribe",
      onEvent: vi.fn(),
      WebSocketImpl: FakeWebSocket as unknown as typeof WebSocket,
    });

    socket.connect();
    const fake = FakeWebSocket.instances.at(-1)!;
    const chunk = new ArrayBuffer(4);

    socket.sendChunk(chunk);
    expect(fake.sent).toEqual([chunk]);

    fake.readyState = 3; // CLOSED
    socket.sendChunk(chunk);
    expect(fake.sent).toHaveLength(1); // not sent while closed
  });
});
