import { test, expect } from "@playwright/test";

test.describe("CampusPulse Responsive Viewport Verification Suite", () => {
  const viewports = [
    { width: 1920, height: 1080, name: "1920x1080 Desktop" },
    { width: 1440, height: 900, name: "1440x900 Laptop" },
    { width: 1280, height: 720, name: "1280x720 Standard" },
    { width: 768, height: 1024, name: "768x1024 Tablet" },
    { width: 375, height: 667, name: "375x667 Mobile" },
  ];

  const routes = [
    "/",
    "/features",
    "/how-it-works",
    "/security",
    "/login",
    "/register",
    "/system-status",
  ];

  for (const vp of viewports) {
    test(`renders without horizontal overflow at ${vp.name}`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });

      for (const route of routes) {
        await page.goto(route, { waitUntil: "networkidle" });
        const hasOverflow = await page.evaluate(() => {
          return (
            document.documentElement.scrollWidth > window.innerWidth ||
            document.body.scrollWidth > window.innerWidth
          );
        });
        expect(hasOverflow, `Horizontal scroll overflow detected on ${route} at ${vp.name}`).toBe(false);
      }
    });
  }
});
