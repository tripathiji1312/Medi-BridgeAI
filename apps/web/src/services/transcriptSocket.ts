import type { TranscriptEvent } from "@medibridge/shared-types";

export interface TranscriptSocketOptions {
  url: string;
  onEvent: (event: TranscriptEvent) => void;
  onOpen?: () => void;
  onClose?: () => void;
  WebSocketImpl?: typeof WebSocket;
}

/** Thin wrapper around the browser WebSocket, injectable for testing.
 * Malformed server messages produce a visible error event rather than
 * throwing/being silently dropped (Blueprint Section 1 Principle 3). */
export class TranscriptSocket {
  private socket: WebSocket | null = null;

  constructor(private readonly options: TranscriptSocketOptions) {}

  connect(): void {
    const Impl = this.options.WebSocketImpl ?? WebSocket;
    const socket = new Impl(this.options.url);
    socket.binaryType = "arraybuffer";
    socket.onopen = () => this.options.onOpen?.();
    socket.onclose = () => this.options.onClose?.();
    socket.onmessage = (event: MessageEvent<string>) => {
      try {
        const parsed = JSON.parse(event.data) as TranscriptEvent;
        this.options.onEvent(parsed);
      } catch {
        this.options.onEvent({
          type: "error",
          utterance_id: "n/a",
          segment: null,
          error: "Received a malformed transcript event from the server",
          latency_ms: null,
        });
      }
    };
    this.socket = socket;
  }

  sendChunk(chunk: ArrayBuffer): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(chunk);
    }
  }

  close(): void {
    this.socket?.close();
    this.socket = null;
  }
}
