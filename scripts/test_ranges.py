import urllib.request
import json
import ssl
import time

ctx = ssl.create_default_context()

def test_stream_range(dataset, dt_from, dt_to):
    t0 = time.time()
    url = f"https://data.elexon.co.uk/bmrs/api/v1/datasets/{dataset}/stream?publishDateTimeFrom={dt_from}&publishDateTimeTo={dt_to}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - t0
            print(f"[{dataset}] {dt_from} to {dt_to} -> {len(data)} records in {elapsed:.2f}s")
            return data
    except Exception as e:
        print(f"[{dataset}] {dt_from} to {dt_to} FAILED: {e}")
        return None

print("Checking range limits...")
# Check 7 days
test_stream_range("WINDFOR", "2025-12-28T00:00:00Z", "2026-01-04T00:00:00Z")
# Check 14 days
test_stream_range("WINDFOR", "2026-01-01T00:00:00Z", "2026-01-15T00:00:00Z")
# Check 31 days
test_stream_range("WINDFOR", "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z")

# Check FUELHH 31 days
test_stream_range("FUELHH", "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z")
