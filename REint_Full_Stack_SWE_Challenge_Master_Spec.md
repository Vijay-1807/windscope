# REint Full Stack SWE Challenge — Master Build Specification

> **Purpose:** This is the single source of truth for implementing, testing, polishing, deploying, and presenting the REint Full Stack Software Engineering challenge. Give this file to Antigravity, OpenCode, or another coding agent **from the root of the project repository**. The agent is expected to implement and verify the working application, not merely return a plan or mock-up.

## 0. Instructions to the coding agent

Act as a senior full-stack engineer, data engineer, product designer, and QA engineer. Read the entire specification before changing files. Inspect the existing repository first; preserve working code where appropriate. Then implement the application end-to-end in small, testable phases.

### Non-negotiable working rules

1. **Build the real application.** Do not stop after creating a proposal, design, static mock-up, or code snippets.
2. **Verify the data contract before committing to an API strategy.** Call and inspect the official API endpoints, response shape, supported historical query filters, and the availability of multiple forecast vintages. Record what is actually observed. Do not invent endpoint parameters or assume a current/latest endpoint provides historical vintages.
3. **Do not fabricate production data.** Deterministic fixtures are allowed only in automated tests and explicitly marked demo/degraded states. A failed data request must never become a chart of made-up values.
4. **Protect the decision-time boundary.** A forecast published after the modeled purchase deadline is ineligible, even if it is closer to the actual generation.
5. **Test while building, not only at the end.** Run focused tests after each phase. Fix regressions before moving on.
6. **Use Playwright to exercise the actual browser UI.** Test desktop and mobile layouts, key interactions, loading/error/empty states, browser-console errors, failed requests, and overflow. Save failure screenshots/traces and inspect screenshots at representative sizes.
7. **Be precise in status reports.** Never claim that a test, deploy, API call, or browser check succeeded unless it actually ran and passed. Finish with commands run, pass/fail counts, live URLs, screenshots/artifacts, and unresolved issues.
8. **Respect the assignment's 16-hour limit.** Prioritize correct analysis, useful product UX, real deployment, and evidence of QA. Do not spend time on unrelated features.

### Implementation phases

- **Phase A — API/data spike:** inspect official docs and real January 2026 responses; document the query method and vintage coverage.
- **Phase B — backend domain logic:** normalize records, apply the decision cut-off, join actuals/forecasts, calculate metrics, and pass unit tests.
- **Phase C — product UI:** implement the responsive design system, charts, filters, table, states, and animations.
- **Phase D — test/deployment hardening:** run Python tests, lint/typecheck/build, Playwright, Docker smoke tests, and production smoke tests.
- **Phase E — submission pack:** complete README, anonymous public repository, public deployment, unlisted demo video, and private/incognito link verification.

Do not skip a phase just because the UI looks finished.

---

## 1. Assignment requirements — authoritative scope

The client is a UK electricity retailer purchasing electricity from the wholesale day-ahead market. The product helps the purchasing team understand national renewable generation forecasts available at decision time and assess how accurate those forecasts were compared with actual generation.

### Required deliverables and constraints

- **Frontend:** React.
- **Backend:** Python.
- **Analysis:** Great Britain national-level wind-generation actuals and forecasts, using Elexon data only for this challenge.
- **Target dates:** delivery intervals in **January 1–31, 2026** only.
- **Actual dataset:** `FUELHH`, filtered to `fuelType=WIND`.
- **Forecast dataset:** `WINDFOR`, using `startTime`, `publishTime`, and `generation`.
- **Resolution/units:** half-hourly intervals; generation is in MW.
- **Local reproducibility:** provide Docker support.
- **Public app:** deploy the working sample application on Vercel or Heroku as requested. If deployment constraints make a separate backend host necessary, keep the submitted application URL on a supported public frontend and document the API URL clearly.
- **Public source repository:** use an anonymous/random repository name, as the assignment requests. Do not put personal identifiers in the repository name.
- **README:** explain files/folders, exact startup steps, deployment URL, and AI tool use explicitly and truthfully.
- **Video:** unlisted YouTube, no more than **10 minutes total**. Part 1 is a customer-facing pilot/product demonstration (maximum 5 minutes); Part 2 is a technical review/knowledge transfer (maximum 5 minutes).
- **Timebox:** no more than 16 hours on the assignment.
- **Submission form:** submit all required details and test each submitted URL in a private/incognito browser window before submitting.

**Out of scope:** price forecasting, price-impact claims, a new ML forecasting model, authentication, a database, accounts, billing, and features that require data not listed in the challenge. Never imply the dashboard recommends a specific trading action: it is a forecast quality/decision-support tool, not a trading system.

---

## 2. Critical data rule: model the forecast available at purchase-decision time

This is the most important part of the assignment. A beautiful dashboard with an incorrect forecast-vintage selection is a failed solution.

### Field definitions

- `startTime`: the target/delivery half-hour that a generation value refers to.
- `publishTime`: the time a forecast record became available/published.
- `generation`: generation in MW.
- Actual `FUELHH` records are selected for `fuelType=WIND` and matched to forecast target timestamps.

### Required decision-time policy

The brief says the team makes its power purchase decision one day before the delivery day. Use this explicit, auditable assumption unless the hiring team supplies a more precise timestamp:

For a target delivery interval on local delivery date **D**, calculate the deadline as the start of date D in `Europe/London`. Select the latest forecast version for that target where:

`publishTime < start_of_delivery_date_in_Europe_London`

In plain English: use the latest version published strictly before the delivery date starts, modeling the forecast available by the end of the prior calendar day. Explain this assumption in the UI and README; do not present it as an unqualified fact about the company's actual internal trading cut-off.

### Correct algorithm

1. Parse source timestamps into timezone-aware datetimes. Never compare naive and timezone-aware values.
2. Normalize actual and forecast `startTime` values to a consistent instant, retaining UTC internally. Convert to `Europe/London` to determine the target's local delivery date and business cut-off.
3. Restrict **target/delivery intervals** to `2026-01-01 <= local delivery date < 2026-02-01`.
4. Retrieve enough historical forecast publication records to include the forecast versions eligible for January targets. At a minimum, confirm coverage of records published before January 1 that could apply to January 1 delivery intervals.
5. For every target `startTime`, discard versions with `publishTime >= deadline`.
6. From the eligible versions, choose the one with the greatest `publishTime`. Use a stable tie-break only if the data actually contains identical publication times, and document it.
7. Join the selected forecast to actual generation on normalized target `startTime`, not on `publishTime` or row order.
8. Keep the raw selected publication timestamp in the analysis result so the logic can be inspected.
9. Exclude missing or invalid values from numerical error calculations, but retain them in coverage diagnostics. **Do not silently fill missing values with zero.**
10. Show the selected forecast's publication time for interval-level rows, so reviewers can confirm it satisfies the cut-off.

### Data-source feasibility gate — do this before UI work

The assignment links directly to the Elexon documentation for:

- FUELHH: <https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream>
- WINDFOR: <https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream>
- General API documentation: <https://bmrs.elexon.co.uk/api-documentation/endpoint>

Before implementing the client, inspect the current official endpoint docs and make small real requests. Confirm:

- the correct API base URL and exact query parameter names;
- whether the endpoint returns an array or an envelope such as `data`/`results`;
- date-time format and timezone conventions;
- maximum date range/response size and whether chunking or pagination is needed;
- whether the documented endpoint exposes historical forecast publication versions, not merely today's latest forecast;
- actual availability for the historical period January 2026;
- whether `generation` is numeric and whether zero is a valid observation.

The challenge's supplied dataset URLs are the starting point. If the current docs show that a particular stream is latest-only or has a different supported historical access method, use the documented Elexon historical/history/evolution endpoint that provides the records needed for the same `WINDFOR` dataset. Do not substitute a latest-only response and pretend it represents the prior-day vintage. Document the exact endpoint/query in `README.md` and leave a short comment in the client explaining why it supports the vintage selection.

Use environment configuration for the API base URL when useful, but do not invent API keys. Add timeouts, bounded retries for transient failures (429/5xx), a clear error for invalid query parameters, and reasonable request chunk sizes. Do not retry non-retryable 4xx responses indefinitely.

---

## 3. Metrics and data-quality reporting

For each valid matched interval:

- `forecast_mw = f`
- `actual_mw = a`
- `error_mw = f - a`
- `absolute_error_mw = abs(f - a)`

Calculate:

| Metric | Formula | Interpretation |
|---|---|---|
| MAE (MW) | `mean(abs(f - a))` | Average magnitude of forecast miss. |
| RMSE (MW) | `sqrt(mean((f - a)^2))` | Weights large misses more strongly. |
| Bias (MW) | `mean(f - a)` | Positive = over-forecast on average; negative = under-forecast. |
| Normalized MAE (%) | `MAE / mean(actual) * 100` | Include only when the denominator is valid and positive; explain the normalization. |
| Coverage (%) | `matched_valid_intervals / expected_intervals * 100` | Shows how much of the month has usable comparison data. |

January 2026 has **31 × 48 = 1,488 expected half-hour target intervals**. Use that as the expected count for this analysis month, but calculate actual coverage from the actual joined dataset. Do not assume all records exist merely because the expected count is known.

Avoid ordinary MAPE as the headline metric because percentage error is unstable when actual generation approaches zero. Report missing actual intervals, missing eligible forecast intervals, invalid records, and matched intervals. If a data source is unavailable, display a clear source/data-quality warning rather than silently changing the analysis.

### Minimum result shape

Provide a validated typed response containing, at minimum:

- `month`, `timezone`, `units`, `source`, and `generatedAt`;
- `decisionCutoffDescription`;
- `expectedIntervals`, `matchedIntervals`, `missingActualIntervals`, `missingEligibleForecastIntervals`, and `coveragePercent`;
- `metrics` containing MAE, RMSE, bias, and normalized MAE when valid;
- `series[]` with `startTime`, `actualMw`, `forecastMw`, `publishTime`, `errorMw`, and `absoluteErrorMw` where available;
- `daily[]` with delivery date, valid interval count, coverage, MAE, RMSE, and bias;
- `warnings[]` describing partial data or endpoint issues.

Represent unavailable numeric results as `null`, not `0`, and show a human-readable “Not available” state in the UI. Validate the output schema before sending it to React.

---

## 4. Recommended architecture and project structure

Use the simplest architecture that makes the logic testable and deployable.

### Stack

- Frontend: React + TypeScript + Vite.
- UI: semantic components, CSS variables/design tokens, and a small consistent component system. Tailwind CSS is fine if already installed; avoid mixing several styling systems.
- Charts: Recharts or another lightweight, responsive chart library. Prefer a chart with controllable tooltip/axis formatting over custom SVG from scratch.
- Backend: Python + FastAPI + Pydantic + HTTPX.
- Backend tests: pytest.
- Browser tests: Playwright Test (`@playwright/test`).
- Local full-stack environment: Docker Compose.
- Optional lightweight cache: in-memory TTL cache. No database required.

### Suggested repository structure

```text
<random-repo-name>/
├── frontend/
│   ├── src/
│   │   ├── app/                 # app shell, router, theme
│   │   ├── components/          # reusable UI, charts, tables, states
│   │   ├── features/analysis/   # analysis page, filters, hooks
│   │   ├── lib/                 # API client, formatting, helpers
│   │   ├── styles/              # tokens, global styles
│   │   └── types/               # API response types
│   ├── tests/e2e/               # Playwright specs
│   ├── playwright.config.ts
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes.py
│   │   ├── schemas.py
│   │   ├── clients/elexon.py
│   │   └── services/analysis.py
│   ├── tests/                   # pytest unit/integration tests
│   └── requirements.txt
├── Dockerfile                   # or separate frontend/backend Dockerfiles
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

Adjust the exact layout to fit the existing repo, but keep external I/O, data transformations, API schemas, and UI rendering separate. Avoid a giant `App.tsx` or one Python file that contains fetch, transform, route, and metrics logic together.

### Backend endpoints

- `GET /api/health`: liveness/readiness status and version.
- `GET /api/analysis?month=2026-01`: metrics, series, daily summaries, coverage, methodology, and warnings.
- `GET /api/analysis/day?date=2026-01-15`: interval-level records for an allowed day in January 2026.

Return sensible HTTP errors and JSON error bodies. Reject dates/months outside the challenge's scope rather than letting frontend controls suggest unsupported ranges. Enable CORS only for the actual local/deployed frontend origin; do not use a wildcard in production unless there is a specific, documented reason.

### Backend engineering requirements

- Split Elexon HTTP retrieval from data cleaning and analysis calculations.
- Validate `startTime`, `publishTime`, and `generation` types; skip or flag malformed rows with counters.
- Use `httpx` timeouts and bounded retries/backoff for transient errors.
- Cache a successful analysis response for a short TTL to avoid refetching the entire month on every UI interaction.
- Never cache error responses as valid empty analysis.
- Add logging that helps diagnose endpoint failures without dumping huge raw payloads or secrets.
- Do not add a database, authentication, paid APIs, or ML inference.

---

## 5. Product concept and visual direction

Build a product that could plausibly be shown to an energy-purchasing team: calm, precise, data-first, and polished. The dashboard should feel like a high-quality analytics product, not a generic admin template.

### Product name and copy

Use a restrained temporary product name such as **WindScope** (do not imply this is the client's existing company/product branding). Page title:

**Wind Forecast Accuracy**  
`Great Britain · January 2026`

Introductory explanation:

> Compare the day-ahead wind generation forecast available before delivery with recorded generation. Use the results to understand forecast errors and data coverage—not as a standalone trading recommendation.

Show a small source/methodology tag such as `Elexon data` and a clearly discoverable `How this is calculated` action.

### Color palette — use design tokens, not scattered literals

Start with a light, high-contrast analytics theme and optionally offer a dark theme if it does not delay the required functionality.

| Token | Suggested color | Use |
|---|---|---|
| `--page` | `#F4F7FA` | App background, subtle cool gray. |
| `--surface` | `#FFFFFF` | Cards, panels, tables. |
| `--surface-muted` | `#EEF3F6` | Secondary surfaces and hover rows. |
| `--ink` | `#152536` | Main text and headings. |
| `--muted` | `#5B6B7A` | Supporting text, captions, axis labels. |
| `--border` | `#DCE5EB` | Borders, dividers, input outlines. |
| `--primary` | `#087F8C` | Primary action and selected controls. |
| `--forecast` | `#697BE8` | Forecast series; visibly distinct from actual. |
| `--actual` | `#078A70` | Actual generation series. |
| `--warning` | `#A65C00` | Partial coverage and non-blocking warnings. |
| `--danger` | `#B42318` | Blocking errors only. |
| `--focus` | `#2563EB` | Keyboard focus ring. |

Use a restrained palette: most of the page should be neutral. Reserve warning/error colors for genuine status. Never rely on color alone; pair colors with series names, labels, line style, icons, or text. Verify text/background contrast; do not put small low-contrast text over gradients.

### Typography and spacing

- Use Inter or a comparable readable sans-serif; system fallback must work if a font cannot load.
- Use a consistent type scale: page title approximately 28–32 px desktop and 23–26 px mobile; section headings 16–20 px; body 14–16 px; dense chart/table labels no smaller than is comfortably readable.
- Adopt a spacing scale such as 4, 8, 12, 16, 20, 24, 32, 40.
- Prefer generous alignment, consistent card padding, and fewer clearly structured panels over many tiny cards.
- Use a consistent radius (roughly 12–16 px), quiet borders, and restrained shadows. Avoid glassmorphism, excessive blur, giant gradients, excessive pill badges, and overused animation.

### Core page layout

**Desktop (≥1200 px)**

1. Compact top bar: product mark/name, “Great Britain” scope, date label, source status, refresh action.
2. Page title and one-sentence context.
3. Four KPI cards in one row: MAE, RMSE, bias, data coverage. Each card has a clear value, unit, concise interpretation, and optional tiny neutral trend/context text only if computed from real data.
4. Main analytics section: forecast vs actual line chart in the larger column; secondary error/coverage context in the smaller column only if it remains readable.
5. Daily error analysis across the full width.
6. Interval detail table, followed by a methodology/source panel that can expand/collapse.

**Tablet (768–1199 px)**

- Keep a compact header and wrap filter/status controls cleanly.
- KPIs use 2×2.
- Charts stack or use a balanced two-column grid only when legible.
- Do not squeeze axis labels or table cells to preserve a desktop layout.

**Mobile (≤767 px)**

- Use a single-column flow with a compact top bar and a real accessible menu only if navigation exists.
- KPIs use 2 columns on ordinary phones and 1 column on very narrow screens.
- Chart cards become full width; legends wrap; long date labels simplify but retain full timestamps in tooltips.
- Table becomes a mobile-friendly card/list layout or a deliberately horizontally scrollable table with a visible affordance. Do not cause page-level horizontal overflow.
- Stack filters and buttons; give touch targets comfortable size (aim for at least 44×44 CSS px where practical).
- Ensure sticky elements do not cover headings, charts, dialogs, or focused controls.

### Data visualization rules

**Primary chart: forecast vs actual**

- Two clearly labeled lines: `Forecast (MW)` and `Actual (MW)`.
- Use `startTime` as the x-axis; y-axis label includes `Generation (MW)`.
- Use a clear legend, gridlines with low visual weight, and a custom tooltip showing date/time, forecast MW, actual MW, signed error MW, and the selected forecast's publish time.
- Allow switching between a whole-month view and an individual delivery day, while keeping target data limited to January 2026.
- Do not make claims from a smoothed/aggregated line unless the aggregation is labeled.

**Daily error chart**

- Show daily MAE (MW) with a clear label and a usable tooltip containing date and valid interval count.
- Missing days should remain visibly missing or show a gap; never draw them as zero error.

**Interval table**

Columns at desktop: delivery time (Europe/London), forecast (MW), actual (MW), signed error (MW), absolute error (MW), forecast published at.

- Format values consistently to a sensible number of decimal places without hiding meaningful variation.
- Support empty/partial rows and expose missing values as `—`/“Not available” instead of zero.
- Add labeled sort controls only if implemented correctly. Pagination/day selection is acceptable; avoid building a complicated table framework for 1,488 possible rows.

**KPI presentation**

- MAE and RMSE: show `MW` explicitly.
- Bias: show sign and explain positive/negative meanings.
- Coverage: show `%` and matched/expected intervals, e.g. `n / 1,488 intervals`.
- If metrics are unavailable, show `Not available`, and the reason, rather than `0.0`.

### Required interaction/states

- Initial loading skeletons sized like the completed components to minimize layout shift.
- A compact, honest data-source status (`Loaded`, `Partial data`, or `Unavailable`) driven by API response state.
- Retry/refresh action with disabled/spinner state while a request is in progress and a clear result/error message.
- Clear “How this is calculated”/methodology dialog or disclosure panel explaining source, date/time rules, vintage policy, timezone, metrics, coverage, and limitations.
- Empty-data state with useful guidance and a retry path where applicable.
- Partial-data warning that explains what is missing and how that affects interpretation.
- Blocking-error state that preserves context and offers retry. Do not leave a perpetual spinner on failure.
- Keyboard focus indicator, sensible tab order, visible button states, reduced-motion support, and screen-reader labels for icon-only buttons.

### Animation and transition guidance

Motion should clarify state change and add finish—not delay analysis or distract from changing numbers.

- Use small entrance transitions on the title/KPIs/chart cards: approximately 160–240 ms, with subtle opacity and 6–10 px movement at most.
- Stagger card entrance only once; do not animate every new data point as if it were a marketing site.
- Buttons and clickable cards can use 120–180 ms color/border/shadow transitions.
- Skeleton shimmer may be subtle; avoid flashing or high-frequency movement.
- Chart transitions should be brief and should not make comparing data difficult. Disable or reduce transitions when `prefers-reduced-motion: reduce` is active.
- Do not animate essential data into view in a way that delays keyboard or screen reader access.
- Prefer CSS transitions for simple interactions; add Framer Motion only if it materially improves the UI and fits the timebox.

---

## 6. API client and frontend behavior

### Frontend API client

- Read the backend base URL from an environment variable (for example `VITE_API_BASE_URL`) and document it in `.env.example`.
- In local development, configure a Vite proxy to `/api` where possible to reduce unnecessary CORS complexity.
- Validate/defensively parse the API response at the boundary. TypeScript types alone do not validate runtime JSON.
- Add a bounded request timeout and display a readable error if the API is unreachable.
- Prevent race conditions when users change a day/filter quickly: cancel stale fetches with `AbortController` or ignore outdated responses.
- Keep filter state in one clear source of truth; charts, metrics, and table must update together.
- Do not log large payloads or turn a failed request into an empty-success state.

### Data presentation integrity

- The UI must label the target interval timezone as `Europe/London`.
- The application must show the exact forecast cut-off rule.
- Show the analysis period as January 2026 and do not imply future/current forecasts are part of the requested retrospective.
- Display a generated/last-loaded time when supplied by the backend.
- If the backend response includes warnings or partial coverage, preserve them visibly.
- Do not report a better/worse “trend” unless both comparison periods are genuinely present and the comparison is well-defined.

---

## 7. Automated testing — mandatory, use Playwright

A final browser test run is a release gate. Build the tests and then execute them. A test file that was never run is not proof of verification.

### 7.1 Backend unit tests (pytest)

At minimum, add deterministic tests for:

1. The latest eligible forecast version is selected for a target interval.
2. A forecast published exactly at or after the delivery-day deadline is excluded (`publishTime < deadline`, strictly).
3. A later-published but ineligible forecast is never used even if it is closer to actual generation.
4. The same target with multiple eligible versions selects the highest eligible `publishTime`.
5. Joining uses normalized target `startTime`, not the publication timestamp or record order.
6. January 1 targets can use eligible forecast publications from December 31.
7. February target intervals are excluded; January target intervals are included.
8. Timestamps with `Z`/UTC offsets are normalized safely; local delivery date is evaluated in `Europe/London`.
9. Duplicate records do not multiply joined interval rows.
10. Missing forecast and missing actual records affect coverage but do not become zero values.
11. Zero actual generation is kept as a valid observation when the source supplies a real zero.
12. MAE, RMSE, bias, normalized MAE, and interval counts match a small hand-calculated fixture.
13. Empty arrays, unexpected response envelopes, malformed numeric fields, HTTP 429, HTTP 5xx, and timeout errors produce explicit, testable results/errors.
14. January 2026 expected count is 1,488 and reported matched coverage cannot exceed expected count after deduplication.

Use pytest fixtures or mocked HTTP responses for deterministic tests. Do not make unit tests depend on the live Elexon service.

### 7.2 Frontend checks before E2E

Run the actual available scripts, or add reliable ones for:

- formatting/lint;
- TypeScript typecheck;
- production build;
- frontend unit tests, if a unit test framework is already included or can be added quickly;
- backend pytest.

No TypeScript errors, unhandled Promise rejections, unused broken UI controls, or major console warnings should remain.

### 7.3 Playwright setup and quality bar

Install `@playwright/test` and the required browser binaries. Add a `playwright.config.ts` with:

- a local base URL from environment configuration;
- `webServer` setup for frontend and backend, or an equivalent documented command that reliably starts both;
- projects for Chromium desktop and a mobile emulation (for example Pixel 7/iPhone-like viewport); add Firefox and WebKit projects if time/resources allow;
- screenshot and trace capture on failures (`screenshot: 'only-on-failure'`, trace on first retry or retained on failure); videos on first retry are useful but optional;
- bounded timeouts and CI-friendly retries; do not use repeated retries to hide flaky tests;
- stable deterministic API fixtures for UI behavior tests. Keep at least one separate live-API smoke test/manual check so fixtures cannot hide a broken integration.

Use user-facing locators such as `getByRole`, `getByLabel`, and `getByText`; use `data-testid` only for components without a stable accessible locator. Avoid brittle long CSS/XPath selectors, arbitrary sleeps, and assertions tied to animation timing. Wait for observable state and use Playwright's auto-waiting.

### 7.4 Required Playwright E2E scenarios

**Core page and data rendering**

- Dashboard loads without uncaught JavaScript errors.
- Main heading and January 2026 scope are visible.
- All four KPI cards display values or honest unavailable states.
- Forecast and actual chart legends/labels are present.
- Table renders rows, including correct missing-value display.
- The methodology disclosure opens, contains the forecast cut-off rule, and can be closed by keyboard.
- Selected-day control updates the line chart/table coherently and stays inside January 2026.
- Refresh button shows a loading state and recovers to success or error.

**Error/data states**

- Slow API shows a visible loading state without layout collapse.
- API 500/timeout shows a readable error and retry action, not fake metrics.
- Empty response displays an empty state, not a success chart of zeros.
- Partial data displays a warning and coverage is less than 100% where appropriate.
- Invalid API data does not crash the page.

**Responsive layout**

Run at minimum these viewports: `320×740`, `375×812`, `390×844`, `768×1024`, `1024×768`, and `1440×900`.

At each size:

- assert that `document.documentElement.scrollWidth <= document.documentElement.clientWidth` unless a deliberately horizontally scrollable child table/chart is responsible and the document itself does not overflow;
- verify page title, KPI values, chart card, and primary controls are visible and not clipped;
- ensure chart legends and tooltips remain usable;
- check mobile table handling and tap targets;
- check that no fixed/sticky layer covers important content.

**Accessibility basics**

- Keyboard Tab traversal reaches each interactive control and focus is visible.
- Inputs have labels, icon-only controls have accessible names, dialogs/disclosures are operable using keyboard.
- Color is not the only way to differentiate forecast and actual series.
- Respect `prefers-reduced-motion`.
- Use an automated axe scan if feasible, and fix serious/critical violations. An axe scan does not replace keyboard testing.

**Network/console hygiene**

- Collect uncaught `pageerror` events and unexpected console errors during each core scenario and fail the test if any occur.
- Inspect failed network requests and unexpected non-2xx API responses; explicitly allow only intentional failures in error-state tests.
- Do not let a favicon/font warning obscure genuine application failures; fix avoidable errors rather than broadly ignoring console messages.

### 7.5 Visual verification — do not skip screenshot review

After Playwright passes:

1. Capture screenshots of the dashboard at desktop, tablet, and mobile sizes using the real app and deterministic fixture data.
2. Open/review the screenshots. Check alignment, text clipping, overlong headings, chart density, tooltips, KPI grid behavior, whitespace, and errors/partial states.
3. Fix visible problems and rerun the affected Playwright tests. Do not simply produce screenshots without inspecting them.
4. Store useful reference screenshots in an appropriate `artifacts/` or `test-results/` path; do not commit huge videos/traces unless they are needed.
5. When practical, run Playwright against the deployed public URL as a production smoke test. Keep this run separate from deterministic local fixture tests.

### 7.6 Example scripts (adapt to the repo)

Frontend `package.json` should offer clear commands similar to:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint .",
    "typecheck": "tsc --noEmit",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

Only keep commands that are correctly configured and runnable. Add a root script or documented sequence to run Python tests and browser tests without guesswork. Use Playwright reports/traces to debug failures.

---

## 8. Docker, deployment, and production verification

### Docker/local development

- Provide `docker-compose.yml` that starts the backend and frontend with documented ports and correct service networking.
- Add health checks if they are reliable and make `depends_on` behavior clear; do not assume `depends_on` alone guarantees readiness.
- Keep secrets out of the repo. Add `.env.example` with placeholder keys only where needed.
- Verify a fresh checkout can start with the README commands and that the frontend can reach the backend.
- Avoid building large images unnecessarily; pin compatible dependency ranges and keep the setup easy to reproduce.

### Deployment approach

Choose the deployment path that actually works with the selected framework and plan limits. The assignment asks for Vercel or Heroku. Verify current platform docs and the selected account's limits instead of assuming a particular free-tier capability.

Preferred decision process:

1. If a single Vercel project can reliably serve the React app and Python API with the current project structure and runtime limits, use it and prove the deployed API endpoints respond.
2. Otherwise deploy the React frontend to Vercel and the FastAPI service to a compatible public Python host; document this split clearly and make sure the user-facing app link is the Vercel frontend.
3. Configure production CORS and `VITE_API_BASE_URL` correctly; do not point the production app at localhost.
4. Test cold-start behavior, timeout behavior, CORS, and the app from a private/incognito browser session.
5. Check the actual app link and API health endpoint immediately before submission/video recording. If deployment sleeps, refresh or wake it before the demo and mention only known limitations.

### Production smoke checks

- Frontend returns a successful HTTP response and renders the expected page.
- `/api/health` returns healthy status.
- `/api/analysis?month=2026-01` responds with the expected schema and realistic source metadata.
- The page works after a hard refresh on its public URL.
- Browser network calls go to the deployed API; no localhost URLs, secret values, or mixed-content errors.
- API CORS accepts the deployed origin and rejects unapproved origins as configured.
- Error states remain helpful when the backend is temporarily unavailable.
- Public repository and deployment do not require the evaluator to sign in.

Do not call a deployment “complete” until these checks are actually executed.

---

## 9. README and repo hygiene

README must be written for a reviewer who has never seen the project. Include:

1. What the dashboard answers and screenshots/preview (if available).
2. Features and explicit scope/limitations.
3. Data source links and exact endpoints/query filters used.
4. The decision cut-off assumption, timezone, how the selected forecast vintage is chosen, and how missing data affects coverage.
5. Metric definitions with units.
6. Architecture diagram or concise request/data flow.
7. Repository directory guide.
8. Exact prerequisites and local startup commands for both Docker Compose and (if provided) manual development.
9. Backend/frontend test commands, including the Playwright command and browser installation step.
10. Environment variables and `.env.example` reference.
11. Public deployment URL and API health URL.
12. AI assistance disclosure, accurate to the actual process used.
13. Known limitations or source-data gaps.

Git/repository hygiene:

- Use the requested anonymous/random repository name.
- Include `.gitignore` for `.env`, `node_modules`, virtual environments, caches, Playwright traces/videos, build output, and local data dumps.
- Never commit secrets, private tokens, large raw API dumps, or generated dependency directories.
- Do not commit dummy “real” chart data.
- Ensure tests and README commands match actual file names and scripts.

---

## 10. Exact 16-hour priority schedule

| Time budget | Task | Exit gate |
|---|---|---|
| 0–1 h | Inspect brief and official docs; test actual and forecast historical access | Confirm actual query and a valid historical forecast-vintage query. If vintage data is unavailable from a chosen endpoint, resolve this before continuing. |
| 1–3 h | Build API client, normalization, cutoff/vintage selection, join | Deterministic January interval analysis; no look-ahead bias. |
| 3–4 h | Metrics and pytest suite | All domain tests pass, including strict cut-off behavior and coverage. |
| 4–8 h | Responsive UI, design tokens, charts, data table, methodology panel, all states | Coherent desktop/mobile design without horizontal page overflow. |
| 8–10 h | API/frontend integration, Docker, lint/typecheck/build | Fresh local startup works; no fake success states. |
| 10–12 h | Playwright scenarios, screenshots, accessibility fixes | Core E2E passes; desktop and mobile screenshots reviewed. |
| 12–14 h | Deploy and production smoke tests | Public app and API work from an unauthenticated session. |
| 14–15 h | README, repository cleanup, video recording | Reviewers can run and understand it; demo fits 10 minutes. |
| 15–16 h | Final private/incognito checks and submission form | Every submitted URL accessible; no unverified claims. |

If behind schedule: drop secondary visualizations or an optional theme switch before dropping data correctness, error states, Playwright, deployment, or the video. Avoid any new feature after hour 12 unless it fixes a blocker.

---

## 11. Video walkthrough — 10 minutes maximum

Record an unlisted YouTube video with the two required parts. Keep it natural; do not spend the first minute on introductions.

### Part 1 — customer-facing pilot (0:00–5:00)

- **0:00–0:30:** State the problem: purchasing teams need to assess forecasts that would have been available before delivery.
- **0:30–1:30:** Explain the KPI cards and use MAE/bias in plain language.
- **1:30–2:45:** Show forecast vs actual on the chart and inspect a specific day's tooltip.
- **2:45–3:45:** Show daily errors and the interval table.
- **3:45–4:30:** Explain the cut-off rule and how the app avoids using a later forecast.
- **4:30–5:00:** Point out coverage, missing data, and the main limitations.

### Part 2 — technical review (5:00–10:00)

- **5:00–5:45:** Show the repository layout and run commands.
- **5:45–6:45:** Explain the Elexon client and why forecast retrieval needs historical versions.
- **6:45–7:45:** Show the vintage-selection logic and a test proving the cut-off.
- **7:45–8:30:** Explain metrics, missing values, and coverage.
- **8:30–9:15:** Show React component structure and responsive behavior.
- **9:15–9:45:** Show pytest/Playwright commands or report, Docker, and deployment architecture.
- **9:45–10:00:** Summarize one trade-off/limitation and a sensible next step.

Do not submit without the video. Verify the YouTube link is accessible to anyone with the link in a private window.

---

## 12. Release checklist — every item must be truthfully checked

### Data correctness

- [ ] Exact current official endpoint/query confirmed and documented.
- [ ] Historical January 2026 actuals retrieved or a transparent source-data blocker is reported.
- [ ] Historical WINDFOR vintages verified; not silently replaced by latest-only values.
- [ ] `publishTime` is strictly before the delivery-day start in `Europe/London` for every selected forecast.
- [ ] Forecast and actual are joined on normalized `startTime`.
- [ ] January target intervals only; December publications can still qualify for January delivery.
- [ ] Metrics reproduce hand-calculated fixtures; missing observations are not zeros.
- [ ] Coverage counts and warnings agree with returned data.

### Product and UI

- [ ] Layout reviewed at 320, 375, 390, 768, 1024, and 1440 px widths.
- [ ] No page-level horizontal overflow or clipped controls.
- [ ] Forecast/actual are distinguishable beyond color alone.
- [ ] Units, timezone, metric explanations, and cut-off assumption are visible.
- [ ] Loading, empty, partial, and error states were tested.
- [ ] Reduced-motion and keyboard focus behavior are reasonable.
- [ ] The UI does not claim to recommend trades or predict prices.

### Quality and deployment

- [ ] Backend pytest suite passes.
- [ ] Frontend lint/typecheck/production build passes.
- [ ] Playwright core E2E passes in Chromium and mobile emulation.
- [ ] Browser console/page errors inspected; unexpected errors fixed.
- [ ] Failure screenshots/traces are enabled; representative screenshots reviewed.
- [ ] Docker startup verified from a clean checkout.
- [ ] Public deployment and API health/analysis endpoint smoke-tested.
- [ ] App link, repository, and video all open in private/incognito mode.
- [ ] README matches the actual project and AI disclosure is truthful.
- [ ] Submission form completed only after all links were checked.

---

## 13. Final report from the coding agent

When implementation is finished, return a concise, evidence-based completion report containing:

1. What was implemented (backend, frontend, charts, UX states, deployment).
2. Exact data endpoint(s) and observed historical-vintage behavior.
3. The implemented cut-off rule and where it is explained.
4. Commands executed and actual results for pytest, lint, typecheck, production build, Docker, and Playwright (include test counts and any skips).
5. Viewports/browsers tested, screenshots reviewed, and material console/network findings.
6. Public app, API health, and public repository URLs.
7. Any known failures, data gaps, host limitations, or incomplete deliverables.
8. Whether the unlisted video and submission form are complete. If they are not, say so plainly.

**Definition of done:** A working, deployed, source-backed dashboard with correct historical forecast-vintage selection; explainable metrics; polished responsive UI; automated backend and Playwright coverage; a usable README; and honest submission artifacts. A good-looking screenshot alone is not done.

---

## Official references

- Assignment's FUELHH endpoint documentation: <https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream>
- Assignment's WINDFOR endpoint documentation: <https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream>
- Elexon Insights API documentation index: <https://bmrs.elexon.co.uk/api-documentation/endpoint>
- Elexon historical/latest wind forecast documentation (use only if it is the verified suitable interface for the needed historical versions): <https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/latest/stream>
- Playwright locators and resilient test selection: <https://playwright.dev/docs/locators>
- Playwright best practices: <https://playwright.dev/docs/best-practices>
- Playwright browser projects: <https://playwright.dev/docs/test-projects>
- Playwright traces/screenshots/videos: <https://playwright.dev/docs/test-use-options>
