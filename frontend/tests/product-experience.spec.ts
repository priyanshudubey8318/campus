import { test, expect } from "@playwright/test";

test.describe("CampusPulse Phase 2.5 Product Experience E2E Suite", () => {
  const studentEmail = "student@campuspulse.edu";
  const facultyEmail = "faculty@campuspulse.edu";
  const adminEmail = "admin@campuspulse.edu";
  const commonPassword = "CampusPulse@2026!";

  test.describe("1. Product Landing & Public Gateway", () => {
    test("public visitors see product landing with role portals and system status access guard", async ({ page }) => {
      await page.goto("/");
      await expect(page).toHaveTitle(/CampusPulse/);

      // Verify product hero and workstations
      await expect(page.locator('[data-testid="product-landing-page"]')).toBeVisible();
      await expect(page.locator('[data-testid="goto-student-portal"]')).toBeVisible();
      await expect(page.locator('[data-testid="goto-faculty-portal"]')).toBeVisible();
      await expect(page.locator('[data-testid="goto-admin-portal"]')).toBeVisible();

      // Click System Status from hero: unauthenticated visitor is gated by authentication
      await page.locator('[data-testid="view-system-status-btn"]').click();
      await expect(page).toHaveURL(/\/login\?returnUrl=%2Fsystem-status/);

      // Super admin logs in and returnUrl redirects directly to system status
      await page.locator("#email").fill("superadmin@campuspulse.edu");
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();
      await expect(page).toHaveURL(/\/system-status/, { timeout: 15000 });
      await expect(page.locator('[data-testid="system-status-page"]')).toBeVisible();
    });
  });

  test.describe("2. Student Product Experience", () => {
    test("student logs in and interacts with dashboard, coursework, attendance, and support hub", async ({ page }) => {
      // 1. Log in
      await page.goto("/login");
      await page.locator("#email").fill(studentEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();

      // 2. Lands on Student Dashboard
      await expect(page).toHaveURL(/\/student/, { timeout: 15000 });
      await expect(page.locator('[data-testid="student-dashboard"]')).toBeVisible({ timeout: 15000 });

      // Verify Student KPIs
      await expect(page.locator('[data-testid="kpi-registered-courses"]')).toBeVisible();
      await expect(page.locator('[data-testid="kpi-attendance-rate"]')).toBeVisible();
      await expect(page.locator('[data-testid="kpi-coursework-assignments"]')).toBeVisible();
      await expect(page.locator('[data-testid="kpi-graded-evaluations"]')).toBeVisible();

      // Verify Institutional Support Hub entry point
      await expect(page.locator('[data-testid="student-support-hub"]')).toBeVisible();
      await expect(page.getByText("Academic Advising Center")).toBeVisible();
      await expect(page.getByText("Office of the Registrar")).toBeVisible();

      // 3. Navigate to Student Academics
      await page.locator('[data-testid="view-academics-btn"]').click();
      await expect(page).toHaveURL(/\/student\/academics/, { timeout: 15000 });
      await expect(page.locator('[data-testid="student-academics-page"]')).toBeVisible();

      // Test tab switching
      // Tab: Attendance
      await page.locator('[data-testid="tab-attendance"]').click();
      await expect(page.locator('[data-testid="attendance-records-list"]')).toBeVisible();

      // Tab: Assignments
      await page.locator('[data-testid="tab-assignments"]').click();
      await expect(page.getByText("Coursework Assignments Desk")).toBeVisible();

      // Tab: Evaluations
      await page.locator('[data-testid="tab-assessments"]').click();
      await expect(page.getByText("Formal Evaluation Results")).toBeVisible();

      // Tab: Support
      await page.locator('[data-testid="tab-support"]').click();
      await expect(page.getByText("Institutional Academic Support Directory")).toBeVisible();
    });
  });

  test.describe("3. Faculty Product Experience", () => {
    test("faculty logs in, views workstation, and interacts with course workspace", async ({ page }) => {
      // 1. Log in as faculty
      await page.goto("/login");
      await page.locator("#email").fill(facultyEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();

      // 2. Lands on Faculty Dashboard
      await expect(page).toHaveURL(/\/faculty/, { timeout: 15000 });
      await expect(page.locator('[data-testid="faculty-portal"]')).toBeVisible({ timeout: 15000 });

      // Verify KPIs
      await expect(page.locator('[data-testid="kpi-faculty-offerings"]')).toBeVisible();
      await expect(page.locator('[data-testid="kpi-faculty-subjects"]')).toBeVisible();
      await expect(page.locator('[data-testid="kpi-faculty-rbac"]')).toBeVisible();

      // 3. Open Course Management Workspace
      await page.locator('[data-testid="faculty-workspace-btn"]').click();
      await expect(page).toHaveURL(/\/faculty\/courses/, { timeout: 15000 });
      await expect(page.locator('[data-testid="faculty-courses-page"]')).toBeVisible();

      // Verify Course Workspace is active
      await expect(page.locator('[data-testid="course-workspace"]')).toBeVisible();

      // Check Roster table within authorized scope
      await expect(page.locator('[data-testid="course-roster-table"]')).toBeVisible();

      // Test Log Attendance modal open/close
      await page.locator('[data-testid="open-attendance-modal-btn"]').click();
      await expect(page.locator('[data-testid="attendance-student-select"]')).toBeVisible();
      await page.locator('[data-testid="modal-close-button"]').click();

      // Test New Assignment modal open/close
      await page.locator('[data-testid="open-create-assignment-btn"]').click();
      await expect(page.locator('[data-testid="assignment-title-input"]')).toBeVisible();
      await page.locator('[data-testid="modal-close-button"]').click();
    });
  });

  test.describe("4. Administrative Governance Experience", () => {
    test("admin logs in and navigates institutional academic catalog and system telemetry", async ({ page }) => {
      // 1. Log in as admin
      await page.goto("/login");
      await page.locator("#email").fill(adminEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();

      // 2. Lands on Admin Dashboard
      await expect(page).toHaveURL(/\/admin/, { timeout: 15000 });
      await expect(page.locator('[data-testid="admin-portal"]')).toBeVisible({ timeout: 15000 });

      // Verify Admin KPIs
      await expect(page.locator('[data-testid="kpi-admin-courses"]')).toBeVisible();
      await expect(page.locator('[data-testid="kpi-admin-enrollments"]')).toBeVisible();
      await expect(page.locator('[data-testid="kpi-admin-departments"]')).toBeVisible();
      await expect(page.locator('[data-testid="kpi-admin-system-health"]')).toBeVisible();

      // 3. Navigate to Academic Catalog
      await page.locator('[data-testid="goto-academic-catalog-btn"]').click();
      await expect(page).toHaveURL(/\/admin\/academic/, { timeout: 15000 });
      await expect(page.locator('[data-testid="admin-academic-page"]')).toBeVisible();
      await expect(page.locator('[data-testid="admin-courses-table"]')).toBeVisible();
      await expect(page.locator('[data-testid="admin-enrollments-table"]')).toBeVisible();
    });
  });

  test.describe("5. Role Boundary & Authorization Protections", () => {
    test("student is blocked from accessing faculty course workspace and admin portal", async ({ page }) => {
      // Log in as student
      await page.goto("/login");
      await page.locator("#email").fill(studentEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();
      await expect(page).toHaveURL(/\/student/, { timeout: 15000 });

      // Attempt navigation to faculty workspace
      await page.goto("/faculty/courses");
      await expect(page.locator('[data-testid="forbidden-state"]')).toBeVisible({ timeout: 15000 });
      await expect(page.getByText("403 — Access Forbidden")).toBeVisible();

      // Attempt navigation to admin portal
      await page.goto("/admin");
      await expect(page.locator('[data-testid="forbidden-state"]')).toBeVisible({ timeout: 15000 });
      await expect(page.getByText("403 — Access Forbidden")).toBeVisible();
    });

    test("faculty is blocked from accessing admin academic governance", async ({ page }) => {
      // Log in as faculty
      await page.goto("/login");
      await page.locator("#email").fill(facultyEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();
      await expect(page).toHaveURL(/\/faculty/, { timeout: 15000 });

      // Attempt navigation to admin academic catalog
      await page.goto("/admin/academic");
      await expect(page.locator('[data-testid="forbidden-state"]')).toBeVisible({ timeout: 15000 });
      await expect(page.getByText("403 — Access Forbidden")).toBeVisible();
    });
  });
});
