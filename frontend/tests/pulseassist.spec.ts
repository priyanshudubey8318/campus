import { test, expect } from "@playwright/test";

test.describe("PulseAssist Institutional Knowledge & Policy Assistant E2E Suite", () => {
  const uid = Date.now();
  const testStudentEmail = `student.pa.${uid}@university.edu`;
  const testPassword = "Password123!";

  test("system status displays PulseAssist RAG subsystem", async ({ page }) => {
    await page.goto("/login");
    await page.locator("#email").fill("superadmin@campuspulse.edu");
    await page.locator("#password").fill("CampusPulse@2026!");
    await page.locator('[data-testid="login-submit-button"]').click();
    await expect(page).toHaveURL(/\/super-admin/, { timeout: 15000 });

    await page.goto("/system-status");
    const main = page.getByRole("main");
    await expect(main.getByText("PulseAssist (RAG)")).toBeVisible();
  });

  test("unauthenticated user accessing /admin/knowledge is redirected to login", async ({ page }) => {
    await page.goto("/admin/knowledge");
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Fadmin%2Fknowledge/);
    await expect(page.getByText("Sign in to CampusPulse")).toBeVisible();
  });

  test("student login displays PulseAssist floating trigger button and drawer interactions", async ({
    page,
  }) => {
    await page.goto("/register");
    await page.locator("#fullName").fill("Priya Sharma");
    await page.locator("#email").fill(testStudentEmail);
    await page.locator("#password").fill(testPassword);
    await page.locator("#confirmPassword").fill(testPassword);
    await page.locator('[data-testid="register-submit-button"]').click();

    // Verify redirected to student dashboard
    await expect(page).toHaveURL(/\/student/, { timeout: 15000 });
    await expect(page.locator('[data-testid="student-portal"]')).toBeVisible();

    // Verify PulseAssist trigger button is visible
    const triggerBtn = page.locator('[data-testid="pulseassist-trigger-btn"]');
    await expect(triggerBtn).toBeVisible();
    await expect(triggerBtn).toContainText("Ask PulseAssist");

    // Click to open drawer
    await triggerBtn.click();

    // Verify drawer opened
    const drawer = page.locator('[data-testid="pulseassist-drawer"]');
    await expect(drawer).toBeVisible();
    await expect(drawer.getByRole("heading", { name: "PulseAssist" })).toBeVisible();
    await expect(drawer.getByText("RAG Subsystem")).toBeVisible();

    // Verify suggested queries are visible
    await expect(drawer.locator('[data-testid="suggested-query-0"]')).toBeVisible();
    await expect(drawer.locator('[data-testid="pulseassist-query-input"]')).toBeVisible();

    // Close drawer
    await page.locator('[data-testid="pulseassist-close-btn"]').click();
    await expect(drawer).not.toHaveClass(/translate-x-0/);
  });

  test("student submits attendance policy inquiry to PulseAssist and receives grounded citation", async ({
    page,
  }) => {
    // 1. Log in as student
    await page.goto("/login");
    await page.locator("#email").fill("student@campuspulse.edu");
    await page.locator("#password").fill("CampusPulse@2026!");
    await page.locator('[data-testid="login-submit-button"]').click();

    await expect(page).toHaveURL(/\/student/, { timeout: 15000 });

    // 2. Open PulseAssist drawer
    const triggerBtn = page.locator('[data-testid="pulseassist-trigger-btn"]');
    await expect(triggerBtn).toBeVisible({ timeout: 10000 });
    await triggerBtn.click();

    const drawer = page.locator('[data-testid="pulseassist-drawer"]');
    await expect(drawer).toBeVisible();

    // 3. Ask policy question using suggested query #0 (minimum attendance required)
    const suggestedQueryBtn = drawer.locator('[data-testid="suggested-query-0"]');
    await expect(suggestedQueryBtn).toBeVisible();
    await suggestedQueryBtn.click();

    // 4. Verify assistant response and citation
    const assistantMsg = page.locator('[data-testid="message-assistant"]').first();
    await expect(assistantMsg).toBeVisible({ timeout: 25000 });
    await expect(assistantMsg).toContainText("attendance");

    // 5. Verify grounded citation pill for POL-ACAD-2026
    const citationPill = page.locator('[data-testid="citation-pill-POL-ACAD-2026"]');
    await expect(citationPill).toBeVisible({ timeout: 10000 });

    // 6. Click citation to open explainability modal
    await citationPill.click();
    const modal = page.locator('[data-testid="why-seeing-modal"]');
    await expect(modal).toBeVisible();
    await expect(page.locator('[data-testid="why-document-code"]')).toHaveText("POL-ACAD-2026");
  });
});
