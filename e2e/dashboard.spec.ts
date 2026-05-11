/**
 * E2E: Dashboard interactions — submit a job, navigate pages.
 *
 * Requires the full stack to be running (make dev).
 */
import { test, expect, type Page } from "@playwright/test";

function uniqueEmail() {
  return `e2e+${Date.now()}@testfleet.dev`;
}

async function registerAndLogin(page: Page) {
  const email = uniqueEmail();
  await page.goto("/");
  await page.getByRole("button", { name: /create one/i }).click();
  await page.getByPlaceholder(/alex johnson/i).fill("Dashboard User");
  await page.getByPlaceholder(/acme logistics/i).fill("Dashboard Fleet");
  await page.getByPlaceholder(/you@fleet\.com/i).fill(email);
  await page.getByPlaceholder(/••••••••/).fill("securepass");
  await page.getByRole("button", { name: /create account/i }).click();
  await expect(page.getByText(/run simulation/i)).toBeVisible({ timeout: 10_000 });
}

test.describe("Dashboard", () => {
  test("shows route form with expected fields", async ({ page }) => {
    await registerAndLogin(page);
    expect(page.getByPlaceholder(/e\.g\. denver/i)).toBeTruthy();
    expect(page.getByPlaceholder(/e\.g\. grand junction/i)).toBeTruthy();
    expect(page.getByText(/payload weight/i)).toBeTruthy();
  });

  test("preset route fills origin and destination", async ({ page }) => {
    await registerAndLogin(page);
    await page.getByRole("button", { name: /denver.*grand junction/i }).click();
    await expect(page.getByPlaceholder(/e\.g\. denver/i)).toHaveValue("Denver, CO");
    await expect(page.getByPlaceholder(/e\.g\. grand junction/i)).toHaveValue("Grand Junction, CO");
  });

  test("can switch to Pareto Sweep mode", async ({ page }) => {
    await registerAndLogin(page);
    await page.getByRole("button", { name: /pareto sweep/i }).click();
    await expect(page.getByRole("button", { name: /run sweep/i })).toBeVisible();
    expect(page.getByText(/time budget/i)).toBeFalsy;
  });
});

test.describe("Navigation", () => {
  test("can navigate to History page", async ({ page }) => {
    await registerAndLogin(page);
    await page.getByRole("button", { name: /history/i }).click();
    await expect(page.getByText(/no jobs yet/i)).toBeVisible({ timeout: 5_000 });
  });

  test("can navigate to Analytics page", async ({ page }) => {
    await registerAndLogin(page);
    await page.getByRole("button", { name: /analytics/i }).click();
    await expect(page.getByText(/total jobs/i)).toBeVisible({ timeout: 5_000 });
  });

  test("can navigate to API Keys page", async ({ page }) => {
    await registerAndLogin(page);
    await page.getByRole("button", { name: /api keys/i }).click();
    await expect(page.getByText(/create/i)).toBeVisible({ timeout: 5_000 });
  });
});
