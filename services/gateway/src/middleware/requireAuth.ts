import type { FastifyReply, FastifyRequest } from "fastify";
import { verifySessionToken } from "../auth/jwt";

export function requireAuth(secret: string) {
  return async function requireAuthHandler(request: FastifyRequest, reply: FastifyReply) {
    const header = request.headers.authorization;
    if (!header?.startsWith("Bearer ")) {
      return reply.status(401).send({ error: "missing_token" });
    }
    const token = header.slice("Bearer ".length);
    try {
      request.session = verifySessionToken(token, secret);
    } catch {
      return reply.status(401).send({ error: "invalid_token" });
    }
  };
}
