import urllib.request
import json
import ssl
from datetime import datetime, timezone
import zoneinfo

ctx = ssl.create_default_context()
lon_tz = zoneinfo.ZoneInfo("Europe/London")

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))

# Fetch actuals for Jan 1-2
fuel_url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?publishDateTimeFrom=2026-01-01T00:00:00Z&publishDateTimeTo=2026-01-03T00:00:00Z"
fuel_data = fetch(fuel_url)
wind_actuals = [d for d in fuel_data if d.get("fuelType") == "WIND"]
print(f"Total WIND actuals: {len(wind_actuals)}")
print("First 3 actuals:")
for a in wind_actuals[:3]:
    print(" ", a)
print("Last 3 actuals:")
for a in wind_actuals[-3:]:
    print(" ", a)

# Fetch forecasts published between 2025-12-30 and 2026-01-02
wind_url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-30T00:00:00Z&publishDateTimeTo=2026-01-02T00:00:00Z"
wind_data = fetch(wind_url)
print(f"\nTotal WINDFOR records in window: {len(wind_data)}")

# Let's inspect target startTime = 2026-01-01T00:00:00Z or 2026-01-01T12:00:00Z
sample_target = "2026-01-01T12:00:00Z"
target_records = [d for d in wind_data if d.get("startTime") == sample_target]
print(f"\nForecast records for startTime {sample_target}: {len(target_records)}")
for r in target_records:
    print(" ", r)

# Cutoff check: For delivery date 2026-01-01, deadline is 2026-01-01T00:00:00Z
deadline = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
eligible = [r for r in target_records if datetime.fromisoformat(r["publishTime"].replace("Z", "+00:00")) < deadline]
print(f"\nEligible forecasts for {sample_target} (published before {deadline.isoformat()}): {len(eligible)}")
for r in eligible:
    print(" ", r)

if eligible:
    # Latest publishTime
    chosen = max(eligible, key=lambda r: datetime.fromisoformat(r["publishTime"].replace("Z", "+00:00")))
    print(f"\nCHOSEN VINTAGE for {sample_target}:")
    print(" ", chosen)
