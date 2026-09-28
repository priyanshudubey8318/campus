import { test, expect } from "@playwright/test";

test.describe("PulseCase Holistic Student Support & Interventions E2E Suite", () => {
  const uid = Date.now();
  const testStudentEmail = `student.pc.${uid}@university.edu`;
  const testPassword = "Password123!";

  test("unauthenticated access to pulsecase routes redirects to login with returnUrl", async ({
    page,
  }) => {
    // 1. Cases management dashboard
    await page.goto("/cases");
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Fcases/);
    await expect(page.getByText("Sign in to CampusPulse")).toBeVisible();

    // 2. Faculty referral submission
    await page.goto("/academic/referrals/new");
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Facademic%2Freferrals%2Fnew/);

    // 3. Faculty my-referrals tracking
    await page.goto("/academic/referrals/my");
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Facademic%2Freferrals%2Fmy/);

    // 4. Student support center
    await page.goto("/support/my-cases");
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Fsupport%2Fmy-cases/);
  });

  test("student role access to self-service support center and 403 protection on staff routes", async ({
    page,
  }) => {
    // Register new student
    await page.goto("/register");
    await page.locator("#fullName").fill("Devendra Sharma");
    await page.locator("#email").fill(testStudentEmail);
    await page.locator("#password").fill(testPassword);
    await page.locator("#confirmPassword").fill(testPassword);
    await page.locator('[data-testid="register-submit-button"]').click();

    // Verify redirected to student dashboard
    await expect(page).toHaveURL(/\/student/, { timeout: 15000 });

    // Navigate to student support center
    await page.goto("/support/my-cases");
    await expect(
      page.getByRole("heading", { name: "Student Support & Academic Success" })
    ).toBeVisible();
    await expect(page.getByText("Your Academic Advisor")).toBeVisible();
    await expect(page.getByText("Your Academic Action Items")).toBeVisible();
    await expect(page.getByText("Scheduled Check-in Appointments")).toBeVisible();

    // Student attempting to access advisor/counselor case triage queue is blocked with 403
    await page.goto("/cases");
    await expect(page.locator('[data-testid="forbidden-state"]')).toBeVisible();
    await expect(page.getByText("403 — Access Forbidden")).toBeVisible();

    // Student attempting to access faculty referral submission is blocked with 403
    await page.goto("/academic/referrals/new");
    await expect(page.locator('[data-testid="forbidden-state"]')).toBeVisible();
    await expect(page.getByText("403 — Access Forbidden")).toBeVisible();
  });
});
