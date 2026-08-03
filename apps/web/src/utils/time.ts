/** Formats a millisecond offset as m:ss for per-utterance timestamps
 * (Blueprint Section 2.1: "per-utterance timestamps"). */
export function formatMsAsTimestamp(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}
