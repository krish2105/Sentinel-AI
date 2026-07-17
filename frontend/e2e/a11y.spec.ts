import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Accessibility gate: no critical/serious WCAG 2 A/AA violations on key pages.
const PAGES = ["/", "/proxy", "/targets", "/auth", "/dashboard", "/model-card"];

for (const path of PAGES) {
  test(`a11y: ${path} has no critical/serious violations`, async ({ page }) => {
    // NOTE: "load", not "networkidle" — pages with the firewall SSE feed keep a
    // connection open, so networkidle never fires.
    await page.goto(path, { waitUntil: "load" });
    // Contrast must be measured on the settled, fully-opaque state — a mid-fade
    // element composites over the page and reports a false low contrast. Kill
    // transitions/animations and snap any still-fading element to full opacity.
    await page.addStyleTag({
      content:
        "*,*::before,*::after{transition:none!important;animation:none!important}",
    });
    await page.evaluate(() => {
      document
        .querySelectorAll<HTMLElement>("[style*='opacity']")
        .forEach((el) => {
          const o = parseFloat(el.style.opacity);
          if (!Number.isNaN(o) && o < 1) el.style.opacity = "1";
        });
    });
    await page.waitForTimeout(1500);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    const blocking = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious"
    );
    // Surface details in the report when something regresses.
    expect(
      blocking,
      blocking
        .map((v) => `[${v.impact}] ${v.id} (${v.nodes.length}) — ${v.help}`)
        .join("\n")
    ).toEqual([]);
  });
}
