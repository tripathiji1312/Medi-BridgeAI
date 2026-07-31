import { buildApp } from "./app";

const PORT = Number(process.env.GATEWAY_PORT ?? 4000);
const JWT_SECRET = process.env.JWT_SECRET ?? "dev-only-change-me";

async function main() {
  const app = await buildApp({ jwtSecret: JWT_SECRET });
  await app.listen({ port: PORT, host: "0.0.0.0" });
  console.log(`gateway listening on :${PORT}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
