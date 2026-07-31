import jwt from "jsonwebtoken";

/**
 * Phase 0 auth stub: symmetric-secret JWT for local dev only.
 * NOT the blueprint's target auth (OAuth2/OIDC + MFA, Section 4/9) — that is
 * explicitly Phase 9 scope. Documented in docs/PROGRESS.md as a deferred item
 * so this stub is never mistaken for the real thing.
 */
export type Role = "doctor" | "patient" | "admin" | "auditor";

export interface SessionClaims {
  sub: string;
  role: Role;
}

export function signSessionToken(claims: SessionClaims, secret: string, expiresIn: string): string {
  return jwt.sign(claims, secret, { expiresIn: expiresIn as jwt.SignOptions["expiresIn"] });
}

export function verifySessionToken(token: string, secret: string): SessionClaims {
  const decoded = jwt.verify(token, secret);
  if (typeof decoded === "string") {
    throw new Error("Invalid token payload");
  }
  const { sub, role } = decoded as Partial<SessionClaims>;
  if (typeof sub !== "string" || typeof role !== "string") {
    throw new Error("Invalid token claims");
  }
  return { sub, role: role as Role };
}
