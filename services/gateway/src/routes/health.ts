import type { FastifyInstance } from "fastify";
import type { HealthResponse } from "@medibridge/shared-types";

const SERVICE_NAME = "gateway";
const SERVICE_VERSION = "0.1.0";

export async function healthRoutes(app: FastifyInstance) {
  app.get("/health", async (): Promise<HealthResponse> => {
    return { status: "ok", service: SERVICE_NAME, version: SERVICE_VERSION };
  });
}
