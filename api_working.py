#!/usr/bin/env python3
"""
Fetch daily (days) aggregated sensor values for CO, O3 and NO2 in India
between 2023-01-01 and 2024-12-31 using OpenAQ v3 endpoints.

Outputs:
 - data.json  -> full list of records (one item per sensor-day)
 - data.csv   -> flattened table (optional, requires pandas)
"""

import os
import time
import requests
import json
from collections import defaultdict

API_BASE = "https://api.openaq.org/v3"
DATE_FROM = "2023-01-01"
DATE_TO = "2024-12-31"
COUNTRY_ISO = "IN"
PARAM_NAMES = ["co"]
OUT_JSON = "data.json"
OUT_CSV = "data.csv"

API_KEY = "cf55cc0533e02e3587cda9046ef19b2088d1b5366b2db28d4eb21cbaa72bc608"  # optional

HEADERS = {}
if API_KEY:
    HEADERS["X-API-Key"] = API_KEY

# helper: safe GET with retries and simple rate-limit handling
def safe_get(url, params=None, max_retries=5):
    for attempt in range(1, max_retries + 1):
        r = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r
        if r.status_code == 429:
            reset = r.headers.get("x-ratelimit-reset")
            # Increase sleep time to 120s or use reset header if available
            sleep_for = 120 if not reset else int(reset) - int(time.time())
            sleep_for = max(10, sleep_for)
            print(f"Rate limited (429). Sleeping {sleep_for}s then retrying...")
            time.sleep(sleep_for)
            continue
        if r.status_code >= 500:
            backoff = 2 ** attempt
            print(f"Server error {r.status_code}. Backing off {backoff}s...")
            time.sleep(backoff)
            continue
        # for 4xx other than 429, print response for debugging then raise
        if r.status_code >= 400:
            print(f"Error {r.status_code} for {url}")
            print("Response text:", r.text)
        r.raise_for_status()
    raise RuntimeError(f"Failed to GET {url} after {max_retries} attempts")

# 1) Get parameter IDs for names (co, o3, no2)
def get_parameter_ids(names):
    print("Fetching parameters list...")
    url = f"{API_BASE}/parameters"
    params = {"limit": 1000}
    r = safe_get(url, params=params)
    data = r.json()
    mapping = {}
    for item in data.get("results", []):
        name = item.get("name")
        if name in names:
            mapping[name] = item.get("id")
    missing = [n for n in names if n not in mapping]
    if missing:
        raise RuntimeError(f"Could not find parameter IDs for: {missing}. Check API response.")
    print("Found parameter IDs:", mapping)
    return mapping

# 2) Get locations in India that measure any of these parameters -> collect sensor ids
def get_sensors_for_parameters(parameter_ids):
    print("Listing locations in India that report the parameters...")
    sensors_set = set()
    # the locations endpoint supports parameters_id (array or comma list)
    params = {
        "iso": COUNTRY_ISO,
        "parameters_id": ",".join(str(v) for v in parameter_ids.values()),
        "limit": 1000,
        "page": 1
    }
    url = f"{API_BASE}/locations"
    while True:
        r = safe_get(url, params=params)
        j = r.json()
        for loc in j.get("results", []):
            # Filter sensors by parameter
            for s in loc.get("sensors", []):
                # Only add sensor if it measures one of the requested parameters
                param_id = s.get("parameter_id") or s.get("parameter", {}).get("id")
                if param_id and param_id in parameter_ids.values():
                    sensors_set.add(int(s["id"]))
        meta = j.get("meta", {})
        found = meta.get("found", 0)
        per_page = meta.get("limit", params["limit"])
        current_page = meta.get("page", params["page"])
        # pagination check:
        if (current_page * per_page) >= found:
            break
        params["page"] = current_page + 1
    print(f"Found {len(sensors_set)} unique sensors in India for parameters {list(parameter_ids.keys())}")
    return sorted(sensors_set)

# 3) For each sensor id, call /v3/sensors/{id}/days with date_from/date_to, paginate and collect
def fetch_sensor_days(sensor_ids):
    all_records = []
    for i, sid in enumerate(sensor_ids, start=1):
        if i > 10:
            break
        print(f"[{i}/{len(sensor_ids)}] Fetching sensor {sid} daily aggregations...")
        url = f"{API_BASE}/sensors/{sid}/days"
        params = {
            "date_from": DATE_FROM,
            "date_to": DATE_TO,
            "limit": 1000,
            "page": 1
        }
        try:
            while True:
                r = safe_get(url, params=params)
                j = r.json()
                for rec in j.get("results", []):
                    # add sensor id to each record for traceability
                    rec["_sensor_id"] = sid
                    all_records.append(rec)
                meta = j.get("meta", {})
                found = meta.get("found", 0)
                per_page = meta.get("limit", params["limit"])
                current_page = meta.get("page", params["page"])
                if (current_page * per_page) >= found:
                    break
                params["page"] = current_page + 1
                # polite sleep to avoid bursts
                time.sleep(0.1)
        except Exception as e:
            print(f"Skipping sensor {sid} due to error: {e}")
        # small pause per sensor to be polite with rate-limits
        time.sleep(0.1)
    print(f"Total sensor-day records collected: {len(all_records)}")
    return all_records

def main():
    param_map = get_parameter_ids(PARAM_NAMES)
    sensors = get_sensors_for_parameters(param_map)
    if not sensors:
        print("No sensors found. Exiting.")
        return
    records = fetch_sensor_days(sensors)
    # save JSON
    with open(OUT_JSON, "w", encoding="utf8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(records)} records to {OUT_JSON}")
    # optional: save CSV if pandas available
    try:
        import pandas as pd
        df = pd.json_normalize(records)
        df.to_csv(OUT_CSV, index=False)
        print(f"Saved flat CSV to {OUT_CSV}")
    except Exception:
        print("pandas not available or CSV save failed; JSON is available.")

if __name__ == "_main_":
    main()
