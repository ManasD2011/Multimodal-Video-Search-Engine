import { expect, test } from "@playwright/test";

test("search explains the unavailable index and navigation reaches the library", async ({ page }) => {
  await page.route("**/healthz", async (route) => {
    await route.fulfill({ json: { status: "ok", search_ready: false } });
  });
  await page.route("**/videos", async (route) => {
    await route.fulfill({ json: [] });
  });
  await page.route("**/search", async (route) => {
    await route.fulfill({
      status: 503,
      json: { detail: "Search is unavailable because no retrieval index is configured." },
    });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: /find a moment/i })).toBeVisible();
  await page.getByRole("textbox", { name: /search video library/i }).fill("a red umbrella");
  await page.getByRole("button", { name: /search/i }).last().click();
  await expect(page.getByRole("alert")).toContainText("Search index is not connected");
  await page.getByRole("link", { name: /library/i }).click();
  await expect(page.getByRole("heading", { name: /video library/i })).toBeVisible();
});

test("theme preference persists and system mode follows the OS", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Dark" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect.poll(() => page.evaluate(() => localStorage.getItem("vs-theme"))).toBe("dark");

  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.emulateMedia({ colorScheme: "dark" });
  await page.getByRole("button", { name: "System" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme-pref", "system");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

  await page.keyboard.press("Control+k");
  await expect(page.getByRole("dialog", { name: "Command palette" })).toBeVisible();
  await page.getByRole("textbox", { name: "Filter commands" }).fill("ol");
  await expect(page.getByRole("option", { name: /open library/i })).toBeVisible();
  await page.keyboard.press("Escape");
  await page.keyboard.press("Shift+/");
  await expect(page.getByText("KEYBOARD SHORTCUTS")).toBeVisible();
});

test("upload, read back, and delete a local library video through the real API", async ({ page }) => {
  await page.goto("/library");
  await page.getByRole("button", { name: "Add videos" }).first().click();
  await page.locator('input[type="file"]').setInputFiles({
    name: "browser-flow.mp4",
    mimeType: "video/mp4",
    buffer: Buffer.from("synthetic test clip"),
  });
  await expect(page.getByText(/browser-flow\.mp4.*stored/i)).toBeVisible();
  await page.getByRole("button", { name: "Done" }).click();
  await expect(page.getByRole("button", { name: "Preview browser-flow.mp4" })).toBeVisible();

  page.once("dialog", (dialog) => void dialog.accept());
  await page.getByRole("button", { name: "Delete browser-flow.mp4" }).click();
  await expect(page.getByText("Add your first video")).toBeVisible();
});
