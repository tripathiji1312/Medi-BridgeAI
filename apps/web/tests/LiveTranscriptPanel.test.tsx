import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { LiveTranscriptPanel } from "../src/components/panels/LiveTranscriptPanel";
import { ThemeProvider } from "../src/theme/ThemeProvider";

class FakeWebSocket {
  static OPEN = 1;
  static instances: FakeWebSocket[] = [];
  readyState = FakeWebSocket.OPEN;
  binaryType = "";
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;

  constructor(public url: string) {
    FakeWebSocket.instances.push(this);
  }

  send(): void {
    // no-op for these UI-level tests
  }

  close(): void {
    this.onclose?.();
  }
}

function makeFakeMediaStream(): MediaStream {
  const track = { stop: vi.fn() };
  return { getTracks: () => [track] } as unknown as MediaStream;
}

// This UI test doesn't need real Web Audio behavior, only that
// useAudioCapture.start() resolves without throwing once mic access is
// granted -- a minimal fake AudioContext suffices.
function makeFakeAudioContext() {
  return {
    sampleRate: 16_000,
    createMediaStreamSource: () => ({ connect: vi.fn() }),
    createScriptProcessor: () => ({ onaudioprocess: null, connect: vi.fn(), disconnect: vi.fn() }),
    destination: {},
    close: vi.fn().mockResolvedValue(undefined),
  };
}

describe("LiveTranscriptPanel", () => {
  it("does not start recording until the user clicks the consent button", () => {
    render(
      <ThemeProvider>
        <LiveTranscriptPanel />
      </ThemeProvider>,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Not recording");
    expect(screen.getByRole("button", { name: /consent to audio recording/i })).toBeInTheDocument();
  });

  it("shows a visible error banner when the server reports an error, rather than failing silently", async () => {
    vi.stubGlobal("WebSocket", FakeWebSocket as unknown as typeof WebSocket);
    vi.stubGlobal(
      "navigator",
      Object.assign({}, navigator, {
        mediaDevices: { getUserMedia: vi.fn().mockResolvedValue(makeFakeMediaStream()) },
      }),
    );
    // jsdom has no AudioContext at all; without a stub, useAudioCapture's
    // start() would throw "AudioContext is not defined" and that error
    // would shadow the socket-level assertions this test cares about.
    vi.stubGlobal(
      "AudioContext",
      vi.fn().mockImplementation(() => makeFakeAudioContext()),
    );

    render(
      <ThemeProvider>
        <LiveTranscriptPanel />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: /consent to audio recording/i }));

    await waitFor(() => expect(FakeWebSocket.instances.length).toBeGreaterThan(0));
    const socket = FakeWebSocket.instances.at(-1)!;

    act(() => {
      socket.onmessage?.({
        data: JSON.stringify({
          type: "error",
          utterance_id: "n/a",
          segment: null,
          error: "ASR model not installed",
          latency_ms: null,
        }),
      });
    });

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("ASR model not installed");
    });

    vi.unstubAllGlobals();
  });

  it("renders finalized transcript text as it arrives", async () => {
    vi.stubGlobal("WebSocket", FakeWebSocket as unknown as typeof WebSocket);
    vi.stubGlobal(
      "navigator",
      Object.assign({}, navigator, {
        mediaDevices: { getUserMedia: vi.fn().mockResolvedValue(makeFakeMediaStream()) },
      }),
    );
    // jsdom has no AudioContext at all; without a stub, useAudioCapture's
    // start() would throw "AudioContext is not defined" and that error
    // would shadow the socket-level assertions this test cares about.
    vi.stubGlobal(
      "AudioContext",
      vi.fn().mockImplementation(() => makeFakeAudioContext()),
    );

    render(
      <ThemeProvider>
        <LiveTranscriptPanel />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: /consent to audio recording/i }));
    await waitFor(() => expect(FakeWebSocket.instances.length).toBeGreaterThan(0));
    const socket = FakeWebSocket.instances.at(-1)!;

    act(() => {
      socket.onmessage?.({
        data: JSON.stringify({
          type: "final",
          utterance_id: "u1",
          segment: {
            text: "mujhe bukhaar hai",
            is_final: true,
            confidence: 0.91,
            start_ms: 0,
            end_ms: 900,
            language: "hi",
          },
          error: null,
          latency_ms: 120,
        }),
      });
    });

    await waitFor(() => {
      expect(screen.getByText("mujhe bukhaar hai")).toBeInTheDocument();
    });

    vi.unstubAllGlobals();
  });

  it("renders the English translation and a playable audio element when TTS succeeds", async () => {
    vi.stubGlobal("WebSocket", FakeWebSocket as unknown as typeof WebSocket);
    vi.stubGlobal(
      "navigator",
      Object.assign({}, navigator, {
        mediaDevices: { getUserMedia: vi.fn().mockResolvedValue(makeFakeMediaStream()) },
      }),
    );
    vi.stubGlobal(
      "AudioContext",
      vi.fn().mockImplementation(() => makeFakeAudioContext()),
    );

    render(
      <ThemeProvider>
        <LiveTranscriptPanel />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: /consent to audio recording/i }));
    await waitFor(() => expect(FakeWebSocket.instances.length).toBeGreaterThan(0));
    const socket = FakeWebSocket.instances.at(-1)!;

    act(() => {
      socket.onmessage?.({
        data: JSON.stringify({
          type: "final",
          utterance_id: "u1",
          segment: {
            text: "mujhe bukhaar hai",
            is_final: true,
            confidence: 0.91,
            start_ms: 0,
            end_ms: 900,
            language: "hi",
          },
          error: null,
          latency_ms: 120,
          translation: { text: "I have a fever", source_language: "hi", target_language: "en" },
          translation_error: null,
          tts: { audio_base64: btoa("fake-pcm-bytes"), sample_rate: 16_000, format: "pcm16" },
          tts_error: null,
        }),
      });
    });

    await waitFor(() => {
      expect(screen.getByText("I have a fever")).toBeInTheDocument();
    });
    const audioEl = document.querySelector("audio");
    expect(audioEl).not.toBeNull();
    expect(audioEl?.getAttribute("src")).toMatch(/^data:audio\/wav;base64,/);

    vi.unstubAllGlobals();
  });

  it("shows a degraded-mode warning (not a silent gap) when translation fails", async () => {
    vi.stubGlobal("WebSocket", FakeWebSocket as unknown as typeof WebSocket);
    vi.stubGlobal(
      "navigator",
      Object.assign({}, navigator, {
        mediaDevices: { getUserMedia: vi.fn().mockResolvedValue(makeFakeMediaStream()) },
      }),
    );
    vi.stubGlobal(
      "AudioContext",
      vi.fn().mockImplementation(() => makeFakeAudioContext()),
    );

    render(
      <ThemeProvider>
        <LiveTranscriptPanel />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: /consent to audio recording/i }));
    await waitFor(() => expect(FakeWebSocket.instances.length).toBeGreaterThan(0));
    const socket = FakeWebSocket.instances.at(-1)!;

    act(() => {
      socket.onmessage?.({
        data: JSON.stringify({
          type: "final",
          utterance_id: "u1",
          segment: {
            text: "mujhe bukhaar hai",
            is_final: true,
            confidence: 0.91,
            start_ms: 0,
            end_ms: 900,
            language: "hi",
          },
          error: null,
          latency_ms: 120,
          translation: null,
          translation_error: "MT provider unavailable",
          tts: null,
          tts_error: null,
        }),
      });
    });

    await waitFor(() => {
      expect(screen.getByText("mujhe bukhaar hai")).toBeInTheDocument();
    });
    expect(screen.getByText(/Translation unavailable: MT provider unavailable/)).toBeInTheDocument();

    vi.unstubAllGlobals();
  });

  it("shows the speaker chip with timestamps and lets the clinician assign a role", async () => {
    vi.stubGlobal("WebSocket", FakeWebSocket as unknown as typeof WebSocket);
    vi.stubGlobal(
      "navigator",
      Object.assign({}, navigator, {
        mediaDevices: { getUserMedia: vi.fn().mockResolvedValue(makeFakeMediaStream()) },
      }),
    );
    vi.stubGlobal(
      "AudioContext",
      vi.fn().mockImplementation(() => makeFakeAudioContext()),
    );

    render(
      <ThemeProvider>
        <LiveTranscriptPanel />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: /consent to audio recording/i }));
    await waitFor(() => expect(FakeWebSocket.instances.length).toBeGreaterThan(0));
    const socket = FakeWebSocket.instances.at(-1)!;

    act(() => {
      socket.onmessage?.({
        data: JSON.stringify({
          type: "final",
          utterance_id: "u1",
          segment: {
            text: "mujhe bukhaar hai",
            is_final: true,
            confidence: 0.91,
            start_ms: 1000,
            end_ms: 3500,
            language: "hi",
          },
          error: null,
          latency_ms: 120,
          translation: null,
          translation_error: null,
          tts: null,
          tts_error: null,
          speaker: { speaker_label: "speaker_a", confidence: 0.95 },
          speaker_error: null,
        }),
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/95% confidence/)).toBeInTheDocument();
    });
    expect(screen.getByText("0:01–0:03")).toBeInTheDocument();
    expect(screen.getByText(/Unassigned \(95% confidence\)/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Assign role for speaker_a"), { target: { value: "doctor" } });

    await waitFor(() => {
      expect(screen.getByText(/Doctor \(95% confidence\)/)).toBeInTheDocument();
    });

    vi.unstubAllGlobals();
  });

  it("shows the confidence badge and a miscommunication alert with its reason", async () => {
    vi.stubGlobal("WebSocket", FakeWebSocket as unknown as typeof WebSocket);
    vi.stubGlobal(
      "navigator",
      Object.assign({}, navigator, {
        mediaDevices: { getUserMedia: vi.fn().mockResolvedValue(makeFakeMediaStream()) },
      }),
    );
    vi.stubGlobal(
      "AudioContext",
      vi.fn().mockImplementation(() => makeFakeAudioContext()),
    );
    // ConversationMemoryPanel fetches once a session_id is present.
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ session_id: "s1", utterances: [], case_memory: [] }),
      }),
    );

    render(
      <ThemeProvider>
        <LiveTranscriptPanel />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: /consent to audio recording/i }));
    await waitFor(() => expect(FakeWebSocket.instances.length).toBeGreaterThan(0));
    const socket = FakeWebSocket.instances.at(-1)!;

    act(() => {
      socket.onmessage?.({
        data: JSON.stringify({
          type: "final",
          utterance_id: "u1",
          session_id: "s1",
          segment: {
            text: "mujhe bukhaar hai",
            is_final: true,
            confidence: 0.8,
            start_ms: 0,
            end_ms: 900,
            language: "hi",
          },
          error: null,
          latency_ms: 120,
          miscommunication: {
            consistent: false,
            similarity_score: 0.3,
            negation_flip_detected: true,
            reason: "Negation mismatch between the original and its back-translation.",
          },
          confidence_v2: 0.55,
          confidence_band: "red",
        }),
      });
    });

    await waitFor(() => {
      expect(screen.getByText("Confidence: 55%")).toBeInTheDocument();
    });
    expect(screen.getByText(/negation mismatch/i)).toBeInTheDocument();
    // Conversation memory panel picked up the session id from the event.
    await waitFor(() => {
      expect(screen.getByText(/Tracking 0 utterances/i)).toBeInTheDocument();
    });

    vi.unstubAllGlobals();
  });

  it("highlights medical entities inline and lists them in the categorized panel", async () => {
    vi.stubGlobal("WebSocket", FakeWebSocket as unknown as typeof WebSocket);
    vi.stubGlobal(
      "navigator",
      Object.assign({}, navigator, {
        mediaDevices: { getUserMedia: vi.fn().mockResolvedValue(makeFakeMediaStream()) },
      }),
    );
    vi.stubGlobal(
      "AudioContext",
      vi.fn().mockImplementation(() => makeFakeAudioContext()),
    );

    render(
      <ThemeProvider>
        <LiveTranscriptPanel />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: /consent to audio recording/i }));
    await waitFor(() => expect(FakeWebSocket.instances.length).toBeGreaterThan(0));
    const socket = FakeWebSocket.instances.at(-1)!;

    act(() => {
      socket.onmessage?.({
        data: JSON.stringify({
          type: "final",
          utterance_id: "u1",
          segment: {
            text: "mujhe bukhaar hai",
            is_final: true,
            confidence: 0.91,
            start_ms: 0,
            end_ms: 900,
            language: "hi",
          },
          error: null,
          latency_ms: 120,
          translation: { text: "I have a fever", source_language: "hi", target_language: "en" },
          translation_error: null,
          entities: null,
          entities_error: null,
          translation_entities: [
            {
              text: "fever",
              category: "symptom",
              canonical_name: "fever",
              canonical_code: "R50.9",
              definition: "An elevated body temperature, often a sign of infection or illness.",
              confidence: 1.0,
              start_char: 9,
              end_char: 14,
              is_fuzzy_match: false,
            },
          ],
          translation_entities_error: null,
        }),
      });
    });

    await waitFor(() => {
      const mark = screen.getByText("fever");
      expect(mark.tagName).toBe("MARK");
    });
    expect(screen.getByText("Symptoms")).toBeInTheDocument();

    vi.unstubAllGlobals();
  });

  it("shows a degraded-mode warning when entity extraction fails, without dropping the transcript text", async () => {
    vi.stubGlobal("WebSocket", FakeWebSocket as unknown as typeof WebSocket);
    vi.stubGlobal(
      "navigator",
      Object.assign({}, navigator, {
        mediaDevices: { getUserMedia: vi.fn().mockResolvedValue(makeFakeMediaStream()) },
      }),
    );
    vi.stubGlobal(
      "AudioContext",
      vi.fn().mockImplementation(() => makeFakeAudioContext()),
    );

    render(
      <ThemeProvider>
        <LiveTranscriptPanel />
      </ThemeProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: /consent to audio recording/i }));
    await waitFor(() => expect(FakeWebSocket.instances.length).toBeGreaterThan(0));
    const socket = FakeWebSocket.instances.at(-1)!;

    act(() => {
      socket.onmessage?.({
        data: JSON.stringify({
          type: "final",
          utterance_id: "u1",
          segment: {
            text: "mujhe bukhaar hai",
            is_final: true,
            confidence: 0.91,
            start_ms: 0,
            end_ms: 900,
            language: "hi",
          },
          error: null,
          latency_ms: 120,
          entities: null,
          entities_error: "clinical-nlp unavailable",
        }),
      });
    });

    await waitFor(() => {
      expect(screen.getByText("mujhe bukhaar hai")).toBeInTheDocument();
    });
    expect(screen.getByText(/Medical term detection unavailable: clinical-nlp unavailable/)).toBeInTheDocument();

    vi.unstubAllGlobals();
  });
});
