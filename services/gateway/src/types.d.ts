import "fastify";
import type { SessionClaims } from "./auth/jwt";

declare module "fastify" {
  interface FastifyRequest {
    session?: SessionClaims;
  }
}
