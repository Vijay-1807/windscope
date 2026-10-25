import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.routes import get_analysis_service
from app.services.analysis import AnalysisService
from app.schemas import AnalysisResponse, MetricSummary, IntervalRecord, DailySummary

@pytest.fixture
def mock_service():
    """Deterministic mock service for route testing."""
    class MockAnalysisService(AnalysisService):
        async def get_monthly_analysis(self, month: str = "2026-01", force_refresh: bool = False):
            if month != "2026-01":
                raise ValueError("Unsupported month")
            return AnalysisResponse(
                month="2026-01",
                timezone="Europe/London",
                units="MW",
                source="Elexon Mock",
                generatedAt="2026-01-31T23:59:59Z",
                decisionCutoffDescription="Mock Cutoff",
                expectedIntervals=1488,
                matchedIntervals=744,
                missingActualIntervals=0,
                missingEligibleForecastIntervals=744,
                coveragePercent=50.0,
                metrics=MetricSummary(
                    mae=1919.28,
                    rmse=2395.25,
                    bias=1713.34,
                    normalizedMae=16.57,
                    meanActual=11581.11,
                ),
                series=[
                    IntervalRecord(
                        startTime="2026-01-01T00:00:00Z",
                        localStartTime="2026-01-01 00:00 GMT",
                        actualMw=13756.0,
                        forecastMw=19498.0,
                        publishTime="2025-12-31T22:30:00Z",
                        localPublishTime="2025-12-31 22:30 GMT",
                        errorMw=5742.0,
                        absoluteErrorMw=5742.0,
                    )
                ],
                daily=[
                    DailySummary(
                        date="2026-01-01",
                        expectedIntervals=48,
                        matchedIntervals=24,
                        coveragePercent=50.0,
                        mae=1500.0,
                        rmse=1800.0,
                        bias=1200.0,
                        meanActual=12000.0,
                    )
                ],
                warnings=["Sample mock warning"],
            )

    return MockAnalysisService()

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "windscope-backend"
        assert "timestamp" in data

@pytest.mark.asyncio
async def test_monthly_analysis_success(mock_service):
    async def override():
        return mock_service
    app.dependency_overrides[get_analysis_service] = override
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/analysis?month=2026-01")
            assert resp.status_code == 200
            data = resp.json()
            assert data["month"] == "2026-01"
            assert data["expectedIntervals"] == 1488
            assert data["matchedIntervals"] == 744
            assert data["coveragePercent"] == 50.0
            assert data["metrics"]["mae"] == 1919.28
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_monthly_analysis_unsupported_month():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/analysis?month=2025-12")
        assert resp.status_code == 400
        data = resp.json()
        assert "Only '2026-01' (January 2026) is supported" in data["detail"]

@pytest.mark.asyncio
async def test_day_analysis_success(mock_service):
    async def override():
        return mock_service
    app.dependency_overrides[get_analysis_service] = override
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/analysis/day?date=2026-01-01")
            assert resp.status_code == 200
            data = resp.json()
            assert data["date"] == "2026-01-01"
            assert data["expectedIntervals"] == 48
            assert "metrics" in data
            assert "intervals" in data
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_day_analysis_invalid_date():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Date outside January 2026
        resp = await client.get("/api/analysis/day?date=2026-02-05")
        assert resp.status_code == 400
        assert "outside supported analysis scope" in resp.json()["detail"]
