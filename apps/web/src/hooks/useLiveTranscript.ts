import { useCallback, useRef, useState } from "react";
import type { TranscriptEvent } from "@medibridge/shared-types";
import { TranscriptSocket } from "../services/transcriptSocket";
import { useAudioCapture, type AudioContextLike } from "./useAudioCapture";

export interface UseLiveTranscriptOptions {
  gatewayWsUrl: string;
  getUserMedia?: (constraints: MediaStreamConstraints) => Promise<MediaStream>;
  createAudioContext?: () => AudioContextLike;
  WebSocketImpl?: typeof WebSocket;
}

export interface UseLiveTranscriptState {
  /** True once the user has explicitly clicked "start" -- the consent
   * gate (Blueprint Section 14: explicit informed consent before
   * recording starts). Capture never begins on its own. */
  consentGiven: boolean;
  isActive: boolean;
  events: TranscriptEvent[];
  error: string | null;
  start: () => Promise<void>;
  stop: () => void;
}

export function useLiveTranscript(options: UseLiveTranscriptOptions): UseLiveTranscriptState {
  const [consentGiven, setConsentGiven] = useState(false);
  const [events, setEvents] = useState<TranscriptEvent[]>([]);
  const [socketError, setSocketError] = useState<string | null>(null);
  const socketRef = useRef<TranscriptSocket | null>(null);

  const handleChunk = useCallback((chunk: ArrayBuffer) => {
    socketRef.current?.sendChunk(chunk);
  }, []);

  const capture = useAudioCapture({
    onChunk: handleChunk,
    getUserMedia: options.getUserMedia,
    createAudioContext: options.createAudioContext,
  });
  const captureStartRef = useRef(capture.start);
  captureStartRef.current = capture.start;
  const captureStopRef = useRef(capture.stop);
  captureStopRef.current = capture.stop;

  const start = useCallback(async () => {
    setConsentGiven(true);
    setSocketError(null);
    setEvents([]);

    const socket = new TranscriptSocket({
      url: options.gatewayWsUrl,
      WebSocketImpl: options.WebSocketImpl,
      onEvent: (event) => {
        setEvents((prev) => [...prev, event]);
        if (event.type === "error") {
          // Fail loud: surface transcription errors, never drop silently
          // (Blueprint Section 1 Principle 3).
          setSocketError(event.error ?? "Unknown transcription error");
        }
      },
      onOpen: () => {
        void captureStartRef.current();
      },
      onClose: () => {
        captureStopRef.current();
      },
    });
    socketRef.current = socket;
    socket.connect();
  }, [options.gatewayWsUrl, options.WebSocketImpl]);

  const stop = useCallback(() => {
    captureStopRef.current();
    socketRef.current?.close();
    socketRef.current = null;
    setConsentGiven(false);
  }, []);

  return {
    consentGiven,
    isActive: capture.isRecording,
    events,
    error: capture.error ?? socketError,
    start,
    stop,
  };
}
