/** Formats a millisecond offset as m:ss for per-utterance timestamps
 * (Blueprint Section 2.1: "per-utterance timestamps"). */
export function formatMsAsTimestamp(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

/** Formats a server-set ISO 8601 wall-clock timestamp (Blueprint Section
 * 2.2's Timeline Generator: "with timestamps") as a local HH:MM:SS clock
 * time -- distinct from formatMsAsTimestamp's audio-relative offsets,
 * since timeline events span the whole session, not one utterance. Falls
 * back to the raw string rather than throwing on an unparseable value
 * (Blueprint Section 1 Principle 3: no silent failure, but also no crash
 * over a display nicety). */
export function formatTimelineTimestamp(isoTimestamp: string): string {
  const date = new Date(isoTimestamp);
  if (Number.isNaN(date.getTime())) {
    return isoTimestamp;
  }
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
