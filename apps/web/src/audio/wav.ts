/**
 * Wraps raw PCM16 mono audio (as sent by speech-pipeline's TTSAudioSegment,
 * Blueprint Section 3.2 step 7) in a minimal WAV header so it can be played
 * via a plain <audio> element -- raw PCM has no container/header and
 * browsers can't play it directly from a data URL without one.
 */
export function pcm16ToWavDataUrl(base64Pcm16: string, sampleRate: number): string {
  const pcmBytes = base64ToBytes(base64Pcm16);
  const wavBytes = wrapPcm16InWavHeader(pcmBytes, sampleRate);
  return `data:audio/wav;base64,${bytesToBase64(wavBytes)}`;
}

function base64ToBytes(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i] ?? 0);
  }
  return btoa(binary);
}

function wrapPcm16InWavHeader(pcmData: Uint8Array, sampleRate: number): Uint8Array {
  const numChannels = 1;
  const bitsPerSample = 16;
  const byteRate = sampleRate * numChannels * (bitsPerSample / 8);
  const blockAlign = numChannels * (bitsPerSample / 8);

  const buffer = new ArrayBuffer(44 + pcmData.length);
  const view = new DataView(buffer);

  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + pcmData.length, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true); // fmt chunk size
  view.setUint16(20, 1, true); // PCM format
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);
  writeString(view, 36, "data");
  view.setUint32(40, pcmData.length, true);

  const bytes = new Uint8Array(buffer);
  bytes.set(pcmData, 44);
  return bytes;
}

function writeString(view: DataView, offset: number, value: string): void {
  for (let i = 0; i < value.length; i++) {
    view.setUint8(offset + i, value.charCodeAt(i));
  }
}
