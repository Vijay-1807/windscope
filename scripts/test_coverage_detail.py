import json
from datetime import datetime, timezone
import zoneinfo

lon_tz = zoneinfo.ZoneInfo("Europe/London")

# Let's inspect the dates and publish times in WINDFOR
import urllib.request, ssl
ctx = ssl.create_default_context()
req = urllib.request.Request(
    "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-25T00:00:00Z&publishDateTimeTo=2026-02-05T00:00:00Z",
    headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
)
with urllib.request.urlopen(req, timeout=45, context=ctx) as resp:
    wind_data = json.loads(resp.read().decode("utf-8"))

print(f"Total WINDFOR records fetched: {len(wind_data)}")

# Let's see publishTime min and max, and target startTime min and max
pts = [datetime.fromisoformat(r["publishTime"].replace("Z", "+00:00")) for r in wind_data if "publishTime" in r]
sts = [datetime.fromisoformat(r["startTime"].replace("Z", "+00:00")) for r in wind_data if "startTime" in r]

print(f"publishTime range: {min(pts)} to {max(pts)}")
print(f"startTime range: {min(sts)} to {max(sts)}")

# For each day in Jan 2026, count how many targets have an eligible forecast (publishTime < start of delivery date)
daily_eligible = {}
for r in wind_data:
    st_raw = r.get("startTime")
    pt_raw = r.get("publishTime")
    if not st_raw or not pt_raw:
        continue
    st_dt = datetime.fromisoformat(st_raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    st_lon = st_dt.astimezone(lon_tz)
    if not (st_lon.year == 2026 and st_lon.month == 1):
        continue
    
    pt_dt = datetime.fromisoformat(pt_raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    deadline_local = datetime(st_lon.year, st_lon.month, st_lon.day, 0, 0, 0, tzinfo=lon_tz)
    deadline_utc = deadline_local.astimezone(timezone.utc)
    
    day_str = st_lon.strftime("%Y-%m-%d")
    if day_str not in daily_eligible:
        daily_eligible[day_str] = set()
    
    if pt_dt < deadline_utc:
        daily_eligible[day_str].add(st_dt.isoformat())

print("\nEligible intervals per day in January 2026:")
for day in sorted(daily_eligible.keys()):
    print(f"  {day}: {len(daily_eligible[day])} / 48 intervals")

# Also check which days had ANY forecasts published (even ineligible)
daily_any = {}
for r in wind_data:
    st_raw = r.get("startTime")
    if not st_raw:
        continue
    st_dt = datetime.fromisoformat(st_raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    st_lon = st_dt.astimezone(lon_tz)
    if not (st_lon.year == 2026 and st_lon.month == 1):
        continue
    day_str = st_lon.strftime("%Y-%m-%d")
    if day_str not in daily_any:
        daily_any[day_str] = set()
    daily_any[day_str].add(st_dt.isoformat())

print("\nTotal target intervals that appear in WINDFOR at all:")
for day in sorted(daily_any.keys()):
    if len(daily_eligible.get(day, set())) < 48:
        print(f"  {day}: total targets in dataset = {len(daily_any[day])}, eligible = {len(daily_eligible.get(day, set()))}")
