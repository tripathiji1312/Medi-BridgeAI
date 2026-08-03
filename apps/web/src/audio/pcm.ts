/**
 * Pure audio-encoding helpers, deliberately free of any browser API so they
 * can be unit-tested directly (no AudioContext/getUserMedia mocking needed).
 * Used by useAudioCapture to turn mic samples into the PCM16/16kHz mono
 * format app.asr.session.StreamingASRSession expects (speech-pipeline side).
 */

export function downsampleBuffer(
  input: Float32Array,
  inputSampleRate: number,
  outputSampleRate: number,
): Float32Array {
  if (outputSampleRate === inputSampleRate) {
    return input;
  }
  if (outputSampleRate > inputSampleRate) {
    throw new Error("outputSampleRate must be <= inputSampleRate");
  }

  const ratio = inputSampleRate / outputSampleRate;
  const newLength = Math.round(input.length / ratio);
  const result = new Float32Array(newLength);

  let offsetResult = 0;
  let offsetInput = 0;
  while (offsetResult < newLength) {
    const nextOffsetInput = Math.round((offsetResult + 1) * ratio);
    let accum = 0;
    let count = 0;
    for (let i = offsetInput; i < nextOffsetInput && i < input.length; i++) {
      accum += input[i] ?? 0;
      count++;
    }
    result[offsetResult] = count > 0 ? accum / count : 0;
    offsetResult++;
    offsetInput = nextOffsetInput;
  }
  return result;
}

/** RMS amplitude of a frame, normalized to roughly [0, 1] for driving a
 * live level-meter/waveform animation (Blueprint Section 2.4 "waveform
 * animations"). Pure so it's unit-testable without a real AudioContext. */
export function computeRmsLevel(input: Float32Array): number {
  if (input.length === 0) {
    return 0;
  }
  let sumSquares = 0;
  for (let i = 0; i < input.length; i++) {
    const sample = input[i] ?? 0;
    sumSquares += sample * sample;
  }
  const rms = Math.sqrt(sumSquares / input.length);
  return Math.max(0, Math.min(1, rms * 4)); // *4: RMS of typical speech is well under 1.0; scale for a visibly responsive meter
}

/** Converts [-1, 1] float samples to little-endian 16-bit PCM, matching
 * FasterWhisperASRProvider's expected input format on the server side. */
export function floatTo16BitPCM(input: Float32Array): ArrayBuffer {
  const buffer = new ArrayBuffer(input.length * 2);
  const view = new DataView(buffer);
  for (let i = 0; i < input.length; i++) {
    const clamped = Math.max(-1, Math.min(1, input[i] ?? 0));
    view.setInt16(i * 2, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true);
  }
  return buffer;
}
