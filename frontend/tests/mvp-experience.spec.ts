import { test, expect } from "@playwright/test";

test.describe("CampusPulse Rapid MVP Demonstrator Experience Suite", () => {
  test("1. Quick Demo Login and Counselor Portal Workflow", async ({ page }) => {
    await page.goto("/login");

    // Verify Demo Quick Login panel exists
    await expect(page.getByText("Demo Instant Login")).toBeVisible();

    // Click Counselor quick login button
    const counselorBtn = page.getByRole("button", { name: /Counselor/i });
    await expect(counselorBtn).toBeVisible();
    await counselorBtn.click();

    // Verify redirect to Counselor Portal
    await expect(page).toHaveURL(/\/counselor/);
    await expect(page.getByRole("heading", { name: "Student Wellbeing & Counseling Services" })).toBeVisible();
    await expect(page.getByText("Strict Confidentiality Boundaries Enforced")).toBeVisible();

    // Verify KPI cards
    await expect(page.getByText("Active Wellbeing Cases")).toBeVisible();
    await expect(page.getByText("Immediate Attention")).toBeVisible();

    // Open New Wellbeing Intake Modal
    const newIntakeBtn = page.getByRole("button", { name: /New Wellbeing Intake/i }).first();
    await newIntakeBtn.click();
    await expect(page.getByText("New Student Wellbeing Intake")).toBeVisible();
    await expect(page.getByText("Student ID or Enrollment Number")).toBeVisible();

    // Close modal
    await page.getByRole("button", { name: "Cancel" }).click();
  });

  test("2. Super Admin Root Governance and AI Audit Telemetry", async ({ page }) => {
    await page.goto("/login");

    // Click Super Admin quick login button
    const superAdminBtn = page.getByRole("button", { name: /Super Admin/i });
    await expect(superAdminBtn).toBeVisible();
    await superAdminBtn.click();

    // Verify redirect to Super Admin Portal
    await expect(page).toHaveURL(/\/super-admin/);
    await expect(page.getByRole("heading", { name: "Institutional Root Governance & Security Audit" })).toBeVisible();
    await expect(page.getByText("System Engine Health")).toBeVisible();
    await expect(page.getByText("PulseAssist Interaction & RAG Audit Trail")).toBeVisible();
  });

  test("3. Advisor Portal Support Case Integration", async ({ page }) => {
    await page.goto("/login");

    // Click Advisor quick login button
    const advisorBtn = page.getByRole("button", { name: /Advisor/i });
    await expect(advisorBtn).toBeVisible();
    await advisorBtn.click();

    // Verify redirect to Advisor Portal
    await expect(page).toHaveURL(/\/advisor/);
    await expect(page.getByRole("heading", { name: "Academic Support Priority & Advising Roster" })).toBeVisible();

    // Verify Support Cases navigation link is present in advisor portal
    const supportCasesLink = page.getByTestId("advisor-portal").getByRole("link", { name: "Support Cases" });
    await expect(supportCasesLink).toBeVisible();
  });
});
