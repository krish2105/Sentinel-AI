import { defineConfig, devices } from "@playwright/test";

/**
 * E2E happy-path. Assumes the backend is running at NEXT_PUBLIC_API_URL
 * (default http://localhost:8000) and starts the Next production server itself.
 * Build first: `npm run build` (with NEXT_PUBLIC_API_URL set for the rewrite).
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  expect: { timeout: 15_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  // Cap parallelism so the single dev backend/frontend isn't overwhelmed
  // (avoids navigation-timeout flakes when many pages load at once).
  workers: 4,
  reporter: process.env.CI ? "line" : "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        // The landing hero uses React Three Fiber; enable software WebGL so it
        // renders in headless CI instead of crashing the page.
        launchOptions: {
          args: [
            "--use-gl=angle",
            "--use-angle=swiftshader",
            "--enable-unsafe-swiftshader",
            "--ignore-gpu-blocklist",
          ],
        },
      },
    },
  ],
  webServer: {
    command: "npm run start -- -p 3000",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
