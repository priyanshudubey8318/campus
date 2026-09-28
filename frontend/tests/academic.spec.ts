import { test, expect } from "@playwright/test";

test.describe("CampusPulse Phase 2 Academic Domain & Profiles E2E Suite", () => {
  const studentEmail = "student@campuspulse.edu";
  const facultyEmail = "faculty@campuspulse.edu";
  const adminEmail = "admin@campuspulse.edu";
  const commonPassword = "CampusPulse@2026!";

  test.describe("Student Academic Experience", () => {
    test("student can log in and view their verified academic profile", async ({ page }) => {
      // 1. Log in as student
      await page.goto("/login");
      await page.locator("#email").fill(studentEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();

      // Verify redirection to student area
      await expect(page).toHaveURL(/\/student/, { timeout: 15000 });

      // 2. Navigate to Student Profile
      await page.goto("/student/profile");
      await expect(page.locator('[data-testid="student-profile-page"]')).toBeVisible({ timeout: 15000 });

      // 3. Verify official institutional student details
      const enrollmentNo = page.locator('[data-testid="student-enrollment-number"]');
      await expect(enrollmentNo).toBeVisible();
      await expect(enrollmentNo).toContainText("STU-2024-001");
      await expect(page.locator('[data-testid="student-profile-page"]').getByText("Aarav Sharma")).toBeVisible();
      await expect(page.locator('[data-testid="student-profile-page"]').getByText("ENROLLED")).toBeVisible();
    });

    test("student can navigate to academics view and verify enrollment and attendance", async ({ page }) => {
      // 1. Log in
      await page.goto("/login");
      await page.locator("#email").fill(studentEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();
      await expect(page).toHaveURL(/\/student/, { timeout: 15000 });

      // 2. Navigate to Academics Dashboard
      await page.goto("/student/academics");
      await expect(page.locator('[data-testid="student-academics-page"]')).toBeVisible({ timeout: 15000 });

      // 3. Verify enrolled courses count and course roster
      await expect(page.locator('[data-testid="enrolled-courses-count"]')).toBeVisible();
      await expect(page.locator('[data-testid="courses-list"]')).toBeVisible();
      await expect(page.locator('[data-testid="courses-list"]').getByText("CS101").first()).toBeVisible();

      // 4. Verify derived attendance percentage rate is rendered
      const attendanceRate = page.locator('[data-testid="attendance-rate"]');
      await expect(attendanceRate).toBeVisible();
      await expect(attendanceRate).toContainText("%");
    });
  });

  test.describe("Faculty Academic Experience", () => {
    test("faculty can log in and view their academic appointment profile", async ({ page }) => {
      // 1. Log in as faculty
      await page.goto("/login");
      await page.locator("#email").fill(facultyEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();

      await expect(page).toHaveURL(/\/faculty/, { timeout: 15000 });

      // 2. Navigate to Faculty Profile
      await page.goto("/faculty/profile");
      await expect(page.locator('[data-testid="faculty-profile-page"]')).toBeVisible({ timeout: 15000 });

      // 3. Verify official employee ID and appointment details
      const employeeId = page.locator('[data-testid="faculty-employee-id"]');
      await expect(employeeId).toBeVisible();
      await expect(employeeId).toContainText("FAC-001");
      await expect(page.getByText("Associate Professor")).toBeVisible();
      await expect(page.locator('[data-testid="faculty-profile-page"]').getByText("Dr. Rajesh Kumar")).toBeVisible();
    });

    test("faculty can view assigned teaching courses and sections", async ({ page }) => {
      // 1. Log in as faculty
      await page.goto("/login");
      await page.locator("#email").fill(facultyEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();
      await expect(page).toHaveURL(/\/faculty/, { timeout: 15000 });

      // 2. Navigate to Faculty Courses
      await page.goto("/faculty/courses");
      await expect(page.locator('[data-testid="faculty-courses-page"]')).toBeVisible({ timeout: 15000 });

      // 3. Verify course assignments grid is rendered
      const grid = page.locator('[data-testid="faculty-assignments-grid"]');
      await expect(grid).toBeVisible();
      await expect(grid.getByText("CS101").first()).toBeVisible();
      await expect(grid.getByText("PRIMARY INSTRUCTOR").first()).toBeVisible();
    });
  });

  test.describe("Administrative Academic Governance", () => {
    test("admin can view institutional course catalog and active enrollments", async ({ page }) => {
      // 1. Log in as admin
      await page.goto("/login");
      await page.locator("#email").fill(adminEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();

      await expect(page).toHaveURL(/\/admin/, { timeout: 15000 });

      // 2. Navigate to Admin Academic Management
      await page.goto("/admin/academic");
      await expect(page.locator('[data-testid="admin-academic-page"]')).toBeVisible({ timeout: 15000 });

      // 3. Verify course catalog table exists and contains CS101, CS201
      const table = page.locator('[data-testid="admin-courses-table"]');
      await expect(table).toBeVisible();
      await expect(table).toContainText("CS101");
      await expect(table).toContainText("CS201");
    });
  });

  test.describe("Cross-Role Academic Boundary Protection", () => {
    test("student cannot access faculty teaching courses view", async ({ page }) => {
      // 1. Log in as student
      await page.goto("/login");
      await page.locator("#email").fill(studentEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();
      await expect(page).toHaveURL(/\/student/, { timeout: 15000 });

      // 2. Attempt navigation to /faculty/courses
      await page.goto("/faculty/courses");

      // 3. Verify 403 Forbidden protection
      await expect(page.locator('[data-testid="forbidden-state"]')).toBeVisible({ timeout: 15000 });
      await expect(page.getByText("403 — Access Forbidden")).toBeVisible();
    });

    test("student cannot access admin academic catalog view", async ({ page }) => {
      // 1. Log in as student
      await page.goto("/login");
      await page.locator("#email").fill(studentEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();
      await expect(page).toHaveURL(/\/student/, { timeout: 15000 });

      // 2. Attempt navigation to /admin/academic
      await page.goto("/admin/academic");

      // 3. Verify 403 Forbidden protection
      await expect(page.locator('[data-testid="forbidden-state"]')).toBeVisible({ timeout: 15000 });
      await expect(page.getByText("403 — Access Forbidden")).toBeVisible();
    });
  });
});
