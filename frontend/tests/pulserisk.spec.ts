import { test, expect } from "@playwright/test";

test.describe("CampusPulse Phase 4: PulseRisk E2E Test Suite", () => {
  const studentEmail = "student@campuspulse.edu";
  const advisorEmail = "advisor@campuspulse.edu";
  const adminEmail = "admin@campuspulse.edu";
  const commonPassword = "CampusPulse@2026!";

  test.describe("1. Student Experience: Academic Support & Momentum Flow", () => {
    test("student sees Support Priority Card, SPI badge, and opens Explainability Decomposition modal", async ({
      page,
    }) => {
      // 1. Log in as student
      await page.goto("/login");
      await page.locator("#email").fill(studentEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();

      // 2. Lands on Student Dashboard
      await expect(page).toHaveURL(/\/student/, { timeout: 15000 });
      await expect(page.locator('[data-testid="student-dashboard"]')).toBeVisible({ timeout: 15000 });

      // 3. Verify Academic Support Card is visible
      const supportCard = page.locator('[data-testid="pulserisk-support-card"]');
      await expect(supportCard).toBeVisible({ timeout: 10000 });

      // 4. Verify SPI Score & Tier Badge
      await expect(page.locator('[data-testid="pulserisk-spi-score"]')).toBeVisible();
      await expect(page.locator('[data-testid="pulserisk-tier-badge"]')).toBeVisible();

      // 5. Click "Why am I seeing this?" button
      const explainBtn = page.locator('[data-testid="pulserisk-explain-btn"]');
      await expect(explainBtn).toBeVisible();
      await explainBtn.click();

      // 6. Verify Explainability Modal is visible and transparent
      const explainModal = page.locator('[data-testid="pulserisk-explain-modal"]');
      await expect(explainModal).toBeVisible({ timeout: 5000 });

      await expect(page.locator('[data-testid="modal-spi-value"]')).toBeVisible();
      await expect(page.locator('[data-testid="modal-priority-tier"]')).toBeVisible();
      await expect(page.locator('[data-testid="modal-contributions-table"]')).toBeVisible();
      await expect(page.locator('[data-testid="modal-explain-summary"]')).toBeVisible();

      // Verify institutional disclaimer
      await expect(explainModal).toContainText(
        "does not infer personal, disciplinary, or medical circumstances"
      );

      // 7. Close Modal
      await page.locator('[data-testid="modal-close-button"]').click();
      await expect(explainModal).not.toBeVisible();
    });
  });

  test.describe("2. Student Access Restrictions", () => {
    test("student is forbidden from accessing the advisor cohort roster", async ({ page }) => {
      // Log in as student
      await page.goto("/login");
      await page.locator("#email").fill(studentEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();

      await expect(page).toHaveURL(/\/student/, { timeout: 15000 });

      // Attempt navigating directly to /advisor
      await page.goto("/advisor");

      // ProtectedRoute redirects or shows access denied
      await expect(page.locator('[data-testid="advisor-roster-table"]')).not.toBeVisible();
    });
  });

  test.describe("3. Advisor Experience: Support Priority Triage Roster", () => {
    test("advisor accesses triage roster, inspects metrics, filters by tier, and views decomposition", async ({
      page,
    }) => {
      // 1. Log in as advisor
      await page.goto("/login");
      await page.locator("#email").fill(advisorEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();
      await expect(page).toHaveURL(/\/advisor/, { timeout: 15000 });

      // 2. Advisor portal is visible
      await expect(page.locator('[data-testid="advisor-portal"]')).toBeVisible({ timeout: 15000 });

      // 3. Verify KPI summary cards
      await expect(page.locator('[data-testid="kpi-urgent-count"]')).toBeVisible();
      await expect(page.locator('[data-testid="kpi-elevated-count"]')).toBeVisible();
      await expect(page.locator('[data-testid="kpi-moderate-count"]')).toBeVisible();
      await expect(page.locator('[data-testid="kpi-stable-count"]')).toBeVisible();

      // 4. Verify Roster Table
      const rosterTable = page.locator('[data-testid="advisor-roster-table"]');
      await expect(rosterTable).toBeVisible({ timeout: 10000 });

      // 5. Test Filters
      const tierFilter = page.locator('[data-testid="filter-tier-select"]');
      await expect(tierFilter).toBeVisible();
      await tierFilter.selectOption("ALL");

      const driverFilter = page.locator('[data-testid="filter-driver-select"]');
      await expect(driverFilter).toBeVisible();
      await driverFilter.selectOption("ALL");

      // 6. Test Search input
      const searchInput = page.locator('[data-testid="roster-search-input"]');
      await expect(searchInput).toBeVisible();
      await searchInput.fill("STU");

      // 7. Click Decomposition button on the first student row
      const decompBtn = page.locator('[data-testid^="view-decomp-"]').first();
      await expect(decompBtn).toBeVisible({ timeout: 10000 });
      await decompBtn.click();

      // Verify decomposition modal opens with multi-signal breakdown
      const explainModal = page.locator('[data-testid="pulserisk-explain-modal"]');
      await expect(explainModal).toBeVisible({ timeout: 8000 });
      await expect(page.locator('[data-testid="modal-contributions-table"]')).toBeVisible();

      // Close modal
      await page.locator('[data-testid="modal-close-button"]').click();
      await expect(explainModal).not.toBeVisible();
    });
  });

  test.describe("4. Administrator Oversight", () => {
    test("admin can view advisor triage roster with institutional scope", async ({ page }) => {
      // 1. Log in as admin
      await page.goto("/login");
      await page.locator("#email").fill(adminEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();
      await expect(page).toHaveURL(/\/admin/, { timeout: 15000 });

      // 2. Navigate to /advisor
      await page.goto("/advisor");
      await expect(page.locator('[data-testid="advisor-portal"]')).toBeVisible({ timeout: 15000 });

      // 3. Verify Roster Table is accessible
      await expect(page.locator('[data-testid="advisor-roster-table"]')).toBeVisible({ timeout: 10000 });
    });
  });
});
