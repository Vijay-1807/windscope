import urllib.request
import json
import ssl

ctx = ssl.create_default_context()

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))

# Test 1: Check what parameters stream supports and test date range limits
# Let's test 1 day range for FUELHH stream
print("Testing FUELHH stream for 2026-01-01 full day:")
url_fuel_1day = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?publishDateTimeFrom=2026-01-01T00:00:00Z&publishDateTimeTo=2026-01-02T00:00:00Z"
try:
    data = fetch(url_fuel_1day)
    print(f"FUELHH 1-day stream returned {len(data)} items")
    wind_items = [d for d in data if d.get("fuelType") == "WIND"]
    print(f"WIND items count in 1 day: {len(wind_items)}")
    if wind_items:
        print("Sample WIND item:", wind_items[0])
except Exception as e:
    print(f"FUELHH 1-day error: {e}")

# Test 2: Check WINDFOR stream for vintages
# Let's fetch WINDFOR stream for a 2-day publish window
print("\nTesting WINDFOR stream published between 2025-12-30 and 2026-01-02:")
url_wind_stream = "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-30T00:00:00Z&publishDateTimeTo=2026-01-02T00:00:00Z"
try:
    data = fetch(url_wind_stream)
    print(f"WINDFOR stream returned {len(data)} items")
    # Check distinct target startTimes and their publishTimes
    by_start_time = {}
    for item in data:
        st = item.get("startTime")
        pt = item.get("publishTime")
        gen = item.get("generation")
        if st not in by_start_time:
            by_start_time[st] = []
        by_start_time[st].append((pt, gen))
    
    # Find startTimes that have multiple publishTimes (multiple vintages!)
    multi_vintages = {st: pts for st, pts in by_start_time.items() if len(pts) > 1}
    print(f"Total distinct startTimes: {len(by_start_time)}")
    print(f"Distinct startTimes with >1 vintage in this window: {len(multi_vintages)}")
    if multi_vintages:
        sample_st = list(multi_vintages.keys())[0]
        print(f"Sample target startTime {sample_st} has vintages:")
        for pt, gen in multi_vintages[sample_st]:
            print(f"  publishTime: {pt}, generation: {gen} MW")
except Exception as e:
    print(f"WINDFOR stream error: {e}")

# Test 3: Can we query WINDFOR stream or FUELHH stream with bigger ranges (e.g. 7 days or 31 days)?
print("\nTesting FUELHH stream 7-day range:")
url_fuel_7d = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?publishDateTimeFrom=2026-01-01T00:00:00Z&publishDateTimeTo=2026-01-08T00:00:00Z"
try:
    data = fetch(url_fuel_7d)
    print(f"FUELHH 7-day returned {len(data)} items")
except Exception as e:
    print(f"FUELHH 7-day error: {e}")
