import { expect, test } from "@playwright/test";

// Exercises Phase 5's entity extraction through the real UI: gateway ->
// speech-pipeline -> clinical-nlp's deterministic lexicon matcher (no
// fixture/static split needed -- it's local and deterministic already).
// StaticMTProvider's fixed translation "I have a fever" contains an exact
// English lexicon match ("fever" -> symptom, R50.9); StaticASRProvider's
// romanized Hindi "mujhe bukhaar hai" has no Devanagari/English lexicon
// variant close enough to match, so the Hindi side is expected to come back
// with no entities -- both are deterministic, non-flaky expectations.
test.describe("Phase 5: medical entity highlighting", () => {
  test("highlights 'fever' inline in the English translation and lists it under Symptoms", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("button", { name: /consent to audio recording/i }).click();

    await expect(page.getByText("mujhe bukhaar hai")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("I have a fever")).toBeVisible();

    const highlighted = page.locator("mark", { hasText: "fever" });
    await expect(highlighted).toBeVisible();
    await expect(highlighted).toHaveAttribute("title", /Symptom: fever \(R50\.9\)/);

    const entitiesPanel = page.getByRole("region", { name: "Medical entities" });
    await expect(entitiesPanel).toBeVisible();
    await expect(entitiesPanel.getByText("Symptoms")).toBeVisible();
    await expect(entitiesPanel.getByText(/fever \(R50\.9\)/)).toBeVisible();
  });
});
