import { test, expect } from "@playwright/test";

test.describe("CampusPulse Phase 1 Authentication & RBAC Suite", () => {
  const testStudentEmail = `pw.student.${Date.now()}@university.edu`;
  const testPassword = "SecurePassword123!";

  test("unauthenticated access to protected route redirects to login with returnUrl", async ({
    page,
  }) => {
    await page.goto("/student");
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Fstudent/);
    await expect(page.getByText("Sign in to CampusPulse")).toBeVisible();
  });

  test("login with invalid credentials displays error alert and prevents enumeration", async ({
    page,
  }) => {
    await page.goto("/login");
    await page.locator("#email").fill("nonexistent.user@university.edu");
    await page.locator("#password").fill("WrongPassword123!");
    await page.locator('[data-testid="login-submit-button"]').click();

    const errorAlert = page.locator('[data-testid="login-error-alert"]');
    await expect(errorAlert).toBeVisible();
    await expect(errorAlert).toContainText("Invalid email or password");
  });

  test("user registration with complexity validation establishes session and opens portal", async ({
    page,
  }) => {
    await page.goto("/register");

    await page.locator("#fullName").fill("Alex Taylor");
    await page.locator("#email").fill(testStudentEmail);
    await page.locator("#password").fill(testPassword);
    await page.locator("#confirmPassword").fill(testPassword);

    await page.locator('[data-testid="register-submit-button"]').click();

    // After registration, user is automatically authenticated and redirected to /student
    await expect(page).toHaveURL(/\/student/, { timeout: 15000 });
    await expect(page.locator('[data-testid="student-portal"]')).toBeVisible();

    // Header displays user initials and role badge
    const profileMenu = page.locator('[data-testid="user-profile-menu"]');
    await expect(profileMenu).toBeVisible();
    await expect(profileMenu).toContainText("Alex Taylor");
    await expect(profileMenu).toContainText("STUDENT");
  });

  test("RBAC role enforcement displays 403 Forbidden when student accesses admin portal", async ({
    page,
  }) => {
    // 1. Log in as student
    await page.goto("/login");
    await page.locator("#email").fill(testStudentEmail);
    await page.locator("#password").fill(testPassword);
    await page.locator('[data-testid="login-submit-button"]').click();

    await expect(page).toHaveURL(/\/student/, { timeout: 15000 });

    // 2. Attempt direct navigation to /admin
    await page.goto("/admin");

    // 3. Verify distinct 403 Forbidden state UI
    const forbiddenCard = page.locator('[data-testid="forbidden-state"]');
    await expect(forbiddenCard).toBeVisible();
    await expect(page.getByText("403 — Access Forbidden")).toBeVisible();
    await expect(
      page.getByText("Your account does not hold the required role for this portal")
    ).toBeVisible();
  });

  test("logout terminates session, clears cookies, and resets header", async ({
    page,
  }) => {
    // 1. Log in
    await page.goto("/login");
    await page.locator("#email").fill(testStudentEmail);
    await page.locator("#password").fill(testPassword);
    await page.locator('[data-testid="login-submit-button"]').click();
    await expect(page).toHaveURL(/\/student/, { timeout: 15000 });

    // 2. Click Sign Out and await logout completion
    const logoutResponsePromise = page.waitForResponse(
      (res) => res.url().includes("/auth/logout") && res.status() === 200
    );
    await page.locator('[data-testid="sign-out-button"]').click();
    await logoutResponsePromise;

    // 3. Verify header displays Sign In and Register actions
    const authActions = page.locator('[data-testid="auth-action-buttons"]');
    await expect(authActions).toBeVisible();
    await expect(page.locator('[data-testid="nav-login-button"]')).toBeVisible();

    // 4. Verify accessing /student now redirects to /login again
    await page.goto("/student");
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Fstudent/, { timeout: 15000 });
  });

  test("browser security: tokens and sensitive credentials are never stored in localStorage or sessionStorage", async ({
    page,
  }) => {
    // 1. Authenticate user
    await page.goto("/login");
    await page.locator("#email").fill(testStudentEmail);
    await page.locator("#password").fill(testPassword);
    await page.locator('[data-testid="login-submit-button"]').click();
    await expect(page).toHaveURL(/\/student/, { timeout: 15000 });

    // 2. Inspect browser storage APIs directly inside the page execution context
    const storageAudit = await page.evaluate(() => {
      const localKeys = Object.keys(localStorage);
      const sessionKeys = Object.keys(sessionStorage);
      const localData = localKeys.map((k) => ({ key: k, val: localStorage.getItem(k) }));
      const sessionData = sessionKeys.map((k) => ({ key: k, val: sessionStorage.getItem(k) }));
      return { localData, sessionData };
    });

    const combinedStorage = [
      ...storageAudit.localData.map((d) => `${d.key}=${d.val}`),
      ...storageAudit.sessionData.map((d) => `${d.key}=${d.val}`),
    ]
      .join(" ")
      .toLowerCase();

    // Verify complete absence of sensitive credential strings from browser persistent storage
    expect(combinedStorage).not.toContain("access_token");
    expect(combinedStorage).not.toContain("refresh_token");
    expect(combinedStorage).not.toContain("campuspulse_");
    expect(combinedStorage).not.toContain(testPassword.toLowerCase());
    expect(combinedStorage).not.toContain("bearer");
  });
});

