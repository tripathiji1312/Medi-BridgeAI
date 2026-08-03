import { expect, test } from "@playwright/test";

test.describe("Dashboard shell", () => {
  test("loads with the disclaimer, health status, and consultation panel visible", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "MediBridge AI" })).toBeVisible();
    await expect(page.getByRole("alert").filter({ hasText: "does not diagnose" })).toBeVisible();
    await expect(page.getByRole("complementary", { name: "Session status" })).toBeVisible();
    await expect(
      page.getByRole("button", { name: /consent to audio recording/i }),
    ).toBeVisible();
  });

  test("shows the gateway as operational once the fixture-mode backend responds", async ({ page }) => {
    await page.goto("/");

    // The gateway/speech-pipeline webServer entries are real running
    // processes for this test run (fixture mode -- no model downloads),
    // so this is a genuine network round trip, not a mock.
    await expect(page.getByRole("status").first()).toHaveText("All systems operational", {
      timeout: 10_000,
    });
  });
});

test.describe("Dark/light mode", () => {
  test("toggling persists across a full page reload", async ({ page }) => {
    await page.goto("/");

    const toggle = page.getByRole("button", { name: /switch to dark mode/i });
    await toggle.click();
    await expect(page.getByRole("button", { name: /switch to light mode/i })).toBeVisible();

    await page.reload();

    await expect(page.getByRole("button", { name: /switch to light mode/i })).toBeVisible();
  });
});
