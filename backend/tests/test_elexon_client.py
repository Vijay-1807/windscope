import pytest
import httpx
from app.clients.elexon import ElexonClient, ElexonAPIError

@pytest.mark.asyncio
async def test_empty_arrays_returns_empty_list():
    """Empty response array returns clean empty list."""
    def handler(request: httpx.Request):
        return httpx.Response(200, json=[])

    client = ElexonClient(base_url="https://mock-elexon")
    # Patch httpx transport
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        # Override client._get_with_retry to use transport
        async def mock_get(endpoint, params):
            resp = await mock_http.get(f"https://mock-elexon/{endpoint}", params=params)
            return resp.json()
        client._get_with_retry = mock_get

        wind = await client.fetch_fuelhh_wind("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z")
        assert wind == []

@pytest.mark.asyncio
async def test_unexpected_response_envelope():
    """Non-list and non-dict envelope raises ElexonAPIError."""
    client = ElexonClient(base_url="https://mock-elexon")

    async def mock_get(endpoint, params):
        return "This is a raw text string, not valid envelope"
    client._get_with_retry = mock_get

    with pytest.raises(ElexonAPIError) as exc_info:
        await client.fetch_fuelhh_wind("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z")
    assert "Unexpected FUELHH response structure" in str(exc_info.value)

@pytest.mark.asyncio
async def test_malformed_numeric_rows_skipped():
    """Rows with missing generation or non-wind fuelType are filtered out safely."""
    client = ElexonClient(base_url="https://mock-elexon")

    sample_payload = [
        {"dataset": "FUELHH", "fuelType": "WIND", "generation": None}, # None generation
        {"dataset": "FUELHH", "fuelType": "COAL", "generation": 500},  # Not wind
        {"dataset": "FUELHH", "fuelType": "WIND", "generation": 12500}, # Valid wind
        "invalid row format", # Not a dict
    ]

    async def mock_get(endpoint, params):
        return sample_payload
    client._get_with_retry = mock_get

    wind = await client.fetch_fuelhh_wind("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z")
    assert len(wind) == 1
    assert wind[0]["generation"] == 12500

@pytest.mark.asyncio
async def test_http_429_and_5xx_retries_and_errors():
    """HTTP 429 or 5xx returns ElexonAPIError with status code."""
    attempts = 0
    def handler(request: httpx.Request):
        nonlocal attempts
        attempts += 1
        return httpx.Response(429, text="Rate limit exceeded")

    transport = httpx.MockTransport(handler)
    client = ElexonClient(base_url="https://mock-elexon", max_retries=2)

    # Use transport inside AsyncClient by patching
    original_async_client = httpx.AsyncClient
    try:
        def patched_client(*args, **kwargs):
            return original_async_client(transport=transport)
        httpx.AsyncClient = patched_client

        with pytest.raises(ElexonAPIError) as exc_info:
            await client.fetch_fuelhh_wind("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z")

        assert exc_info.value.status_code == 429
        assert attempts == 2  # Proves retry was attempted up to max_retries
    finally:
        httpx.AsyncClient = original_async_client

@pytest.mark.asyncio
async def test_timeout_error_handling():
    """Timeout produces explicit ElexonAPIError."""
    def handler(request: httpx.Request):
        raise httpx.TimeoutException("Connection timed out")

    transport = httpx.MockTransport(handler)
    client = ElexonClient(base_url="https://mock-elexon", max_retries=1)

    original_async_client = httpx.AsyncClient
    try:
        def patched_client(*args, **kwargs):
            return original_async_client(transport=transport)
        httpx.AsyncClient = patched_client

        with pytest.raises(ElexonAPIError) as exc_info:
            await client.fetch_windfor("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z")

        assert "Timeout connecting to Elexon API" in str(exc_info.value)
    finally:
        httpx.AsyncClient = original_async_client
