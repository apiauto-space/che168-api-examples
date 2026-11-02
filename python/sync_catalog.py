"""Keep a local copy of Che168 listings in SQLite: one import, then change-feed polls.

    pip install httpx
    export APIAUTO_KEY=...
    python sync_catalog.py --brand BYD --limit 20 --max-records 200   # fits the demo key
    python sync_catalog.py --brand BYD --once                         # one pass, for cron

The first run imports the selection; every next one applies what changed since the last.
The change feed (/v1/changes) comes with Pro, Max and the demo key.
"""

import argparse
import json
import os
import sqlite3
import time
from datetime import datetime, timezone

import httpx

api = httpx.Client(
    base_url="https://api.apiauto.space/v1",
    headers={"X-API-Key": os.environ["APIAUTO_KEY"]},
    timeout=60,
)
db = sqlite3.connect("cars.db")
db.execute(
    """create table if not exists cars (
        id text primary key, title text, price text, price_usd text, is_active integer, record text
    )"""
)
db.execute("create table if not exists sync (market text primary key, since text)")


def get(path: str, params: dict | None = None) -> dict:
    """GET with up to 5 tries on 429 (rate limit) and 503, waiting Retry-After, at most 60 s."""
    for attempt in range(5):
        response = api.get(path, params=params)
        if response.status_code not in (429, 503) or attempt == 4:
            response.raise_for_status()
            return response.json()
        value = response.headers.get("Retry-After", "")
        time.sleep(min(int(value[:9]), 60) if value.isdecimal() else 1)


def next_page(page: dict, params: dict, seen: set) -> bool:
    """Move params to the next page; False at the end, on an empty page or a repeated cursor."""
    cursor = page["next_cursor"]
    if not page["items"] or not cursor or cursor in seen:
        return False
    seen.add(cursor)
    params["cursor"] = cursor
    return True


def save(car: dict) -> None:
    db.execute(
        "insert or replace into cars values (?, ?, ?, ?, ?, ?)",
        (
            car["id"], car["title"], car["price"]["amount"], car["price_usd"],
            int(car["is_active"]), json.dumps(car, ensure_ascii=False),
        ),
    )


def import_cars(filters: dict, limit: int, max_records: int | None) -> None:
    """The first import: every page by the cursor. Each car returned is one record of quota."""
    params = {"market": "cn", "limit": limit, **filters}
    total = 0
    seen: set = set()
    while max_records is None or total < max_records:
        if max_records is not None:
            params["limit"] = min(limit, max_records - total)
        page = get("/cars", params)
        for car in page["items"]:
            save(car)
        total += len(page["items"])
        db.commit()
        print(f"imported {total}")
        if not next_page(page, params, seen):
            return


def follow_changes(since: str, filters: dict, limit: int) -> str:
    """Apply every event since the last poll; returns the moment to ask from next time.
    The feed covers the whole market, so new cars are checked against our filters."""
    now = datetime.now(timezone.utc).isoformat()
    params = {"market": "cn", "since": since, "limit": limit}
    seen: set = set()
    while True:
        page = get("/changes", params)
        for event in page["items"]:
            if event["type"] == "added":
                car = get(f"/cars/{event['car_id']}")
                if filters.get("brand") in (None, car["brand"]):
                    save(car)
            elif event["type"] == "disappeared":      # left the source; it does not say why
                db.execute("update cars set is_active = 0 where id = ?", (event["car_id"],))
            else:                                     # price_drop, price_up
                db.execute(
                    "update cars set price = ? where id = ?",
                    (event["new_price"], event["car_id"]),
                )
        db.commit()
        print(f"{len(page['items'])} events")
        if not next_page(page, params, seen):
            return now


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--brand")
    parser.add_argument("--limit", type=int, default=100, help="20 on the demo key")
    parser.add_argument("--max-records", type=int, help="stop the first import after this many cars")
    parser.add_argument("--once", action="store_true", help="one pass and exit, for cron")
    args = parser.parse_args()
    filters = {"brand": args.brand} if args.brand else {}

    row = db.execute("select since from sync where market = 'cn'").fetchone()
    if row is None:
        since = datetime.now(timezone.utc).isoformat()
        import_cars(filters, args.limit, args.max_records)
    else:
        since = follow_changes(row[0], filters, args.limit)

    while True:
        db.execute("insert or replace into sync values ('cn', ?)", (since,))
        db.commit()
        if args.once:
            break
        time.sleep(3600)  # the market copy is refreshed hourly; polling more often brings nothing
        since = follow_changes(since, filters, args.limit)
