import { buildApp } from "./app";

const PORT = Number(process.env.GATEWAY_PORT ?? 4000);
const JWT_SECRET = process.env.JWT_SECRET ?? "dev-only-change-me";
const SPEECH_PIPELINE_WS_URL =
  process.env.SPEECH_PIPELINE_WS_URL ?? "ws://localhost:8001/ws/transcribe";

async function main() {
  const app = await buildApp({ jwtSecret: JWT_SECRET, speechPipelineWsUrl: SPEECH_PIPELINE_WS_URL });
  await app.listen({ port: PORT, host: "0.0.0.0" });
  console.log(`gateway listening on :${PORT}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
