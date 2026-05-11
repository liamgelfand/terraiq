/**
 * E2E: Authentication flows
 *
 * Requires the full stack to be running (make dev).
 * Uses a unique email per run so tests are idempotent.
 */
import { test, expect } from "@playwright/test";

function uniqueEmail() {
  return `e2e+${Date.now()}@testfleet.dev`;
}

test.describe("Registration", () => {
  test("user can register and lands on the dashboard", async ({ page }) => {
    const email = uniqueEmail();

    await page.goto("/");
    await page.getByRole("button", { name: /create one/i }).click();

    await page.getByPlaceholder(/alex johnson/i).fill("E2E User");
    await page.getByPlaceholder(/acme logistics/i).fill("E2E Fleet");
    await page.getByPlaceholder(/you@fleet\.com/i).fill(email);
    await page.getByPlaceholder(/••••••••/).fill("securepass");

    await page.getByRole("button", { name: /create account/i }).click();

    // After registration we should see the dashboard
    await expect(page.getByText(/run simulation/i)).toBeVisible({ timeout: 10_000 });
  });

  test("duplicate email shows an inline error", async ({ page }) => {
    const email = uniqueEmail();

    // First registration
    await page.goto("/");
    await page.getByRole("button", { name: /create one/i }).click();
    await page.getByPlaceholder(/alex johnson/i).fill("First User");
    await page.getByPlaceholder(/acme logistics/i).fill("Fleet 1");
    await page.getByPlaceholder(/you@fleet\.com/i).fill(email);
    await page.getByPlaceholder(/••••••••/).fill("securepass");
    await page.getByRole("button", { name: /create account/i }).click();
    await expect(page.getByText(/run simulation/i)).toBeVisible({ timeout: 10_000 });

    // Logout
    await page.getByRole("button", { name: /sign out/i }).click();

    // Second registration with the same email
    await page.getByRole("button", { name: /create one/i }).click();
    await page.getByPlaceholder(/alex johnson/i).fill("Duplicate User");
    await page.getByPlaceholder(/acme logistics/i).fill("Fleet 2");
    await page.getByPlaceholder(/you@fleet\.com/i).fill(email);
    await page.getByPlaceholder(/••••••••/).fill("password99");
    await page.getByRole("button", { name: /create account/i }).click();

    await expect(page.getByText(/already exists/i)).toBeVisible({ timeout: 5_000 });
  });
});

test.describe("Login / Logout", () => {
  test("user can log in and log out", async ({ page }) => {
    const email = uniqueEmail();

    // Register first
    await page.goto("/");
    await page.getByRole("button", { name: /create one/i }).click();
    await page.getByPlaceholder(/alex johnson/i).fill("Login Test");
    await page.getByPlaceholder(/acme logistics/i).fill("Login Fleet");
    await page.getByPlaceholder(/you@fleet\.com/i).fill(email);
    await page.getByPlaceholder(/••••••••/).fill("securepass");
    await page.getByRole("button", { name: /create account/i }).click();
    await expect(page.getByText(/run simulation/i)).toBeVisible({ timeout: 10_000 });

    // Logout
    await page.getByRole("button", { name: /sign out/i }).click();
    await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();

    // Login again
    await page.getByPlaceholder(/you@fleet\.com/i).fill(email);
    await page.getByPlaceholder(/••••••••/).fill("securepass");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page.getByText(/run simulation/i)).toBeVisible({ timeout: 10_000 });
  });

  test("wrong password shows error message", async ({ page }) => {
    await page.goto("/");
    await page.getByPlaceholder(/you@fleet\.com/i).fill("nobody@fleet.dev");
    await page.getByPlaceholder(/••••••••/).fill("wrongpassword");
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page.getByText(/invalid/i)).toBeVisible({ timeout: 5_000 });
  });
});

test.describe("Forgot Password", () => {
  test("forgot password flow shows confirmation message", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: /forgot password/i }).click();
    await page.getByPlaceholder(/you@fleet\.com/i).fill("anyone@fleet.dev");
    await page.getByRole("button", { name: /send reset link/i }).click();
    await expect(page.getByText(/check the/i)).toBeVisible({ timeout: 5_000 });
  });
});
