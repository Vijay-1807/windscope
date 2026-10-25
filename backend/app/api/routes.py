from datetime import datetime, timezone
from typing import Optional
import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from ..schemas import AnalysisResponse, DayAnalysisResponse, HealthResponse, ErrorResponse
from ..services.analysis import AnalysisService, format_utc_iso
from ..clients.elexon import ElexonAPIError

logger = logging.getLogger("windscope.api")

router = APIRouter(prefix="/api", tags=["WindScope Analysis"])

# Dependency provider for AnalysisService
_service_instance: Optional[AnalysisService] = None

async def get_analysis_service() -> AnalysisService:
    global _service_instance
    if _service_instance is None:
        _service_instance = AnalysisService()
    return _service_instance

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health and readiness probe",
    description="Returns service liveness, current timestamp, and API version.",
)
async def get_health():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        service="windscope-backend",
        timestamp=format_utc_iso(datetime.now(timezone.utc)),
    )

@router.get(
    "/analysis",
    response_model=AnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Unsupported month requested"},
        502: {"model": ErrorResponse, "description": "Upstream Elexon API error"}
    },
    summary="Monthly forecast accuracy analysis",
    description="Computes error metrics, joined series, daily aggregates, and data coverage for January 2026.",
)
async def get_monthly_analysis(
    month: str = Query("2026-01", description="Delivery month (YYYY-MM). Only '2026-01' is supported."),
    refresh: bool = Query(False, description="Bypass cache and force re-fetch from upstream Elexon API."),
    service: AnalysisService = Depends(get_analysis_service),
):
    if month != "2026-01":
        raise HTTPException(
            status_code=400,
            detail=f"Month '{month}' is outside the challenge scope. Only '2026-01' (January 2026) is supported."
        )

    try:
        return await service.get_monthly_analysis(month=month, force_refresh=refresh)
    except ElexonAPIError as ee:
        logger.error("Upstream Elexon failure: %s", ee)
        raise HTTPException(status_code=502, detail=f"Elexon upstream communication error: {str(ee)}")
    except Exception as e:
        logger.exception("Unexpected error building monthly analysis: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error processing wind forecast analysis.")

@router.get(
    "/analysis/day",
    response_model=DayAnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid date format or date outside January 2026"},
        502: {"model": ErrorResponse, "description": "Upstream Elexon API error"}
    },
    summary="Daily interval-level analysis",
    description="Returns half-hourly actuals, selected forecast vintage, and errors for a specific date in January 2026.",
)
async def get_day_analysis(
    date: str = Query(..., description="Target delivery date (YYYY-MM-DD). Allowed: 2026-01-01 to 2026-01-31."),
    service: AnalysisService = Depends(get_analysis_service),
):
    try:
        return await service.get_day_analysis(date_str=date)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except ElexonAPIError as ee:
        logger.error("Upstream Elexon failure for day %s: %s", date, ee)
        raise HTTPException(status_code=502, detail=f"Elexon upstream communication error: {str(ee)}")
    except Exception as e:
        logger.exception("Unexpected error building day analysis for %s: %s", date, e)
        raise HTTPException(status_code=500, detail=f"Internal server error processing day analysis: {str(e)}")
