import { expect, test } from "@playwright/test";

// Blueprint Section 12.4: "Accessibility pass: keyboard-only navigation
// through all panels, screen reader announces live transcript updates and
// emergency alerts." Emergency alerts don't exist yet (Phase 6) -- scoped
// here to what Phase 0-3 actually ships: the disclaimer, the consent
// button, and the live transcript region.
test.describe("Accessibility", () => {
  test("the disclaimer is announced via an ARIA alert region, not just visually styled", async ({ page }) => {
    await page.goto("/");

    const disclaimer = page.getByRole("alert").filter({ hasText: "does not diagnose" });
    await expect(disclaimer).toBeVisible();
  });

  test("the consent button is reachable and operable via keyboard alone, no mouse", async ({ page }) => {
    await page.goto("/");

    // Tab from the top of the document until the consent button has focus,
    // with a bound so a regression (e.g. a focus trap) fails the test
    // instead of looping forever.
    let focused = false;
    for (let i = 0; i < 20; i++) {
      await page.keyboard.press("Tab");
      const isFocused = await page
        .getByRole("button", { name: /consent to audio recording/i })
        .evaluate((el) => el === document.activeElement);
      if (isFocused) {
        focused = true;
        break;
      }
    }
    expect(focused).toBe(true);

    await page.keyboard.press("Enter");

    await expect(page.getByRole("button", { name: /stop consultation/i })).toBeVisible({
      timeout: 15_000,
    });
  });

  test("the transcript region is a live region so a screen reader announces new utterances", async ({
    page,
  }) => {
    await page.goto("/");

    const transcript = page.getByRole("list", { name: "Transcript" });
    await expect(transcript).toHaveAttribute("aria-live", "polite");
  });
});
