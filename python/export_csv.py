"""Export a selection of Che168 cars to CSV (opens in Excel and Google Sheets).

    pip install httpx
    export APIAUTO_KEY=...
    python export_csv.py --brand BYD --year-min 2022 --max 100 > byd.csv

Every car exported is one record of quota; --max keeps the export small.
"""

import argparse
import csv
import os
import sys
import time

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--brand")
parser.add_argument("--model")
parser.add_argument("--year-min", type=int)
parser.add_argument("--price-usd-max", type=float)
parser.add_argument("--max", type=int, default=100, help="stop after this many cars")
parser.add_argument("--limit", type=int, default=20, help="cars per page: 20 on the demo, up to 100")
args = parser.parse_args()

api = httpx.Client(
    base_url="https://api.apiauto.space/v1",
    headers={"X-API-Key": os.environ["APIAUTO_KEY"]},
    timeout=60,
)
params = {
    "market": "cn",
    "brand": args.brand,
    "model": args.model,
    "year_min": args.year_min,
    "price_usd_max": args.price_usd_max,
    "limit": args.limit,
}
params = {key: value for key, value in params.items() if value is not None}

columns = [
    "id", "title", "brand", "model", "trim", "year", "mileage_km", "fuel", "transmission",
    "engine_cc", "body_type", "color", "price", "currency", "price_usd", "city",
    "drive", "power_hp", "first_registration", "photo_count", "listing_url", "first_seen_at",
]


def get_page(query: dict) -> dict:
    """GET with up to 5 tries on 429 (rate limit) and 503, waiting Retry-After, at most 60 s."""
    for attempt in range(5):
        response = api.get("/cars", params=query)
        if response.status_code not in (429, 503) or attempt == 4:
            response.raise_for_status()
            return response.json()
        value = response.headers.get("Retry-After", "")
        time.sleep(min(int(value[:9]), 60) if value.isdecimal() else 1)


def safe_cell(value):
    """Listing text comes from strangers: a leading ' stops Excel running it as a formula."""
    if isinstance(value, str) and (value[:1] in ("\t", "\r") or value.lstrip()[:1] in ("=", "+", "-", "@")):
        return "'" + value
    return value


def safe_row(row: dict) -> dict:
    return {name: safe_cell(value) for name, value in row.items()}


writer = csv.DictWriter(sys.stdout, fieldnames=columns, extrasaction="ignore")
writer.writeheader()

seen: set = set()
written = 0
while written < args.max:
    params["limit"] = min(args.limit, args.max - written)  # no quota for cars we would drop
    page = get_page(params)
    for car in page["items"]:
        writer.writerow(safe_row({
            **car,
            "price": car["price"]["amount"],
            "currency": car["price"]["currency"],
            "city": car["location"]["city"],
            "drive": car["raw"].get("drive"),
            "power_hp": car["raw"].get("power_hp"),
            "first_registration": car["raw"].get("first_registration"),
        }))
        written += 1
    cursor = page["next_cursor"]
    if not page["items"] or not cursor or cursor in seen:
        break
    seen.add(cursor)
    params["cursor"] = cursor

print(f"exported {written} cars", file=sys.stderr)
