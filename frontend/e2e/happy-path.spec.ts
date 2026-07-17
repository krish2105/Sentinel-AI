import { expect, test } from "@playwright/test";

test("landing page renders the hero", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/Sentinel AI/);
  // Nav is present on every page (exact match — the hero also links "Try the firewall").
  await expect(page.getByRole("link", { name: "Firewall", exact: true })).toBeVisible();
});

test("firewall playground blocks a malicious prompt end-to-end", async ({ page }) => {
  await page.goto("/proxy");
  await expect(page.getByRole("heading", { name: "Runtime firewall" })).toBeVisible();

  // The default preset is a malicious prompt with guardrails ON.
  await page.getByRole("button", { name: /Send through proxy/ }).click();

  // The guardrail should stamp BLOCKED (input scan fires on the injection).
  await expect(page.getByText("BLOCKED", { exact: false }).first()).toBeVisible();
});

test("theme toggle switches the document theme", async ({ page }) => {
  await page.goto("/");
  const html = page.locator("html");
  const before = await html.getAttribute("data-theme");
  await page.getByRole("button", { name: /Switch to (light|dark) mode/ }).click();
  await expect(async () => {
    expect(await html.getAttribute("data-theme")).not.toBe(before);
  }).toPass();
});

test("targets page loads", async ({ page }) => {
  await page.goto("/targets");
  // Exact — otherwise the empty-state "No targets yet" heading also matches.
  await expect(
    page.getByRole("heading", { name: "Targets", exact: true })
  ).toBeVisible();
});
