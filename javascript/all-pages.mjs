// Walk every page of a Che168 selection with the cursor, as an async generator.
//
//   export APIAUTO_KEY=...
//   node all-pages.mjs
//
// Every car returned is one record of quota, so stop when you have enough.

if (!process.env.APIAUTO_KEY) throw new Error("Set the APIAUTO_KEY environment variable");

const BASE = "https://api.apiauto.space/v1";
const PAGE_SIZE = 20; // up to 20 on the demo key, up to 100 on paid plans

async function* cars(filters, { maxItems = Infinity } = {}) {
  const params = new URLSearchParams({ market: "cn", ...filters });
  let yielded = 0;
  let tries = 0;
  const seen = new Set();
  while (yielded < maxItems) {
    // Ask for no more than is still wanted: the quota counts every car returned.
    params.set("limit", String(Math.min(PAGE_SIZE, maxItems - yielded)));
    const response = await fetch(`${BASE}/cars?${params}`, {
      headers: { "X-API-Key": process.env.APIAUTO_KEY },
      redirect: "error", // the key must not follow a redirect to another host
      signal: AbortSignal.timeout(30000),
    });
    if ((response.status === 429 || response.status === 503) && ++tries < 5) {
      // Wait as long as the API asks, at most 60 s; 1 s when it does not give a number.
      const value = response.headers.get("Retry-After") ?? "";
      const seconds = /^\d+$/.test(value) ? Math.min(Number(value), 60) : 1;
      await new Promise((resolve) => setTimeout(resolve, seconds * 1000));
      continue;
    }
    if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
    tries = 0;

    const page = await response.json();
    for (const car of page.items) {
      yielded++;
      yield car;
    }
    if (page.items.length === 0 || !page.next_cursor || seen.has(page.next_cursor)) return;
    seen.add(page.next_cursor);
    params.set("cursor", page.next_cursor);
  }
}

// Electric BYDs from 2022 with under 60,000 km, the first 30 of them.
for await (const car of cars(
  { brand: "BYD", fuel: "electric", year_min: "2022", mileage_max: "60000" },
  { maxItems: 30 },
)) {
  console.log(car.id, car.title, car.mileage_km, car.price_usd);
}
