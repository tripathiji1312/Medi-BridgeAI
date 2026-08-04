import { useCallback, useEffect, useState } from "react";
import { GATEWAY_HTTP_URL } from "../config";

export interface CaseMemoryEntry {
  id: string;
  category: "symptom" | "medication" | "allergy";
  value: string;
  source_utterance_id: string | null;
}

export interface Utterance {
  id: string;
  speaker: string | null;
  original_text: string;
  translated_text: string | null;
  sequence: number;
}

export interface SessionMemory {
  session_id: string;
  utterances: Utterance[];
  case_memory: CaseMemoryEntry[];
}

export interface UseConversationMemoryOptions {
  fetchImpl?: typeof fetch;
  gatewayHttpUrl?: string;
}

/**
 * Fetches conversation memory (Blueprint Section 2.2/2.4) via gateway's
 * proxy to orchestrator. `refreshTrigger` lets the caller re-fetch on a
 * meaningful event (e.g. a new final transcript) rather than polling --
 * eventually consistent with orchestrator's store, since speech-pipeline
 * records utterances as a best-effort side effect *after* delivering the
 * transcript event to the client (see
 * services/speech-pipeline/app/orchestrator_client.py), so a refresh
 * immediately after a final event can occasionally still show the
 * previous utterance count. Acceptable per Blueprint Section 3.3 (this
 * path may lag); a real push mechanism is a documented follow-up.
 */
export function useConversationMemory(
  sessionId: string | null,
  refreshTrigger: number,
  options: UseConversationMemoryOptions = {},
) {
  const fetchImpl = options.fetchImpl ?? fetch;
  const gatewayHttpUrl = options.gatewayHttpUrl ?? GATEWAY_HTTP_URL;
  const [memory, setMemory] = useState<SessionMemory | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!sessionId) return;
    try {
      const response = await fetchImpl(`${gatewayHttpUrl}/sessions/${sessionId}/memory`);
      if (!response.ok) {
        setError(`Conversation memory unavailable (status ${response.status})`);
        return;
      }
      setMemory((await response.json()) as SessionMemory);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Conversation memory unavailable");
    }
  }, [sessionId, fetchImpl, gatewayHttpUrl]);

  // refreshTrigger is a bump counter (not read inside refresh) that lets
  // the caller force a re-fetch on a meaningful event.
  useEffect(() => {
    void refresh();
  }, [refresh, refreshTrigger]);

  const removeCaseMemoryEntry = useCallback(
    async (entryId: string) => {
      if (!sessionId) return;
      try {
        await fetchImpl(`${gatewayHttpUrl}/sessions/${sessionId}/case-memory/${entryId}`, {
          method: "DELETE",
        });
      } finally {
        await refresh();
      }
    },
    [sessionId, fetchImpl, gatewayHttpUrl, refresh],
  );

  return { memory, error, removeCaseMemoryEntry };
}
