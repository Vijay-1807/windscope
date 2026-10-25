import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("windscope.main")

app = FastAPI(
    title="WindScope API",
    description=(
        "Decision-support API for Great Britain national wind generation forecast accuracy analysis (January 2026). "
        "Evaluates day-ahead forecast vintages available strictly before the delivery day cut-off against recorded FUELHH actuals."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS configuration
allowed_origins_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
)
allowed_origins = [orig.strip() for orig in allowed_origins_env.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "WindScope API",
        "description": "Day-ahead wind forecast accuracy analysis for Great Britain (January 2026)",
        "docs": "/api/docs",
        "health": "/api/health",
        "analysis": "/api/analysis?month=2026-01"
    }
