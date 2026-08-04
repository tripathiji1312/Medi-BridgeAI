import { expect, test } from "@playwright/test";

// Exercises Phase 4's cross-service pipeline through the real UI: gateway
// -> speech-pipeline (back-translation + confidence v2) -> clinical-nlp
// (miscommunication check) -> orchestrator (conversation memory), all real
// running processes in MEDIBRIDGE_FIXTURE_MODE. StaticASRProvider (0.92
// confidence) + StaticSimilarityProvider (0.9 similarity, no negation
// markers in either static text) compose to confidence_v2 = 0.91 -> green
// band -- a deterministic, non-flaky expected value.
test.describe("Phase 4: confidence v2 and conversation memory", () => {
  test("shows a green confidence badge and no miscommunication alert on the consistent fixture-mode path", async ({
    page,
  }) => {
    await page.goto("/");

    await page.getByRole("button", { name: /consent to audio recording/i }).click();

    await expect(page.getByText("mujhe bukhaar hai")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("Confidence: 91%")).toBeVisible();
    // StaticSimilarityProvider's fixed 0.9 score and no negation markers in
    // either static text means the consistent path, not the alert one.
    await expect(page.getByText(/possible miscommunication/i)).toHaveCount(0);
  });

  test("the conversation memory panel picks up the session and starts tracking utterances", async ({
    page,
  }) => {
    await page.goto("/");

    await page.getByRole("button", { name: /consent to audio recording/i }).click();
    await expect(page.getByText("mujhe bukhaar hai")).toBeVisible({ timeout: 15_000 });

    const memoryPanel = page.getByRole("region", { name: "Conversation memory" });
    await expect(memoryPanel).toBeVisible();
    // Eventually consistent (speech-pipeline records utterances in
    // orchestrator as a best-effort side effect *after* delivering the
    // transcript event -- see app/orchestrator_client.py) -- assert at
    // least one utterance is tracked rather than an exact count, to avoid
    // a race with exactly how many finals had landed by fetch time.
    await expect(memoryPanel.getByText(/tracking [1-9]\d* utterance/i)).toBeVisible({ timeout: 10_000 });
  });
});
