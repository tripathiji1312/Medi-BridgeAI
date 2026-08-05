import { expect, test } from "@playwright/test";

// Exercises Phase 6's risk/emotion pipeline through the real UI: gateway ->
// speech-pipeline (emergency detection -> emotion classification -> risk
// scoring, all real running processes) -> clinical-nlp (emergency detector +
// risk scorer). StaticASRProvider's fixed romanized-Hindi text ("mujhe
// bukhaar hai") has no lexicon match (same reason Phase 5's E2E spec
// documents for the Hindi side), so the deterministic expected outcome here
// is Low risk / no symptoms + StaticEmotionClassifier's fixed Neutral
// result -- both computed by the real route logic against real running
// services, not asserted in isolation.
//
// A genuine "emergency banner fires" scenario isn't covered here since
// StaticASRProvider's canned text isn't configurable per E2E run without
// changing what phase4/phase5's specs already depend on -- that path is
// covered instead at the unit/integration level (clinical-nlp's emergency
// route tests, speech-pipeline's enrichment-chain tests with a stub
// emergency detector reporting alert=true, and apps/web's
// EmergencyAlertCard/LiveTranscriptPanel tests simulating the alert
// end-to-end at the React level).
test.describe("Phase 6: risk scoring and emotion indicator", () => {
  test("shows a Low risk badge and a Neutral tone indicator on the deterministic fixture-mode path", async ({
    page,
  }) => {
    await page.goto("/");

    await page.getByRole("button", { name: /consent to audio recording/i }).click();

    await expect(page.getByText("mujhe bukhaar hai")).toBeVisible({ timeout: 15_000 });

    await expect(page.getByText("Low risk")).toBeVisible();
    await expect(page.getByText(/No symptoms or risk signals detected/)).toBeVisible();

    await expect(page.getByText(/Tone: Neutral \(50%\)/)).toBeVisible();
  });

  test("does not show an emergency alert banner on the routine fixture-mode path", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("button", { name: /consent to audio recording/i }).click();
    await expect(page.getByText("mujhe bukhaar hai")).toBeVisible({ timeout: 15_000 });

    await expect(page.getByRole("alertdialog", { name: "Emergency alert" })).toHaveCount(0);
  });
});
