import { test, expect } from '@playwright/test';
import { mockAnalysisResponse } from './fixtures';

const VIEWPORTS = [
  { name: 'mobile-small', width: 320, height: 740 },
  { name: 'mobile-iphone', width: 375, height: 812 },
  { name: 'mobile-pixel', width: 390, height: 844 },
  { name: 'tablet-portrait', width: 768, height: 1024 },
  { name: 'tablet-landscape', width: 1024, height: 768 },
  { name: 'desktop', width: 1440, height: 900 },
];

test.describe('Responsive Layout & No Horizontal Overflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/analysis*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAnalysisResponse),
      });
    });
  });

  for (const vp of VIEWPORTS) {
    test(`renders cleanly without horizontal overflow at ${vp.width}x${vp.height} (${vp.name})`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto('/');

      // Wait for content to render
      await expect(page.getByRole('heading', { name: /Wind Forecast Accuracy/i })).toBeVisible();

      // Check document-level horizontal overflow: scrollWidth must be <= clientWidth
      const hasHorizontalScroll = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
      });
      expect(hasHorizontalScroll).toBe(false);

      // Verify KPI cards are visible
      await expect(page.getByTestId('kpi-mae')).toBeVisible();
      await expect(page.getByTestId('kpi-coverage')).toBeVisible();

      // Verify chart cards are visible
      await expect(page.getByTestId('forecast-chart-card')).toBeVisible();
      await expect(page.getByTestId('interval-table-card')).toBeVisible();

      // Capture screenshot for visual inspection
      await page.screenshot({
        path: `test-results/screenshots/screenshot-${vp.name}-${vp.width}x${vp.height}.png`,
        fullPage: false,
      });
    });
  }
});
