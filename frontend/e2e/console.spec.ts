import { test, expect } from '@playwright/test';

test.describe('ProcedureGuard Evidence Console E2E Tests', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to the local server
    await page.goto('/');
  });

  test('should load the dashboard and verify key elements', async ({ page }) => {
    // Verify title/header identity
    await expect(page.locator('h1')).toContainText('ProcedureGuard Console');
    
    // Verify active run cards
    await expect(page.locator('text=Active Runs')).toBeVisible();
    await expect(page.locator('text=Active Deviations')).toBeVisible();
    await expect(page.locator('text=Review Backlog')).toBeVisible();
    await expect(page.locator('text=Compliance Trend')).toBeVisible();

    // Verify recent runs table is present
    await expect(page.locator('text=Recent Verification Runs')).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });

  test('should navigate to the runs cockpit page and test tab switching', async ({ page }) => {
    // Go to runs page
    await page.click('nav a:has-text("Verification Runs")');
    await page.waitForURL('**/runs');

    // Confirm default headers
    await expect(page.locator('h1')).toContainText('Run ID:');
    
    // Test tabs switching
    await page.click('button:has-text("Step verification")');
    await expect(page.locator('text=SOP Step Checklist DetailsList')).toBeVisible();

    await page.click('button:has-text("Evidence workspace")');
    await expect(page.locator('text=Visual Evidence Playback')).toBeVisible();

    await page.click('button:has-text("Human review")');
    await expect(page.locator('text=Run Backlog Queue')).toBeVisible();

    await page.click('button:has-text("Audit trail")');
    await expect(page.locator('text=Verification record assembled')).toBeVisible();

    await page.click('button:has-text("Ask")');
    await expect(page.locator('text=Agent 3 Compliance Chat Assistant')).toBeVisible();
  });

  test('should open evidence drawer and test reviewer status overrides', async ({ page }) => {
    await page.click('nav a:has-text("Verification Runs")');
    await page.waitForURL('**/runs');
    await page.click('text=Step verification');

    // Find first table row inside step verification ledger and click it to open drawer
    const firstRow = page.locator('tbody tr').first();
    await expect(firstRow).toBeVisible();
    await firstRow.click();

    // Verify drawer header slides open
    const drawer = page.locator('aside');
    await expect(drawer).toBeVisible();
    await expect(drawer.locator('text=Evidence package')).toBeVisible();

    // Test override click: click 'Confirm Compliant' in drawer
    const compliantButton = drawer.locator('button:has-text("Confirm Compliant")');
    await expect(compliantButton).toBeVisible();
    await compliantButton.click();

    // Verify status updates
    await expect(firstRow.locator('text=Confirmed compliant')).toBeVisible();

    // Test drawer close
    const closeBtn = drawer.locator('button').first();
    await closeBtn.click();
    await expect(drawer).not.toBeVisible();
  });

  test('should verify run selection from recent verification runs table updates active run', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');

    // Find the link for the third run and click it
    const otherRunLink = page.locator('table a:has-text("run-20260616-5b0b97e6")');
    await expect(otherRunLink).toBeVisible();
    await otherRunLink.click();

    // Confirm navigation to runs page and check that active run ID matches in heading
    await page.waitForURL('**/runs');
    await expect(page.locator('h1')).toContainText('run-20260616-5b0b97e6');
  });

  test('should verify printable report export page and watermark', async ({ page }) => {
    await page.click('text=Report Export');
    await page.waitForURL('**/export');

    // Confirm limitations notice statement exists
    await expect(page.locator('text=Regulatory Limitations & human-review Notice')).toBeVisible();
    await expect(page.locator('text=This verification record aggregates computer-vision pipeline outputs')).toBeVisible();

    // Confirm watermark presence or draft status is rendered when queue is unresolved
    const watermark = page.locator('text=DRAFT');
    const subtitle = page.locator('text=Pending Supervisor review signatures');
    if (await watermark.count() > 0) {
      await expect(subtitle).toBeVisible();
    }
  });

  test('should verify consolidated navigation sidebar deep links', async ({ page }) => {
    // Click 'Human Review' in sidebar
    await page.click('nav a:has-text("Human Review")');
    await page.waitForURL('**/runs?tab=REVIEW');
    await expect(page.locator('text=Run Backlog Queue')).toBeVisible();

    // Click 'Audit Trail' in sidebar
    await page.click('nav a:has-text("Audit Trail")');
    await page.waitForURL('**/runs?tab=AUDIT');
    await expect(page.locator('text=Verification record assembled')).toBeVisible();

    // Click 'Deviations' in sidebar
    await page.click('nav a:has-text("Deviations")');
    await page.waitForURL('**/runs?tab=STEPS&filter=Deviation%20Detected');
    await expect(page.locator('select')).toHaveValue('Deviation Detected');
  });
});
