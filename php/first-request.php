<?php
// Search Che168 (China) and print the cars. PHP 7.4+ with the curl extension.
//
//   export APIAUTO_KEY=...   # the demo key from https://t.me/apiautospace_bot?start=demo
//   php first-request.php

if (PHP_SAPI !== "cli") {
    exit("Run this example from the command line. Listing data is untrusted: escape it before showing it in HTML.\n");
}

function apiauto_get(string $path, array $params = []): array
{
    $key = getenv("APIAUTO_KEY");
    if (!$key) {
        throw new RuntimeException("Set the APIAUTO_KEY environment variable");
    }
    $url = "https://api.apiauto.space/v1" . $path . ($params ? "?" . http_build_query($params) : "");
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_HTTPHEADER => ["X-API-Key: " . $key],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
    ]);
    $body = curl_exec($ch);
    $status = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    if ($status !== 200) {
        // Errors are JSON too: {"error": "quota_exhausted", "reset_at": "..."}
        throw new RuntimeException("HTTP $status: $body");
    }
    return json_decode($body, true);
}

$page = apiauto_get("/cars", [
    "market" => "cn",          // cn = Che168
    "brand" => "BYD",
    "year_min" => 2021,
    "price_usd_max" => 20000,  // dollars at the ECB daily rate; price_max takes yuan
    "limit" => 20,             // up to 20 on the demo key, up to 100 on paid plans
]);

printf("%s cars match\n", $page["count"] ?? "10,000+");
foreach ($page["items"] as $car) {
    printf(
        "%-18s %-40s %7s km  %s %s (≈ $%s)  %s\n",
        $car["id"],
        $car["title"],
        $car["mileage_km"] ?? "?",
        $car["price"]["amount"],
        $car["price"]["currency"],
        $car["price_usd"],
        $car["location"]["city"]
    );
}
