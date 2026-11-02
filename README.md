# Che168 API examples

Working curl, Python, JavaScript and PHP examples for reading used-car listings from **Che168** (China,
part of Autohome) as JSON through [apiauto.space](https://apiauto.space/en/che168-api/), a read-only REST API.

Che168 has no public API for its listings that we could find: on 2026-11-02 neither Che168 nor Autohome
published documentation for one. apiauto.space is an independent service, not a Che168 product.

The API is paid from $59 a month for 100,000 cars. A free demo key works for 1 day: 100 requests, up to 20
cars per request, no card. It comes from the Telegram bot
[@apiautospace_bot](https://t.me/apiautospace_bot?start=demo).

```bash
curl -s "https://api.apiauto.space/v1/cars/che168:60385167" -H "X-API-Key: $APIAUTO_KEY"
```

A real answer, shortened; the full one is in [che168-car.json](https://github.com/apiauto-space/che168-api-examples/blob/main/samples/che168-car.json):

```json
{
  "id": "che168:60385167",
  "market": "cn",
  "source": "che168",
  "title": "2025 BYD Song Pro New Energy",
  "brand": "BYD",
  "model": "Song Pro",
  "year": 2025,
  "mileage_km": 10000,
  "fuel": "plug_in_hybrid",
  "vin": null,
  "price": {
    "amount": "79000.00",
    "currency": "CNY"
  },
  "price_usd": "11874.55",
  "location": {
    "country": "CN",
    "region": null,
    "city": "Meizhou"
  },
  "photo_count": 24,
  "listing_url": "https://www.che168.com/dealer/559088/60385167.html",
  "is_active": true,
  "raw": {
    "drive": "fwd",
    "power_hp": 101,
    "first_registration": "2025-09-19"
  }
}
```

Last verified: 2026-11-02, every example below run against the live API.

## Quick start

1. Get the demo key in [the bot](https://t.me/apiautospace_bot?start=demo) and save it:
   `export APIAUTO_KEY=your-key`.
2. Search. Che168 listings live in `market=cn`:

```bash
curl -s "https://api.apiauto.space/v1/cars?market=cn&brand=BYD&price_usd_max=20000&limit=20" \
  -H "X-API-Key: $APIAUTO_KEY"
```

Call the API from your server: CORS is off, because a key in browser code is visible to everyone. Every
request is in [curl/README.md](https://github.com/apiauto-space/che168-api-examples/blob/main/curl/README.md).

| Task | Python | JavaScript | PHP |
|---|---|---|---|
| Search by make, year, price | [first_request.py](https://github.com/apiauto-space/che168-api-examples/blob/main/python/first_request.py) | [first-request.mjs](https://github.com/apiauto-space/che168-api-examples/blob/main/javascript/first-request.mjs) | [first-request.php](https://github.com/apiauto-space/che168-api-examples/blob/main/php/first-request.php) |
| Every page by the cursor | [sync_catalog.py](https://github.com/apiauto-space/che168-api-examples/blob/main/python/sync_catalog.py) | [all-pages.mjs](https://github.com/apiauto-space/che168-api-examples/blob/main/javascript/all-pages.mjs) | [sync-catalog.php](https://github.com/apiauto-space/che168-api-examples/blob/main/php/sync-catalog.php) |
| Price drops of 5% or more | [price_drops.py](https://github.com/apiauto-space/che168-api-examples/blob/main/python/price_drops.py) | [price-drops.mjs](https://github.com/apiauto-space/che168-api-examples/blob/main/javascript/price-drops.mjs) | |
| Export to CSV | [export_csv.py](https://github.com/apiauto-space/che168-api-examples/blob/main/python/export_csv.py) | | |
| Download photos | [download_photos.py](https://github.com/apiauto-space/che168-api-examples/blob/main/python/download_photos.py) | | |

Real answers, shortened, with photo signatures removed: [a page](https://github.com/apiauto-space/che168-api-examples/blob/main/samples/cars-page-cn.json),
[change feed](https://github.com/apiauto-space/che168-api-examples/blob/main/samples/changes-page-cn.json), [price drops](https://github.com/apiauto-space/che168-api-examples/blob/main/samples/price-drops-cn.json),
[makes](https://github.com/apiauto-space/che168-api-examples/blob/main/samples/brands-cn.json), [BYD models](https://github.com/apiauto-space/che168-api-examples/blob/main/samples/models-cn-byd.json).

## Fields

| Field | Meaning |
|---|---|
| `id` | `che168:<listing>`, stable |
| `brand`, `model` | Latin script, one spelling; the source's own in `raw.source_values` |
| `trim` | Che168's full name of the version |
| `year`, `mileage_km`, `engine_cc` | numbers |
| `fuel`, `transmission`, `body_type`, `color` | canonical values, list in `/v1/references/dictionaries` |
| `price`, `price_usd` | price in CNY, and in dollars at the ECB daily rate |
| `location` | `city` from the source; `region` is often `null` |
| `photos`, `photo_count` | signed links, valid about a day: keep the id, not the link |
| `listing_url` | the listing on Che168 |
| `is_active`, `first_seen_at`, `disappeared_at` | status of the listing |
| `raw` | source-only fields: `drive`, `power_hp`, `power_kw`, `first_registration`, `dealer_id` |

Full schema: [openapi.json](https://api.apiauto.space/openapi.json), [the record](https://apiauto.space/en/docs/record/).

## Units and gotchas

- **Prices are full yuan.** Che168 shows prices in 万元 (10,000 yuan); `price.amount` is `79000.00`, not `7.9`.
- **Mileage is kilometres**, not 万公里, and often rounded by the seller.
- **`vin` is always `null`:** Che168 listings do not publish VINs.
- **A price is an asking price,** not what a car sold for.
- **`disappeared` is not "sold".** A car that leaves Che168 gets `is_active: false` for 14 days and a
  `disappeared` event; the source does not say why it left.
- Photos may answer with a redirect to `autoimg.cn`, and may be WebP. Listing text is untrusted input:
  escape it in HTML and in spreadsheets.

## Data freshness

The refresh target is hourly. That is a target, not a promise: the real age is in the
`X-Data-Age-Seconds` header of every answer and in `GET /v1/references/markets`. When we read it on 2026-11-02, the Che168 copy was
33 min old, and the API marks it stale after 3 h 0 min.

## Limits

Up to 100 cars per request (20 on the demo). Pagination is cursor-only. Paid plans count cars returned, not
requests; the demo counts data requests. References, usage and photos are free. Over the rate limit the API
answers 429 with `Retry-After`. Details: [limits](https://apiauto.space/en/docs/limits/).

## Pricing

| Plan | Price | Cars a month | Markets | Requests a second | Change feed |
|---|---|---|---|---|---|
| Demo | free, 1 day, no card | 100 requests | all 3 | — | yes |
| Start | $59 a month | 100,000 | 1 | 2 | no |
| Pro | $149 a month | 500,000 | 2 | 5 | yes |
| Max | $299 a month | 2,000,000 | 3 | 10 | yes |

`cn` is one market. Current prices and Enterprise terms: [apiauto.space/en/#pricing](https://apiauto.space/en/#pricing).

## Other languages

| Language | Package | Repository |
|---|---|---|
| Python | `pip install apiauto-space` | [apiauto-python](https://github.com/apiauto-space/apiauto-python) |
| JavaScript / TypeScript | `npm i apiauto` | [apiauto-js](https://github.com/apiauto-space/apiauto-js) |
| PHP | `composer require apiauto/apiauto` | [apiauto-php](https://github.com/apiauto-space/apiauto-php) |
| Go | `go get github.com/apiauto-space/apiauto-go` | [apiauto-go](https://github.com/apiauto-space/apiauto-go) |

## Not affiliated

apiauto.space is not affiliated with, endorsed by or sponsored by Che168 or Autohome; the names only say where
the listings come from. Listing data and photos belong to the source and the sellers. The examples are
[MIT-licensed](https://github.com/apiauto-space/che168-api-examples/blob/main/LICENSE).
