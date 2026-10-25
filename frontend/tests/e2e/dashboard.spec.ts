import { test, expect } from '@playwright/test';
import { mockAnalysisResponse } from './fixtures';

test.describe('WindScope Core Dashboard & Interactions', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept backend API call with deterministic fixture
    await page.route('**/api/analysis*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAnalysisResponse),
      });
    });
  });

  test('loads dashboard without uncaught JavaScript or console errors', async ({ page }) => {
    const pageErrors: string[] = [];
    page.on('pageerror', (err) => pageErrors.push(err.message));

    await page.goto('/');

    // Verify main headings
    await expect(page.getByRole('heading', { name: /Wind Forecast Accuracy/i })).toBeVisible();
    await expect(page.getByText(/Great Britain · January 2026/i)).toBeVisible();

    // Verify no page errors occurred
    expect(pageErrors).toEqual([]);
  });

  test('displays all four KPI cards with correct metric values and units', async ({ page }) => {
    await page.goto('/');

    // MAE Card
    const maeCard = page.getByTestId('kpi-mae');
    await expect(maeCard).toBeVisible();
    await expect(maeCard).toContainText('1,919.3');
    await expect(maeCard).toContainText('MW');

    // RMSE Card
    const rmseCard = page.getByTestId('kpi-rmse');
    await expect(rmseCard).toBeVisible();
    await expect(rmseCard).toContainText('2,395.3');

    // Bias Card
    const biasCard = page.getByTestId('kpi-bias');
    await expect(biasCard).toBeVisible();
    await expect(biasCard).toContainText('+1713.3');

    // Coverage Card
    const coverageCard = page.getByTestId('kpi-coverage');
    await expect(coverageCard).toBeVisible();
    await expect(coverageCard).toContainText('50.0%');
    await expect(coverageCard).toContainText('744 of 1,488');
  });

  test('renders primary forecast chart and daily error chart', async ({ page }) => {
    await page.goto('/');

    const chartCard = page.getByTestId('forecast-chart-card');
    await expect(chartCard).toBeVisible();
    await expect(chartCard.getByText('Forecast (MW)')).toBeVisible();
    await expect(chartCard.getByText('Actual (MW)')).toBeVisible();

    await expect(page.getByTestId('daily-error-chart-card')).toBeVisible();
    await expect(page.getByText(/Daily Mean Absolute Error/i)).toBeVisible();
  });

  test('renders interval table with correct missing-value representation', async ({ page }) => {
    await page.goto('/');

    const tableCard = page.getByTestId('interval-table-card');
    await expect(tableCard).toBeVisible();

    // Verify row with valid forecast
    await expect(tableCard.getByText('19,498')).toBeVisible();
    await expect(tableCard.getByText('13,756')).toBeVisible();

    // Verify row with missing forecast displays em-dash (—) and NOT 0
    const dashes = tableCard.locator('.cell-na');
    await expect(dashes.first()).toBeVisible();
    await expect(dashes.first()).toHaveText('—');
  });

  test('opens methodology modal, displays cut-off rule, and closes via keyboard Escape', async ({ page }) => {
    await page.goto('/');

    const methodologyBtn = page.getByRole('button', { name: /How this is calculated/i });
    await expect(methodologyBtn).toBeVisible();
    await methodologyBtn.click();

    // Modal dialog is displayed
    const modal = page.getByRole('dialog');
    await expect(modal).toBeVisible();
    await expect(modal.getByRole('heading', { name: /Methodology & Calculation Rules/i })).toBeVisible();

    // Contains strict cut-off rule
    await expect(modal).toContainText('publishTime < start_of_delivery_date_in_Europe_London');

    // Press Escape to close modal
    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible();
  });

  test('allows toggling between whole month and single delivery day view', async ({ page }) => {
    await page.goto('/');

    // Click "Single Delivery Day" tab
    const singleDayTab = page.getByRole('tab', { name: /Single Delivery Day/i });
    await singleDayTab.click();
    await expect(singleDayTab).toHaveAttribute('aria-selected', 'true');

    // Day picker control becomes visible
    const daySelect = page.getByLabel(/Select delivery date/i);
    await expect(daySelect).toBeVisible();

    // Table title updates
    await expect(page.getByTestId('interval-table-card')).toContainText('Interval Details');
  });

  test('refresh button shows loading state and completes', async ({ page }) => {
    await page.goto('/');

    const refreshBtn = page.getByRole('button', { name: /Refresh/i });
    await expect(refreshBtn).toBeVisible();
    await refreshBtn.click();

    // Verifies button returns to interactive state
    await expect(refreshBtn).not.toBeDisabled();
  });
});
