# Che168 API with curl

Every Che168 request of the [apiauto.space API](https://apiauto.space/en/docs/) from the command
line. Che168 listings live in `market=cn`. Put the key in a variable first; the demo key comes from
[the Telegram bot](https://t.me/apiautospace_bot?start=demo) (one day, 100 requests).

```bash
export APIAUTO_KEY=your-key
API=https://api.apiauto.space/v1
```

On a shared server other users can read a key from the command line in the process list. Send the
header through stdin there (curl 7.55+):

```bash
printf 'X-API-Key: %s\n' "$APIAUTO_KEY" | curl -s -H @- "$API/usage"
```

Add `| jq` to any command for readable JSON, `-i` to see the quota headers.

## Cars

```bash
# BYD under $20,000, newest listings first
curl -s "$API/cars?market=cn&brand=BYD&price_usd_max=20000&limit=20" \
  -H "X-API-Key: $APIAUTO_KEY"

# Toyota Camry from 2021 with photos, cheapest first, price in yuan
curl -s "$API/cars?market=cn&brand=Toyota&model=Camry&year_min=2021&has_photos=true&sort=price&limit=20" \
  -H "X-API-Key: $APIAUTO_KEY"

# Electric cars under 50,000 km
curl -s "$API/cars?market=cn&fuel=electric&mileage_max=50000&limit=20" \
  -H "X-API-Key: $APIAUTO_KEY"

# Free text: up to 6 words of the title
curl -s "$API/cars?market=cn&q=2024+BYD+Song&limit=20" -H "X-API-Key: $APIAUTO_KEY"

# The next page: pass next_cursor of the previous answer
curl -s "$API/cars?market=cn&brand=BYD&limit=20&cursor=PASTE_NEXT_CURSOR" \
  -H "X-API-Key: $APIAUTO_KEY"
```

Filters: `brand`, `model`, `trim`, `year_min`, `year_max`, `price_min`, `price_max` (yuan),
`price_usd_min`, `price_usd_max`, `mileage_max` (km), `fuel`, `transmission`, `body_type`,
`has_photos`, `is_active`, `q`. Sort: `-first_seen` (default), `first_seen`, `price`, `-price`,
`year`, `-year`, `mileage`, `-mileage`.

## One car

```bash
curl -s "$API/cars/che168:60385167" -H "X-API-Key: $APIAUTO_KEY"
```

A car taken off sale answers with `is_active: false` for 14 more days, then 404. The id in this
example may be gone by the time you read this: take a fresh one from a search.

## Change feed: new cars, removed cars, price changes

```bash
# Everything that happened since a moment
curl -s "$API/changes?market=cn&since=2026-11-02T00:00:00Z&limit=100" -H "X-API-Key: $APIAUTO_KEY"

# Only price drops of 5% or more
curl -s "$API/changes?market=cn&since=2026-11-02T00:00:00Z&type=price_drop&min_pct=5" \
  -H "X-API-Key: $APIAUTO_KEY"
```

Event types: `added`, `disappeared` (left the source, which does not say why), `price_drop`, `price_up`.

## References (free, no quota)

```bash
curl -s "$API/references/brands?market=cn" -H "X-API-Key: $APIAUTO_KEY"
curl -s "$API/references/models?market=cn&brand=BYD" -H "X-API-Key: $APIAUTO_KEY"
curl -s "$API/references/dictionaries" -H "X-API-Key: $APIAUTO_KEY"   # fuel, gearbox, body…
curl -s "$API/references/markets" -H "X-API-Key: $APIAUTO_KEY"        # freshness and counts
curl -s "$API/usage" -H "X-API-Key: $APIAUTO_KEY"                     # your quota
```

## Quota headers

```bash
curl -si "$API/cars?market=cn&limit=1" -H "X-API-Key: $APIAUTO_KEY" | grep -i '^x-'
```

Each answer carries `X-Quota-Limit`, `X-Quota-Remaining`, `X-Quota-Reset`, `X-RateLimit-Limit` and
`X-Data-Age-Seconds`. Errors are JSON: `{"error": "rate_limited", "retry_after": 1}`; the codes are on
[apiauto.space/en/docs/errors/](https://apiauto.space/en/docs/errors/).
