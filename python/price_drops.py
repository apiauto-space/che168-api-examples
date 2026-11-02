"""Che168 cars whose price dropped by 5% or more in the last 24 hours, with the car record.

    pip install httpx
    export APIAUTO_KEY=...
    python price_drops.py

The change feed (/v1/changes) comes with Pro, Max and the demo key.
"""

import os
from datetime import datetime, timedelta, timezone

import httpx

api = httpx.Client(
    base_url="https://api.apiauto.space/v1",
    headers={"X-API-Key": os.environ["APIAUTO_KEY"]},
    timeout=30,
)

since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
events = api.get(
    "/changes",
    params={"market": "cn", "since": since, "type": "price_drop", "min_pct": 5, "limit": 5},
).raise_for_status().json()["items"]

if not events:
    print("No price drops of 5% or more in the last 24 hours")

for event in events:
    car = api.get(f"/cars/{event['car_id']}").raise_for_status().json()
    print(
        f"-{float(event['pct']):.1f}%  {car['title']}: "
        f"{event['old_price']} → {event['new_price']} CNY  {car['listing_url'] or car['id']}"
    )
