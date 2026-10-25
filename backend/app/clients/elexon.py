import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger("windscope.elexon")

DEFAULT_ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

class ElexonAPIError(Exception):
    """Custom exception raised for Elexon API communication or format errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

class ElexonClient:
    """
    HTTP client for querying official Elexon BMRS API streams:
    - FUELHH/stream: Generation by Fuel Type (filtered to fuelType=WIND)
    - WINDFOR/stream: Wind Generation Forecast evolution stream (vintages)
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 45.0, max_retries: int = 3):
        self.base_url = (base_url or os.getenv("ELEXON_API_BASE_URL", DEFAULT_ELEXON_BASE_URL)).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    async def _get_with_retry(self, endpoint: str, params: Dict[str, str]) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "WindScope/1.0 (+https://github.com/windscope)"
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.info("Calling Elexon API endpoint: %s (attempt %d/%d)", endpoint, attempt, self.max_retries)
                    resp = await client.get(url, params=params, headers=headers)

                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except Exception as json_err:
                        raise ElexonAPIError(f"Failed to decode JSON response from {endpoint}: {json_err}", status_code=200)

                # Check if transient error eligible for retry
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    backoff = 1.0 * (2 ** (attempt - 1))
                    logger.warning(
                        "Transient error %d from Elexon API (%s). Backing off for %.1fs...",
                        resp.status_code, endpoint, backoff
                    )
                    await asyncio.sleep(backoff)
                    continue

                # Non-retryable error or exhausted retries
                error_body = resp.text[:300]
                raise ElexonAPIError(
                    f"Elexon API returned status {resp.status_code} for {endpoint}: {error_body}",
                    status_code=resp.status_code
                )

            except httpx.TimeoutException as te:
                last_error = te
                if attempt < self.max_retries:
                    backoff = 1.0 * (2 ** (attempt - 1))
                    logger.warning("Timeout connecting to Elexon API (%s). Retrying in %.1fs...", endpoint, backoff)
                    await asyncio.sleep(backoff)
                    continue
                raise ElexonAPIError(f"Timeout connecting to Elexon API ({endpoint}) after {self.max_retries} attempts: {te}")
            except httpx.RequestError as re:
                last_error = re
                if attempt < self.max_retries:
                    backoff = 1.0 * (2 ** (attempt - 1))
                    logger.warning("Network error contacting Elexon API (%s): %s. Retrying...", endpoint, re)
                    await asyncio.sleep(backoff)
                    continue
                raise ElexonAPIError(f"Network error contacting Elexon API ({endpoint}): {re}")

        raise ElexonAPIError(f"Failed to fetch data from {endpoint}: {last_error}")

    async def fetch_fuelhh_wind(self, publish_from: str, publish_to: str) -> List[Dict[str, Any]]:
        """
        Fetch FUELHH actual wind generation records between two ISO publish timestamps.
        Only rows with fuelType='WIND' and valid generation are returned.
        """
        data = await self._get_with_retry(
            "datasets/FUELHH/stream",
            params={
                "publishDateTimeFrom": publish_from,
                "publishDateTimeTo": publish_to
            }
        )

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("data", [])
        else:
            raise ElexonAPIError(f"Unexpected FUELHH response structure: expected list or envelope with 'data' array.")

        wind_records = []
        for row in items:
            if not isinstance(row, dict):
                continue
            if row.get("fuelType") == "WIND" and row.get("generation") is not None:
                wind_records.append(row)

        logger.info("Fetched %d FUELHH records, filtered to %d WIND records", len(items), len(wind_records))
        return wind_records

    async def fetch_windfor(self, publish_from: str, publish_to: str) -> List[Dict[str, Any]]:
        """
        Fetch WINDFOR forecast records published between two ISO publish timestamps.
        Preserves all publication vintages so the decision-time selector can pick the latest eligible version.
        """
        data = await self._get_with_retry(
            "datasets/WINDFOR/stream",
            params={
                "publishDateTimeFrom": publish_from,
                "publishDateTimeTo": publish_to
            }
        )

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("data", [])
        else:
            raise ElexonAPIError(f"Unexpected WINDFOR response structure: expected list or envelope with 'data' array.")

        valid_records = []
        for row in items:
            if not isinstance(row, dict):
                continue
            if row.get("generation") is not None and row.get("startTime") and row.get("publishTime"):
                valid_records.append(row)

        logger.info("Fetched %d WINDFOR forecast vintage records", len(valid_records))
        return valid_records
