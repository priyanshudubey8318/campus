import { test, expect } from "@playwright/test";

test.describe("CampusPulse Frontend Smoke Suite", () => {
  test("product landing page loads and displays brand gateways", async ({ page }) => {
    await page.goto("/");

    // Verify browser title
    await expect(page).toHaveTitle(/CampusPulse/);

    // Verify product landing elements
    await expect(page.locator('[data-testid="product-landing-page"]')).toBeVisible();
    await expect(page.getByRole("heading", { name: "Helping students succeed" })).toBeVisible();
    await expect(page.getByText("before challenges become barriers.")).toBeVisible();

    // Verify role workstation cards
    await expect(page.getByText("Role-Based Workstations")).toBeVisible();
    await expect(page.locator('[data-testid="goto-student-portal"]')).toBeVisible();
    await expect(page.locator('[data-testid="goto-faculty-portal"]')).toBeVisible();
    await expect(page.locator('[data-testid="goto-admin-portal"]')).toBeVisible();

    // Verify link to system status
    await expect(page.locator('[data-testid="view-system-status-btn"]')).toBeVisible();
  });

  test("non-superadmin visitor is blocked from system status", async ({ page }) => {
    await page.goto("/system-status");
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Fsystem-status/, { timeout: 10000 });
  });

  test("system status page loads and displays architecture shell and branding for super admin", async ({ page }) => {
    await page.goto("/login");
    await page.locator("#email").fill("superadmin@campuspulse.edu");
    await page.locator("#password").fill("CampusPulse@2026!");
    await page.locator('[data-testid="login-submit-button"]').click();
    await expect(page).toHaveURL(/\/super-admin/, { timeout: 15000 });

    await page.goto("/system-status");

    // Verify main hero elements on relocated architecture shell
    await expect(page.getByRole("heading", { name: "CampusPulse Architecture Shell" })).toBeVisible();
    await expect(page.getByText("Phase 0 Foundation", { exact: true })).toBeVisible();

    // Verify core system status cards
    await expect(page.getByText("FastAPI Runtime")).toBeVisible();
    await expect(page.getByText("PostgreSQL & Alembic")).toBeVisible();
    await expect(page.getByText("Next.js App Shell")).toBeVisible();
  });

  test("domain modules roadmap displays planned subsystems correctly on system status", async ({ page }) => {
    await page.goto("/login");
    await page.locator("#email").fill("superadmin@campuspulse.edu");
    await page.locator("#password").fill("CampusPulse@2026!");
    await page.locator('[data-testid="login-submit-button"]').click();
    await expect(page).toHaveURL(/\/super-admin/, { timeout: 15000 });

    await page.goto("/system-status");

    // Verify roadmap section and cards in main content
    const main = page.getByRole("main");
    await expect(main.getByText("Domain Subsystems Roadmap")).toBeVisible();
    await expect(main.getByText("PulseWatch Subsystem")).toBeVisible();
    await expect(main.getByText("PulseRisk Subsystem")).toBeVisible();
    await expect(main.getByText("PulseAssist (RAG)")).toBeVisible();
    await expect(main.getByText("PulseRecord (Leaves & Claims)")).toBeVisible();
    await expect(main.getByText("PulseCase (Interventions)")).toBeVisible();
  });

  test("system status page dynamically displays live backend health and database connectivity", async ({ page }) => {
    await page.goto("/login");
    await page.locator("#email").fill("superadmin@campuspulse.edu");
    await page.locator("#password").fill("CampusPulse@2026!");
    await page.locator('[data-testid="login-submit-button"]').click();
    await expect(page).toHaveURL(/\/super-admin/, { timeout: 15000 });
    await page.waitForLoadState("networkidle");

    // Intercept and observe the actual live network response from the FastAPI backend
    const [healthResponse] = await Promise.all([
      page.waitForResponse(
        (response) => response.url().includes("/api/v1/health") && response.status() === 200,
        { timeout: 15000 }
      ),
      page.goto("/system-status"),
    ]);

    expect(healthResponse).toBeDefined();

    const livePayload = await healthResponse.json();
    expect(livePayload).toHaveProperty("status");
    expect(livePayload).toHaveProperty("version");
    expect(livePayload).toHaveProperty("uptime_seconds");
    expect(livePayload).toHaveProperty("database");
    expect(livePayload.database).toHaveProperty("dialect");
    expect(livePayload.database).toHaveProperty("connected");

    // Verify browser renders the dynamically retrieved backend status
    const statusLocator = page.locator('[data-testid="backend-status"]');
    await expect(statusLocator).toBeVisible();
    await expect(statusLocator).toHaveText(new RegExp(livePayload.status, "i"));

    // Verify browser renders the dynamically retrieved backend version
    const versionLocator = page.locator('[data-testid="backend-version"]');
    await expect(versionLocator).toBeVisible();
    await expect(versionLocator).toHaveText(livePayload.version);

    // Verify browser renders the dynamically retrieved database dialect
    const dialectLocator = page.locator('[data-testid="db-dialect"]');
    await expect(dialectLocator).toBeVisible();
    await expect(dialectLocator).toHaveText(new RegExp(livePayload.database.dialect, "i"));

    // Verify browser renders database connectivity status matching live backend report
    const dbStatusLocator = page.locator('[data-testid="db-status"]');
    await expect(dbStatusLocator).toBeVisible();
    const expectedDbStatus = livePayload.database.connected ? "Connected" : "Disconnected";
    await expect(dbStatusLocator).toHaveText(expectedDbStatus);

    // Verify live uptime is rendered and active
    const uptimeLocator = page.locator('[data-testid="backend-uptime"]');
    await expect(uptimeLocator).toBeVisible();
    await expect(uptimeLocator).not.toHaveText("Checking...");
    await expect(uptimeLocator).not.toHaveText("Unavailable");
  });
});
