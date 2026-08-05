import { useCallback, useState } from "react";
import { GATEWAY_HTTP_URL } from "../config";

export interface UseDismissAlertOptions {
  fetchImpl?: typeof fetch;
  gatewayHttpUrl?: string;
}

/**
 * Posts an emergency-alert dismissal + its required reason to
 * orchestrator's session memory (Blueprint Section 2.2: "easy dismissal
 * logged for audit" -- a clinician must always give a reason, and it must
 * be recorded, not just cleared from screen). Returns whether the POST
 * itself succeeded so the caller can decide how to react to a logging
 * failure -- see EmergencyAlertCard, which still lets the clinician
 * dismiss visually even if logging failed, but surfaces that failure
 * rather than hiding it (Blueprint Section 1 Principle 3: no silent
 * failure).
 */
export function useDismissAlert(sessionId: string | null, options: UseDismissAlertOptions = {}) {
  const fetchImpl = options.fetchImpl ?? fetch;
  const gatewayHttpUrl = options.gatewayHttpUrl ?? GATEWAY_HTTP_URL;
  const [error, setError] = useState<string | null>(null);

  const dismiss = useCallback(
    async (reason: string, sourceUtteranceId: string | null): Promise<boolean> => {
      if (!sessionId) {
        setError("No active session -- dismissal was not logged.");
        return false;
      }
      try {
        const response = await fetchImpl(`${gatewayHttpUrl}/sessions/${sessionId}/dismissed-alerts`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ reason, source_utterance_id: sourceUtteranceId }),
        });
        if (!response.ok) {
          setError(`Dismissal could not be logged for audit (status ${response.status}).`);
          return false;
        }
        setError(null);
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Dismissal could not be logged for audit.");
        return false;
      }
    },
    [sessionId, fetchImpl, gatewayHttpUrl],
  );

  return { dismiss, error };
}
