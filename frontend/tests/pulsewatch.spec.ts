import { test, expect } from "@playwright/test";

test.describe("CampusPulse Phase 3: PulseWatch E2E Test Suite", () => {
  const studentEmail = "student@campuspulse.edu";
  const facultyEmail = "faculty@campuspulse.edu";
  const commonPassword = "CampusPulse@2026!";

  test.describe("1. Academic Pulse on Student Dashboard", () => {
    test("student sees Academic Pulse card, status badge, metric pills, and explainability drawer", async ({ page }) => {
      // 1. Log in as student
      await page.goto("/login");
      await page.locator("#email").fill(studentEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();

      // 2. Lands on Student Dashboard
      await expect(page).toHaveURL(/\/student/, { timeout: 15000 });
      await expect(page.locator('[data-testid="student-dashboard"]')).toBeVisible({ timeout: 15000 });

      // 3. Verify Academic Pulse Section is displayed
      const pulseSection = page.locator('[data-testid="academic-pulse-section"]');
      await expect(pulseSection).toBeVisible({ timeout: 10000 });

      // 4. Verify Status Badge & Summary
      await expect(page.locator('[data-testid="academic-pulse-status"]')).toBeVisible();
      await expect(page.locator('[data-testid="academic-pulse-summary-text"]')).toBeVisible();

      // 5. Verify 3 Deterministic Metric Pills
      await expect(page.locator('[data-testid="pulse-metric-attendance"]')).toBeVisible();
      await expect(page.locator('[data-testid="pulse-metric-coursework"]')).toBeVisible();
      await expect(page.locator('[data-testid="pulse-metric-assessment"]')).toBeVisible();

      // 6. Test 'Why am I seeing this?' Explainability Drawer/Modal
      const explainBtn = page.locator('[data-testid="academic-pulse-explain-btn"]');
      await expect(explainBtn).toBeVisible();
      await explainBtn.click();

      // 7. Verify Explainability Modal & Content
      const explainModal = page.locator('[data-testid="academic-pulse-explain-modal"]');
      await expect(explainModal).toBeVisible({ timeout: 5000 });

      await expect(page.locator('[data-testid="explain-what-changed"]')).toBeVisible();
      await expect(page.locator('[data-testid="explain-compared-with"]')).toBeVisible();
      await expect(page.locator('[data-testid="explain-observation-period"]')).toBeVisible();
      await expect(page.locator('[data-testid="explain-data-sufficiency"]')).toBeVisible();
      await expect(page.locator('[data-testid="explain-disclaimer"]')).toBeVisible();

      // Check non-punitive institutional disclaimer text
      await expect(page.locator('[data-testid="explain-disclaimer"]')).toContainText(
        "does not infer personal, medical, or psychological causes"
      );

      // 8. Close Modal
      await page.locator('[data-testid="modal-close-button"]').click();
      await expect(explainModal).not.toBeVisible();
    });
  });

  test.describe("2. Academic Pulse Tab & Historical Behavioral Timeline", () => {
    test("student navigates to Academic Pulse tab, views secondary cohort context and timeline", async ({ page }) => {
      // 1. Log in as student
      await page.goto("/login");
      await page.locator("#email").fill(studentEmail);
      await page.locator("#password").fill(commonPassword);
      await page.locator('[data-testid="login-submit-button"]').click();

      await expect(page).toHaveURL(/\/student/, { timeout: 15000 });

      // 2. Open Academic Records
      await page.locator('[data-testid="view-academics-btn"]').click();
      await expect(page).toHaveURL(/\/student\/academics/, { timeout: 15000 });
      await expect(page.locator('[data-testid="student-academics-page"]')).toBeVisible();

      // 3. Switch to Academic Pulse tab
      const pulseTab = page.locator('[data-testid="tab-pulse"]');
      await expect(pulseTab).toBeVisible();
      await pulseTab.click();

      // 4. Verify Academic Pulse tab content is visible
      await expect(page.locator('[data-testid="academic-pulse-tab-content"]')).toBeVisible({ timeout: 10000 });

      // 5. Verify Secondary Cohort Context Card
      const cohortCard = page.locator('[data-testid="cohort-context-card"]');
      await expect(cohortCard).toBeVisible();
      await expect(cohortCard).toContainText("Secondary Cohort Context");
      await expect(cohortCard).toContainText("Never overrides personal baseline");

      // 6. Verify Academic Environmental Context Card
      const academicCtxCard = page.locator('[data-testid="academic-context-card"]');
      await expect(academicCtxCard).toBeVisible();
      await expect(academicCtxCard).toContainText("Academic Environmental Context");
      await expect(academicCtxCard).toContainText("Deferred Context Modules");

      // 7. Verify Timeline section is rendered
      const timelineList = page.locator('[data-testid="behavior-timeline-list"]');
      const emptyTimeline = page.locator('[data-testid="empty-behavior-timeline"]');
      const hasTimelineOrEmpty = (await timelineList.isVisible()) || (await emptyTimeline.isVisible());
      expect(hasTimelineOrEmpty).toBeTruthy();

      // 8. Test Explain Calculation trigger inside timeline view
      const timelineExplainBtn = page.locator('[data-testid="timeline-explain-btn"]');
      if (await timelineExplainBtn.isVisible()) {
        await timelineExplainBtn.click();
        await expect(page.locator('[data-testid="academic-pulse-explain-modal"]')).toBeVisible();
        await page.locator('[data-testid="modal-close-button"]').click();
      }
    });
  });

  test.describe("3. PulseWatch Security & Scoping Controls", () => {
    test("cross-student PulseWatch access is rejected with HTTP 403", async ({ request }) => {
      // 1. Authenticate as student
      const loginRes = await request.post("http://127.0.0.1:8000/api/v1/auth/login", {
        data: {
          email: studentEmail,
          password: commonPassword,
        },
      });
      expect(loginRes.ok()).toBeTruthy();
      const loginData = await loginRes.json();
      const token = loginData.access_token;

      // 2. Fetch my profile to obtain valid student ID
      const meRes = await request.get("http://127.0.0.1:8000/api/v1/academic/student-profiles/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      expect(meRes.ok()).toBeTruthy();
      const myProfile = await meRes.json();

      // 3. Own student summary succeeds with HTTP 200
      const ownSummaryRes = await request.get(
        `http://127.0.0.1:8000/api/v1/pulsewatch/student/${myProfile.id}/summary`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      expect(ownSummaryRes.status()).toBe(200);
      const summaryData = await ownSummaryRes.json();
      expect(summaryData.student_id).toBe(myProfile.id);
      expect(summaryData.algorithm_version).toBe("pulsewatch-v1.0");

      // 4. Attempt to access a random/different student's summary -> MUST BE HTTP 403 Forbidden
      const unauthorizedId = "00000000-0000-0000-0000-000000009999";
      const crossStudentRes = await request.get(
        `http://127.0.0.1:8000/api/v1/pulsewatch/student/${unauthorizedId}/summary`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      expect(crossStudentRes.status()).toBe(403);
    });
  });
});
