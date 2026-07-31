import Fastify, { type FastifyInstance } from "fastify";
import cors from "@fastify/cors";
import websocketPlugin from "@fastify/websocket";
import { healthRoutes } from "./routes/health";
import { requireAuth } from "./middleware/requireAuth";
import { registerTranscribeProxy } from "./ws/transcribeProxy";

export interface BuildAppOptions {
  jwtSecret: string;
  speechPipelineWsUrl: string;
}

export async function buildApp(options: BuildAppOptions): Promise<FastifyInstance> {
  const app = Fastify({ logger: false });

  await app.register(cors, { origin: true });
  await app.register(websocketPlugin);
  await app.register(healthRoutes);
  await registerTranscribeProxy(app, { upstreamUrl: options.speechPipelineWsUrl });

  // Example of a route boundary that will require auth once real session
  // routes exist (Phase 3+). Registered now so the auth stub has coverage.
  app.get("/session/whoami", { preHandler: requireAuth(options.jwtSecret) }, async (request) => {
    return request.session;
  });

  return app;
}
