import { test, expect } from '@playwright/test';
import { mockAnalysisResponse } from './fixtures';

test.describe('Dashboard States & Resilience', () => {
  test('displays loading skeleton during slow API response', async ({ page }) => {
    // Delay API response by 1.5 seconds
    await page.route('**/api/analysis*', async (route) => {
      await new Promise((r) => setTimeout(r, 1500));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAnalysisResponse),
      });
    });

    await page.goto('/');

    // Skeleton is displayed while loading
    const skeleton = page.locator('.skeleton');
    await expect(skeleton.first()).toBeVisible();

    // After resolution, real dashboard renders
    await expect(page.getByRole('heading', { name: /Wind Forecast Accuracy/i })).toBeVisible();
  });

  test('displays error state with retry action on API 500 failure', async ({ page }) => {
    let shouldFail = true;
    await page.route('**/api/analysis*', async (route) => {
      if (shouldFail) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Internal Elexon upstream timeout' }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockAnalysisResponse),
        });
      }
    });

    await page.goto('/');

    // Error banner is visible with message and retry button
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByText(/Internal Elexon upstream timeout/i)).toBeVisible();

    const retryBtn = page.getByRole('button', { name: /Retry Request/i });
    await expect(retryBtn).toBeVisible();

    // Set shouldFail to false and click retry -> recovers to success state
    shouldFail = false;
    await retryBtn.click();
    await expect(page.getByRole('heading', { name: /Wind Forecast Accuracy/i })).toBeVisible();
  });

  test('displays partial data status and warning banner when coverage < 100%', async ({ page }) => {
    await page.route('**/api/analysis*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAnalysisResponse),
      });
    });

    await page.goto('/');

    // Partial data pill in header
    await expect(page.getByText(/Partial Data/i)).toBeVisible();

    // Data Quality Notice banner
    const notice = page.getByRole('region', { name: /Data coverage notices/i });
    await expect(notice).toBeVisible();
    await expect(notice).toContainText('Elexon WINDFOR dataset publishes national wind forecasts at hourly intervals');
  });
});
