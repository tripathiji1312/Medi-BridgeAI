/**
 * Proxy to orchestrator's session-memory API (Blueprint Section 2.4:
 * "Conversation Memory Status ... editable/removable by clinician"). Only
 * the clinician-facing reads/removes are exposed here -- appending
 * utterances/case-memory entries happens service-to-service
 * (speech-pipeline/clinical-nlp -> orchestrator directly), never through a
 * browser-initiated request, so there's no gateway route for those.
 *
 * Dismissed-alerts, summary/generate, and summary/approve are all
 * browser-initiated writes (Blueprint Section 2.2: dismissing an alert
 * requires a typed reason; Section 2.4: "AI Consultation Summary (draft,
 * clinician must review/approve before export -- never auto-finalized)"
 * -- both generation and approval are explicit clinician actions) --
 * unlike case-memory/timeline-events, these genuinely originate in the
 * browser, not another service. Timeline events themselves have no
 * separate gateway route -- they're posted service-to-service by
 * speech-pipeline directly to orchestrator, and read back as part of
 * GET .../memory's `timeline` field, same as utterances/case_memory.
 *
 * Gateway boundary rule (AGENT_INSTRUCTIONS.md Section 2): routing only,
 * no reinterpretation of orchestrator's response body.
 */

import type { FastifyInstance } from "fastify";

export interface MemoryProxyOptions {
  orchestratorUrl: string;
}

export async function registerMemoryProxy(app: FastifyInstance, options: MemoryProxyOptions): Promise<void> {
  const base = options.orchestratorUrl.replace(/\/$/, "");

  app.get("/sessions/:sessionId/memory", async (request, reply) => {
    const { sessionId } = request.params as { sessionId: string };
    try {
      const upstream = await fetch(`${base}/sessions/${encodeURIComponent(sessionId)}/memory`);
      const body = await upstream.json();
      return reply.status(upstream.status).send(body);
    } catch (err) {
      // Fail loud, not silent (Blueprint Section 1 Principle 3): the
      // client needs to know memory is unreachable, not see a blank panel.
      return reply.status(503).send({
        error: "orchestrator_unavailable",
        detail: err instanceof Error ? err.message : String(err),
      });
    }
  });

  app.post("/sessions/:sessionId/dismissed-alerts", async (request, reply) => {
    const { sessionId } = request.params as { sessionId: string };
    try {
      const upstream = await fetch(`${base}/sessions/${encodeURIComponent(sessionId)}/dismissed-alerts`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request.body),
      });
      const body = await upstream.json();
      return reply.status(upstream.status).send(body);
    } catch (err) {
      return reply.status(503).send({
        error: "orchestrator_unavailable",
        detail: err instanceof Error ? err.message : String(err),
      });
    }
  });

  app.post("/sessions/:sessionId/summary/generate", async (request, reply) => {
    const { sessionId } = request.params as { sessionId: string };
    try {
      // No explicit timeout override here -- the LLM call this triggers
      // can genuinely take longer than every other request this gateway
      // proxies; undici's fetch has no default timeout, so this is a
      // deliberate absence, not an oversight.
      const upstream = await fetch(`${base}/sessions/${encodeURIComponent(sessionId)}/summary/generate`, {
        method: "POST",
      });
      const body = await upstream.json().catch(() => ({}));
      return reply.status(upstream.status).send(body);
    } catch (err) {
      return reply.status(503).send({
        error: "orchestrator_unavailable",
        detail: err instanceof Error ? err.message : String(err),
      });
    }
  });

  app.post("/sessions/:sessionId/summary/approve", async (request, reply) => {
    const { sessionId } = request.params as { sessionId: string };
    try {
      const upstream = await fetch(`${base}/sessions/${encodeURIComponent(sessionId)}/summary/approve`, {
        method: "POST",
      });
      if (upstream.status === 204) {
        return reply.status(204).send();
      }
      const body = await upstream.json().catch(() => ({}));
      return reply.status(upstream.status).send(body);
    } catch (err) {
      return reply.status(503).send({
        error: "orchestrator_unavailable",
        detail: err instanceof Error ? err.message : String(err),
      });
    }
  });

  app.delete("/sessions/:sessionId/case-memory/:entryId", async (request, reply) => {
    const { sessionId, entryId } = request.params as { sessionId: string; entryId: string };
    try {
      const upstream = await fetch(
        `${base}/sessions/${encodeURIComponent(sessionId)}/case-memory/${encodeURIComponent(entryId)}`,
        { method: "DELETE" },
      );
      if (upstream.status === 204) {
        return reply.status(204).send();
      }
      const body = await upstream.json().catch(() => ({}));
      return reply.status(upstream.status).send(body);
    } catch (err) {
      return reply.status(503).send({
        error: "orchestrator_unavailable",
        detail: err instanceof Error ? err.message : String(err),
      });
    }
  });
}
