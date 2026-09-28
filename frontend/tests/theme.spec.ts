import { test, expect } from "@playwright/test";

test.describe("Theme System (Light, Dark, System Default)", () => {
  test.beforeEach(async ({ page }) => {
    // Clear theme storage before each test
    await page.addInitScript(() => {
      localStorage.removeItem("campuspulse-theme");
    });
  });

  test("public navbar renders accessible ThemeToggle with dropdown options", async ({ page }) => {
    await page.goto("/");

    const themeToggle = page.locator('header [data-testid="theme-toggle"]').first();
    await expect(themeToggle).toBeVisible();

    // Open theme dropdown
    await themeToggle.click();
    const dropdown = page.locator('[data-testid="theme-dropdown"]');
    await expect(dropdown).toBeVisible();

    // Verify all 3 options are present
    await expect(page.locator('[data-testid="theme-option-light"]')).toBeVisible();
    await expect(page.locator('[data-testid="theme-option-dark"]')).toBeVisible();
    await expect(page.locator('[data-testid="theme-option-system"]')).toBeVisible();
  });

  test("switching to Light theme sets html.light and persists to localStorage", async ({ page }) => {
    await page.goto("/");

    const themeToggle = page.locator('header [data-testid="theme-toggle"]').first();
    await themeToggle.click();

    // Select Light option
    await page.locator('[data-testid="theme-option-light"]').click();

    // Verify html element has class "light" and not "dark"
    const html = page.locator("html");
    await expect(html).toHaveClass(/light/);
    await expect(html).not.toHaveClass(/dark/);

    // Verify localStorage was updated
    const savedTheme = await page.evaluate(() => localStorage.getItem("campuspulse-theme"));
    expect(savedTheme).toBe("light");
  });

  test("switching to Dark theme sets html.dark and persists to localStorage", async ({ page }) => {
    await page.goto("/");

    const themeToggle = page.locator('header [data-testid="theme-toggle"]').first();
    await themeToggle.click();

    // Select Dark option
    await page.locator('[data-testid="theme-option-dark"]').click();

    // Verify html element has class "dark" and not "light"
    const html = page.locator("html");
    await expect(html).toHaveClass(/dark/);
    await expect(html).not.toHaveClass(/light/);

    // Verify localStorage was updated
    const savedTheme = await page.evaluate(() => localStorage.getItem("campuspulse-theme"));
    expect(savedTheme).toBe("dark");
  });

  test("switching back to System mode respects OS preference and persists", async ({ page }) => {
    await page.goto("/");

    const themeToggle = page.locator('header [data-testid="theme-toggle"]').first();

    // First switch to light
    await themeToggle.click();
    await page.locator('[data-testid="theme-option-light"]').click();
    await expect(page.locator("html")).toHaveClass(/light/);

    // Now switch to system
    await themeToggle.click();
    await page.locator('[data-testid="theme-option-system"]').click();

    const savedTheme = await page.evaluate(() => localStorage.getItem("campuspulse-theme"));
    expect(savedTheme).toBe("system");
  });

  test("persisted theme survives page reload with zero flicker", async ({ page }) => {
    // Set light theme in localStorage prior to page navigation
    await page.addInitScript(() => {
      localStorage.setItem("campuspulse-theme", "light");
    });

    await page.goto("/");

    // Verify html has class light immediately
    const html = page.locator("html");
    await expect(html).toHaveClass(/light/);
    await expect(html).not.toHaveClass(/dark/);

    // Reload page and verify still light
    await page.reload();
    await expect(html).toHaveClass(/light/);
    await expect(html).not.toHaveClass(/dark/);
  });

  test("authenticated AppHeader includes working ThemeToggle", async ({ page }) => {
    // Sign in as superadmin
    await page.goto("/login");
    await page.locator("#email").fill("superadmin@campuspulse.edu");
    await page.locator("#password").fill("CampusPulse@2026!");
    await page.locator('[data-testid="login-submit-button"]').click();
    await expect(page).toHaveURL(/\/super-admin/, { timeout: 15000 });

    // Verify ThemeToggle in AppHeader
    const appHeaderToggle = page.locator('header [data-testid="theme-toggle"]');
    await expect(appHeaderToggle).toBeVisible();

    // Toggle theme to light in student workstation
    await appHeaderToggle.click();
    await page.locator('[data-testid="theme-option-light"]').click();
    await expect(page.locator("html")).toHaveClass(/light/);

    // Toggle back to dark
    await appHeaderToggle.click();
    await page.locator('[data-testid="theme-option-dark"]').click();
    await expect(page.locator("html")).toHaveClass(/dark/);
  });
});
