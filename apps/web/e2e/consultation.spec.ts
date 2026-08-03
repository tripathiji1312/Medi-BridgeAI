import { expect, test } from "@playwright/test";

// Exercises Blueprint Section 3.2's full pipeline (ASR -> MT -> TTS ->
// diarization) through the real UI, backed by real running gateway/
// speech-pipeline processes in MEDIBRIDGE_FIXTURE_MODE -- deterministic
// canned responses, no model downloads, but a genuine WebSocket round trip
// through the actual application code, not a mocked one (see
// tests/*.test.tsx for the component-level mocked-WebSocket coverage).
test.describe("Consultation flow", () => {
  test("does not start recording until consent is given", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("status").filter({ hasText: "Not recording" })).toBeVisible();
  });

  test("consenting starts a session that produces a bilingual transcript with a speaker chip", async ({
    page,
  }) => {
    await page.goto("/");

    await page.getByRole("button", { name: /consent to audio recording/i }).click();

    // Fake audio device feeds the pre-recorded Hindi fixture (see
    // playwright.config.ts) through the real mic-capture -> WebSocket ->
    // speech-pipeline -> MT -> TTS -> diarization pipeline.
    await expect(page.getByText("mujhe bukhaar hai")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("I have a fever")).toBeVisible();
    await expect(page.getByText(/confidence\)/)).toBeVisible(); // speaker chip

    await expect(page.getByRole("button", { name: /stop consultation/i })).toBeVisible();
  });

  test("stopping the consultation returns to the not-recording, consent-gated state", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("button", { name: /consent to audio recording/i }).click();
    await expect(page.getByRole("button", { name: /stop consultation/i })).toBeVisible({
      timeout: 15_000,
    });

    await page.getByRole("button", { name: /stop consultation/i }).click();

    await expect(
      page.getByRole("button", { name: /consent to audio recording/i }),
    ).toBeVisible();
    await expect(page.getByRole("status").filter({ hasText: "Not recording" })).toBeVisible();
  });
});
