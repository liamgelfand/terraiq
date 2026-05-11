import { defineConfig, devices } from "@playwright/test";

/**
 * E2E test configuration.
 *
 * Requires all services to be running:
 *   make dev   (or run Docker + FastAPI + Celery + Vite manually)
 *
 * Run with:
 *   npx playwright test
 *   npx playwright test --ui         (interactive mode)
 *   npx playwright test --headed     (watch the browser)
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",

  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
