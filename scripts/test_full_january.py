import urllib.request
import json
import ssl
from datetime import datetime, timezone, timedelta
import zoneinfo

ctx = ssl.create_default_context()
lon_tz = zoneinfo.ZoneInfo("Europe/London")

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("Fetching January 2026 FUELHH actuals...")
fuel_data = fetch("https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?publishDateTimeFrom=2026-01-01T00:00:00Z&publishDateTimeTo=2026-02-01T01:00:00Z")
wind_actuals = [d for d in fuel_data if d.get("fuelType") == "WIND"]
print(f"Total WIND actuals: {len(wind_actuals)}")

print("Fetching WINDFOR forecasts (from 2025-12-25 to 2026-01-31)...")
wind_data = fetch("https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-25T00:00:00Z&publishDateTimeTo=2026-01-31T01:00:00Z")
print(f"Total WINDFOR records: {len(wind_data)}")

# Process actuals: map normalized target startTime -> actual MW
actual_map = {}
for a in wind_actuals:
    st_raw = a.get("startTime")
    gen = a.get("generation")
    if not st_raw or gen is None:
        continue
    # parse ISO
    st_dt = datetime.fromisoformat(st_raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    # Filter to January 2026 target in Europe/London
    st_lon = st_dt.astimezone(lon_tz)
    if st_lon.year == 2026 and st_lon.month == 1:
        st_iso = st_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        actual_map[st_iso] = float(gen)

print(f"Distinct January 2026 actual intervals: {len(actual_map)}")

# Process forecasts: group by target startTime -> list of (publishTime_dt, raw_pt, generation)
forecast_candidates = {}
for f in wind_data:
    st_raw = f.get("startTime")
    pt_raw = f.get("publishTime")
    gen = f.get("generation")
    if not st_raw or not pt_raw or gen is None:
        continue
    st_dt = datetime.fromisoformat(st_raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    st_lon = st_dt.astimezone(lon_tz)
    if not (st_lon.year == 2026 and st_lon.month == 1):
        continue
    
    pt_dt = datetime.fromisoformat(pt_raw.replace("Z", "+00:00")).astimezone(timezone.utc)
    # Delivery date deadline: start of delivery date D in Europe/London
    deadline_local = datetime(st_lon.year, st_lon.month, st_lon.day, 0, 0, 0, tzinfo=lon_tz)
    deadline_utc = deadline_local.astimezone(timezone.utc)

    # Condition: publishTime < deadline
    if pt_dt < deadline_utc:
        st_iso = st_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        if st_iso not in forecast_candidates:
            forecast_candidates[st_iso] = []
        forecast_candidates[st_iso].append((pt_dt, pt_raw, float(gen)))

print(f"Distinct target intervals with eligible forecasts: {len(forecast_candidates)}")

# Select best vintage for each target
best_forecasts = {}
for st_iso, candidates in forecast_candidates.items():
    # Pick candidate with max publishTime. Tie-break: highest generation or stable sort
    best = max(candidates, key=lambda c: (c[0], c[2]))
    best_forecasts[st_iso] = (best[1], best[2])

# Join across all expected intervals in Jan 2026: 31 * 48 = 1488
expected_intervals = 31 * 48
matched = []
missing_actual = 0
missing_forecast = 0

start_dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
for i in range(expected_intervals):
    t = start_dt + timedelta(minutes=30 * i)
    t_iso = t.strftime("%Y-%m-%dT%H:%M:%SZ")
    act = actual_map.get(t_iso)
    fc = best_forecasts.get(t_iso)
    if act is None:
        missing_actual += 1
    if fc is None:
        missing_forecast += 1
    if act is not None and fc is not None:
        f_pt, f_gen = fc
        err = f_gen - act
        abs_err = abs(err)
        matched.append({
            "startTime": t_iso,
            "actualMw": act,
            "forecastMw": f_gen,
            "publishTime": f_pt,
            "errorMw": err,
            "absoluteErrorMw": abs_err
        })

print(f"\nResults for January 2026:")
print(f"Expected intervals: {expected_intervals}")
print(f"Matched intervals: {len(matched)}")
print(f"Missing actuals: {missing_actual}")
print(f"Missing eligible forecasts: {missing_forecast}")
coverage = (len(matched) / expected_intervals) * 100
print(f"Coverage: {coverage:.2f}%")

if matched:
    mae = sum(m["absoluteErrorMw"] for m in matched) / len(matched)
    rmse = (sum(m["errorMw"] ** 2 for m in matched) / len(matched)) ** 0.5
    bias = sum(m["errorMw"] for m in matched) / len(matched)
    mean_actual = sum(m["actualMw"] for m in matched) / len(matched)
    nmae = (mae / mean_actual * 100) if mean_actual > 0 else None
    print(f"MAE: {mae:.2f} MW")
    print(f"RMSE: {rmse:.2f} MW")
    print(f"Bias: {bias:.2f} MW")
    print(f"Mean Actual: {mean_actual:.2f} MW")
    print(f"Normalized MAE: {nmae:.2f}%" if nmae else "Normalized MAE: N/A")
