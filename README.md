# WindScope — Great Britain Wind Generation Forecast Accuracy Platform

**WindScope** is a high-performance, full-stack decision-support platform designed to evaluate the accuracy of day-ahead national wind generation forecasts for Great Britain across January 2026.

Built to address the **REint Full Stack SWE Challenge**, WindScope enforces strict day-ahead decision cut-offs, joins hourly and half-hourly datasets from the live Elexon BMRS API, calculates production-grade error metrics, and presents an editorial, accessible, and responsive dashboard.

---

## 📑 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Quickstart & Setup](#quickstart--setup)
3. [Decision Cut-Off & Methodology](#decision-cut-off--methodology)
4. [Data Engineering & Discovery Insights](#data-engineering--discovery-insights)
5. [API Specification](#api-specification)
6. [Testing & Quality Assurance](#testing--quality-assurance)
7. [UI/UX Design Decisions](#uiux-design-decisions)

---

## 🏛️ Architecture Overview

```
                        ┌─────────────────────────────────────┐
                        │          Elexon BMRS API            │
                        │  (data.elexon.co.uk/bmrs/api/v1)    │
                        └──────────────────┬──────────────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        │   Upstream Stream Endpoints:        │
                        │   • /datasets/FUELHH/stream (WIND)  │
                        │   • /datasets/WINDFOR/stream        │
                        └──────────────────┬──────────────────┘
                                           │ HTTP/JSON
                                           ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Python 3.9+)                        │
│                                                                           │
│  app/clients/elexon.py                                                    │
│    └── Asynchronous HTTP client with retry backoff & range queries       │
│  app/services/analysis.py                                                 │
│    ├── Timezone normalization (Europe/London ↔ UTC)                       │
│    ├── Day-ahead purchasing cut-off filter (strictly publishTime < cut-off)│
│    ├── Vintage selection (latest published eligible forecast)            │
│    ├── Equi-join on target startTime (ISO 8601 UTC)                       │
│    ├── Metrics engine: MAE, RMSE, Mean Bias, Normalized MAE               │
│    └── In-memory cached results with concurrent request locking           │
│  app/api/routes.py                                                        │
│    └── /api/health, /api/analysis?month=2026-01, /api/analysis/day        │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │ RESTful JSON / CORS
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                 React 19 + TypeScript + Vite Frontend                     │
│                                                                           │
│  • KPI Cards: MAE, RMSE, Mean Bias, Data Coverage (with custom units)     │
│  • Dual-Line Chart: Actuals vs Selected Forecast (custom SVG / Canvas)    │
│  • Daily Error Bar Chart: Daily MAE & RMSE with click-to-filter drilldown │
│  • Detailed Interval Table: Sortable, filterable by date, missing states  │
│  • Methodology Modal: Accessible modal explaining math & cut-offs         │
│  • Data Quality Banner: Explicit transparency on 50% hourly resolution    │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart & Setup

### Prerequisites
- **Python**: 3.9+ (tested on Python 3.9, 3.11, 3.12)
- **Node.js**: 18+ & **npm**: 9+

---

### 1. Backend Service

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment (optional but recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend API server on port 8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The API is available at `http://127.0.0.1:8000`:
- **Interactive OpenAPI Documentation (Swagger)**: [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
- **Alternative ReDoc**: [http://127.0.0.1:8000/api/redoc](http://127.0.0.1:8000/api/redoc)
- **Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **January 2026 Analysis Endpoint**: [http://127.0.0.1:8000/api/analysis?month=2026-01](http://127.0.0.1:8000/api/analysis?month=2026-01)

---

### 2. Frontend Application

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
The dashboard will open at `http://localhost:5173`.

---

## ⏱️ Decision Cut-Off & Methodology

### 1. The Day-Ahead Decision Cut-Off
In UK electricity markets, energy contracts are committed prior to the delivery day. To evaluate the true accuracy of the forecast available at decision time:
1. Every target delivery interval $t$ is mapped to its local delivery date $D$ in `Europe/London`.
2. The day-ahead cut-off deadline $T_{\text{cutoff}}(D)$ is set to **00:00:00 local time on date $D$** (midnight preceding delivery day).
3. **Strict Inequality Rule**: Only forecast vintages published **strictly before** the cut-off are considered eligible:
   $$\text{publishTime} < T_{\text{cutoff}}(D)$$
   Any forecast published at 00:00:00 or later on date $D$ is strictly disqualified from evaluating interval $t$, preventing hindsight bias.
4. **Vintage Selection**: Among all eligible vintages for delivery interval $t$, the algorithm selects the one with the maximum $\text{publishTime}$ (the latest information available before the gate closed).

### 2. Metric Formulations
Let $N$ denote the count of matched intervals where both actual generation $A_i$ and eligible forecast $F_i$ exist.
Let error residual $e_i = F_i - A_i$.

- **Mean Absolute Error (MAE)**:
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} |F_i - A_i|$$
- **Root Mean Square Error (RMSE)**:
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (F_i - A_i)^2}$$
- **Mean Bias**:
  $$\text{Bias} = \frac{1}{N} \sum_{i=1}^{N} (F_i - A_i)$$
  *(Positive indicates systematic over-forecasting; negative indicates systematic under-forecasting)*
- **Normalized MAE**:
  $$\text{Normalized MAE} = \frac{\text{MAE}}{\bar{A}} \times 100\% \quad \text{where} \quad \bar{A} = \frac{1}{N} \sum_{i=1}^{N} A_i$$

---

## 🔍 Data Engineering & Discovery Insights

During live verification of the official Elexon BMRS APIs for January 2026:
1. **Resolution Difference**:
   - `FUELHH` (fuelType=WIND) provides half-hourly actuals (1,488 intervals for 31 days $\times$ 48 half-hours).
   - `WINDFOR` stream publishes national wind forecasts at **hourly** timestamps (:00 minutes).
2. **Coverage Impact**:
   - Because of hourly forecast resolution, 744 target intervals (:00) match with day-ahead forecasts, yielding **50.0% coverage** of the month.
   - Non-matched half-hourly intervals (:30) have recorded actuals, but no forecast.
3. **No Artificial Zero-Filling**:
   - Missing forecasts are **never filled with zeros or interpolated**. In financial and grid risk evaluation, treating missing forecast entries as 0 MW would introduce severe artificial errors.
   - Half-hourly rows are transparently displayed in the data table with em-dashes (`—`) and explicit "Not available" labels for screen readers.

---

## 🧪 Testing & Quality Assurance

### Backend Unit & Integration Tests (22 Passed)
Comprehensive pytest suite covering cut-off boundary rules, tie-breaking, ISO timestamp parsing, upstream error handling, and metric fixture validation:
```bash
cd backend
python -m pytest tests/ -v
```
All 22 tests pass:
- `test_cutoff_calculation_delivery_date`
- `test_strictly_before_cutoff_rule` (validates `<` strictly excludes `=`)
- `test_closer_ineligible_forecast_is_never_used`
- `test_multiple_eligible_versions_selects_latest`
- `test_joining_on_normalized_start_time`
- `test_january_1_uses_december_31_publications`
- `test_february_intervals_excluded_january_included`
- `test_timestamp_offsets_normalized_safely`
- `test_duplicate_records_do_not_multiply_rows`
- `test_elexon_client_*` (retries, timeouts, malformed rows)
- `test_hand_calculated_metric_fixture`
- `test_missing_records_not_replaced_with_zero`
- `test_expected_count_is_1488_and_coverage_bounds`
- `test_api_routes_*` (health, monthly 2026-01, day routes, 400 validations)

### Frontend End-to-End Tests (36 Passed)
Full Playwright suite running across Desktop Chrome (1440x900) and Mobile Chrome (Pixel 7 / 390x844):
```bash
cd frontend
npx playwright test
```
All 36 tests pass across:
- **Accessibility & Keyboard Navigation**: Tab sequence focus, aria attributes, modal trapping, escape handling, dual visual encoding (color + dashed lines).
- **Core Dashboard Interactions**: KPI values, dual charts, table pagination and sorting, month vs day toggle, day selector.
- **States & Resilience**: Loading skeleton, upstream 500 error display with retry button, partial coverage warning banner.
- **Responsive Layout**: Validated with zero horizontal overflow across 320px, 375px, 390px, 768px, 1024px, and 1440px viewports.

---

## 🎨 UI/UX Design Decisions

- **Color Palette**: High-contrast, executive palette. Real actual generation rendered in deep forest/slate (`#0F172A`), forecasts rendered in clear cobalt blue (`#2563EB`) with a dashed stroke, avoiding ambiguous bright green/red styling.
- **Dual Visual Encoding**: Forecast and actual traces differ in stroke pattern (solid vs dashed) and point glyphs, ensuring accessibility for color-blind operators.
- **Performance**: In-memory caching with asynchronous locks prevents duplicate concurrent fetches to Elexon BMRS, ensuring sub-50ms subsequent page loads.
- **Transparency**: Prominent data quality banner alerts analysts to the 50.0% hourly resolution match without blocking workflow.
