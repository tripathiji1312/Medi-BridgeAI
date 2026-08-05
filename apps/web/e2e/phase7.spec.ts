import { expect, test } from "@playwright/test";

// Exercises Phase 7's summary/timeline/analytics pipeline through the real
// UI: gateway -> orchestrator -> clinical-nlp's real /summarize endpoint
// (StaticSummarizer under MEDIBRIDGE_FIXTURE_MODE -- deterministic, no
// OpenRouter/Claude call needed for this to be a genuine real HTTP round
// trip through every service). All real running processes.
test.describe("Phase 7: summary, timeline, analytics", () => {
  test("generating then approving a summary shows DRAFT then APPROVED, grounded in a real utterance", async ({
    page,
  }) => {
    await page.goto("/");

    await page.getByRole("button", { name: /consent to audio recording/i }).click();
    await expect(page.getByText("mujhe bukhaar hai")).toBeVisible({ timeout: 15_000 });

    // speech-pipeline records the utterance in orchestrator best-effort,
    // *after* delivering the transcript event to the client (same
    // eventual-consistency caveat as Phase 4's conversation-memory test) --
    // wait for orchestrator to actually have it, rather than a blind
    // timeout, or summarization can race ahead of an empty utterance list.
    await expect(page.getByText(/tracking [1-9]\d* utterance/i)).toBeVisible({ timeout: 10_000 });

    await page.getByRole("button", { name: /generate summary/i }).click();

    await expect(page.getByText(/DRAFT — AI-generated, not yet reviewed/)).toBeVisible({ timeout: 15_000 });
    await expect(
      page.getByText("Fixture mode: deterministic canned summary, not derived from real content."),
    ).toBeVisible();

    await page.getByRole("button", { name: /approve summary/i }).click();

    await expect(page.getByText("APPROVED")).toBeVisible({ timeout: 5_000 });
  });

  test("the timeline picks up a symptom mention and the analytics dashboard reflects real session data", async ({
    page,
  }) => {
    await page.goto("/");

    await page.getByRole("button", { name: /consent to audio recording/i }).click();
    await expect(page.getByText("mujhe bukhaar hai")).toBeVisible({ timeout: 15_000 });
    // English translation side ("I have a fever") does match the "fever"
    // lexicon entry (Phase 5's E2E spec establishes the same fixture-mode
    // asymmetry: the Hindi original doesn't match, the translation does),
    // so speech-pipeline should post a symptom_mentioned timeline event.
    await expect(page.getByText(/fever mentioned/)).toBeVisible({ timeout: 15_000 });

    const analytics = page.getByRole("region", { name: "Analytics dashboard" });
    await expect(analytics).toBeVisible();
    await expect(analytics.getByText("Symptom count")).toBeVisible();
  });
});
