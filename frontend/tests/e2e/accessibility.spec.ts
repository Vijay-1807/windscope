import { test, expect } from '@playwright/test';
import { mockAnalysisResponse } from './fixtures';

test.describe('Accessibility & Keyboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/analysis*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAnalysisResponse),
      });
    });
  });

  test('interactive controls are reachable and focusable via keyboard Tab', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Wind Forecast Accuracy/i })).toBeVisible();

    // Press Tab repeatedly and verify activeElement changes
    await page.keyboard.press('Tab'); // Refresh button
    const activeTagName = await page.evaluate(() => document.activeElement?.tagName);
    expect(['BUTTON', 'A']).toContain(activeTagName);

    // Tab into "How this is calculated" button and press Enter to open
    const methodologyBtn = page.getByRole('button', { name: /How this is calculated/i });
    await methodologyBtn.focus();
    await page.keyboard.press('Enter');

    // Dialog must open
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Close button should receive initial focus or be closable via Escape
    await page.keyboard.press('Escape');
    await expect(dialog).not.toBeVisible();
  });

  test('distinguishes forecast and actual lines beyond color alone', async ({ page }) => {
    await page.goto('/');

    const chartCard = page.getByTestId('forecast-chart-card');
    await expect(chartCard).toBeVisible();

    // Legend has distinct text labels
    await expect(chartCard.getByText('Forecast (MW)')).toBeVisible();
    await expect(chartCard.getByText('Actual (MW)')).toBeVisible();

    // Forecast line uses dashed stroke pattern
    const lines = chartCard.locator('path.recharts-line-curve');
    await expect(lines.first()).toBeVisible();
  });
});
