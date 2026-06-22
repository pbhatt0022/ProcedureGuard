import { test } from '@playwright/test';

test.describe('Capture Console Screenshots', () => {
  test('should capture pages', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });

    // 1. Capture Dashboard
    await page.goto('/');
    await page.waitForTimeout(1000); // let animations settle
    await page.screenshot({ path: 'C:/Users/priya/.gemini/antigravity/brain/96586636-7507-418b-a22a-6b6fc22e6d64/dashboard.png' });

    // 2. Capture Cockpit (Overview)
    await page.goto('/runs');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'C:/Users/priya/.gemini/antigravity/brain/96586636-7507-418b-a22a-6b6fc22e6d64/cockpit_overview.png' });

    // 3. Capture Cockpit (Steps list)
    await page.click('button:has-text("Step verification")');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'C:/Users/priya/.gemini/antigravity/brain/96586636-7507-418b-a22a-6b6fc22e6d64/cockpit_steps.png' });

    // 4. Capture Export Page
    await page.goto('/export');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'C:/Users/priya/.gemini/antigravity/brain/96586636-7507-418b-a22a-6b6fc22e6d64/export_report.png' });

    // 5. Capture Cockpit (Human Review tab)
    await page.goto('/runs?tab=REVIEW');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'C:/Users/priya/.gemini/antigravity/brain/96586636-7507-418b-a22a-6b6fc22e6d64/cockpit_review.png' });

    // 6. Capture Cockpit (Audit Trail tab)
    await page.goto('/runs?tab=AUDIT');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'C:/Users/priya/.gemini/antigravity/brain/96586636-7507-418b-a22a-6b6fc22e6d64/cockpit_audit.png' });
  });
});
