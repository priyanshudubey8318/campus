import { test, expect } from "@playwright/test";

test.describe("PulseRecord Institutional Records & Grievance E2E Suite", () => {
  const uid = Date.now();
  const testStudentEmail = `student.pr.${uid}@university.edu`;
  const testPassword = "Password123!";

  test("unauthenticated access to pulserecord routes redirects to login", async ({ page }) => {
    // 1. Student leaves
    await page.goto("/student/leaves");
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Fstudent%2Fleaves/);
    await expect(page.getByText("Sign in to CampusPulse")).toBeVisible();

    // 2. Student complaints
    await page.goto("/student/complaints");
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Fstudent%2Fcomplaints/);

    // 3. Faculty leaves
    await page.goto("/faculty/leaves");
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Ffaculty%2Fleaves/);

    // 4. Admin records
    await page.goto("/admin/records");
    await expect(page).toHaveURL(/\/login\?returnUrl=%2Fadmin%2Frecords/);
  });

  test("student can navigate to leave and complaint portals and see required workflows", async ({
    page,
  }) => {
    // Register new student
    await page.goto("/register");
    await page.locator("#fullName").fill("Aarav Patel");
    await page.locator("#email").fill(testStudentEmail);
    await page.locator("#password").fill(testPassword);
    await page.locator("#confirmPassword").fill(testPassword);
    await page.locator('[data-testid="register-submit-button"]').click();

    // Verify redirected to student dashboard
    await expect(page).toHaveURL(/\/student/, { timeout: 15000 });

    // Navigate to /student/leaves
    await page.goto("/student/leaves");
    await expect(page.getByRole("heading", { name: "Leave Management" })).toBeVisible();
    const newLeaveBtn = page.getByRole("button", { name: "New Leave Request" }).first();
    await expect(newLeaveBtn).toBeVisible();

    // Open leave application modal
    await newLeaveBtn.click();
    await expect(page.getByRole("heading", { name: "Submit Leave Request" })).toBeVisible();
    await page.getByRole("button", { name: "Cancel" }).first().click();

    // Navigate to /student/complaints
    await page.goto("/student/complaints");
    await expect(page.getByRole("heading", { name: "Grievances & Complaints" })).toBeVisible();
    const newGrievanceBtn = page.getByRole("button", { name: "File Grievance" }).first();
    await expect(newGrievanceBtn).toBeVisible();

    // Open grievance modal
    await newGrievanceBtn.click();
    await expect(page.getByRole("heading", { name: "File Protected Grievance" })).toBeVisible();
    await expect(page.getByText("Anonymous Reporting")).toBeVisible();
    await page.getByRole("button", { name: "Cancel" }).first().click();
  });
});
