<?php
// Keep a catalog of Che168 cars in MySQL/PostgreSQL in sync: import once, then poll the change
// feed hourly. Run it from cron: `0 * * * * php sync-catalog.php`. PHP 7.4+ with curl.
//
// The SQL is left as comments: plug in your own database layer. MAX_RECORDS caps the first import.

if (PHP_SAPI !== "cli") {
    exit("Run this example from the command line. Listing data is untrusted: escape it before showing it in HTML.\n");
}

const API = "https://api.apiauto.space/v1";
const STATE_FILE = __DIR__ . "/since.txt";
const MAX_RECORDS = 200;

function apiauto_get(string $path, array $params = []): array
{
    $key = getenv("APIAUTO_KEY");
    if (!$key) {
        throw new RuntimeException("Set the APIAUTO_KEY environment variable");
    }
    for ($attempt = 1; ; $attempt++) {
        $ch = curl_init(API . $path . ($params ? "?" . http_build_query($params) : ""));
        curl_setopt_array($ch, [
            CURLOPT_HTTPHEADER => ["X-API-Key: " . $key],
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HEADER => true,
            CURLOPT_TIMEOUT => 60,
        ]);
        $response = curl_exec($ch);
        $status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        $headerSize = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
        $body = substr($response, $headerSize);

        if (($status === 429 || $status === 503) && $attempt < 5) {
            // Wait as long as the API asks, at most 60 s; 1 s when it does not give a number.
            preg_match('/^retry-after:\s*(\d+)\s*$/mi', substr($response, 0, $headerSize), $m);
            sleep(min((int)($m[1] ?? 1), 60));
            continue;
        }
        if ($status !== 200) {
            throw new RuntimeException("HTTP $status: $body");
        }
        return json_decode($body, true);
    }
}

function next_cursor(array $page, array &$seen): ?string
{
    // Null at the end, on an empty page or a repeated cursor.
    $cursor = $page["next_cursor"] ?? null;
    if (!$page["items"] || !$cursor || isset($seen[$cursor])) {
        return null;
    }
    $seen[$cursor] = true;
    return $cursor;
}

function save_car(array $car): void
{
    // INSERT ... ON CONFLICT (id) DO UPDATE: id, title, price.amount, price.currency, price_usd,
    // mileage_km, photos (refresh them when showing the car: links live about a day), raw.
    echo "save {$car['id']} {$car['title']}\n";
}

if (!file_exists(STATE_FILE)) {
    // The first run: the selection by the cursor.
    $since = gmdate("Y-m-d\TH:i:s\Z");
    $pageSize = 20; // up to 100 on paid plans
    $params = ["market" => "cn", "brand" => "BYD"];
    $saved = 0;
    $seen = [];
    do {
        $params["limit"] = min($pageSize, MAX_RECORDS - $saved);
        $page = apiauto_get("/cars", $params);
        array_map("save_car", $page["items"]);
        $saved += count($page["items"]);
        $params["cursor"] = next_cursor($page, $seen);
    } while ($params["cursor"] && $saved < MAX_RECORDS);
} else {
    // Every next run: only what changed since the last one.
    $since = trim(file_get_contents(STATE_FILE));
    $now = gmdate("Y-m-d\TH:i:s\Z");
    $params = ["market" => "cn", "since" => $since, "limit" => 20]; // up to 100 on paid plans
    $seen = [];
    do {
        $page = apiauto_get("/changes", $params);
        foreach ($page["items"] as $event) {
            switch ($event["type"]) {
                case "added":
                    save_car(apiauto_get("/cars/" . $event["car_id"]));
                    break;
                case "disappeared": // left the source; it does not say why
                    // UPDATE cars SET is_active = false WHERE id = $event["car_id"]
                    echo "gone {$event['car_id']}\n";
                    break;
                default: // price_drop, price_up
                    // UPDATE cars SET price = $event["new_price"] WHERE id = $event["car_id"]
                    echo "{$event['type']} {$event['car_id']}: {$event['old_price']} → {$event['new_price']}\n";
            }
        }
        $params["cursor"] = next_cursor($page, $seen);
    } while ($params["cursor"]);
    $since = $now;
}

file_put_contents(STATE_FILE, $since);
