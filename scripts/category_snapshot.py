from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


PACIFIC = ZoneInfo("America/Los_Angeles")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
)

WHOLE_FOODS_CATEGORY_URLS = {
    "coffee": "https://www.wholefoodsmarket.com/products/beverages/coffee",
}

WHOLE_FOODS_CARD_RE = re.compile(
    r'<div id="gridElement-(?P<asin>[^"]+)".*?'
    r'<img alt="(?P<name>[^"]+)" src="(?P<image>[^"]+)".*?'
    r'<a class="a-link-normal" href="(?P<href>/[^"]+?fpw=alm[^"]+)"',
    re.S,
)

SIZE_PATTERNS = [
    re.compile(
        r"(?P<size>\d+(?:\.\d+)?\s?(?:oz|OZ|lb|LB|ct|CT|count|ml|ML|g|kg|FZ|fl oz|pack))\b"
    ),
    re.compile(r",\s*(?P<size>[^,]+)$"),
]

BRAND_STOP_WORDS = {
    "blend",
    "bold",
    "brew",
    "coffee",
    "cold",
    "dark",
    "decaf",
    "espresso",
    "french",
    "ground",
    "house",
    "iced",
    "instant",
    "italian",
    "light",
    "medium",
    "organic",
    "pods",
    "protein",
    "ready",
    "roast",
    "single-serve",
    "whole",
}


@dataclass
class SnapshotProduct:
    retailer: str
    category: str
    asin: str
    name: str
    brand_guess: str | None
    size_guess: str | None
    product_url: str
    image_url: str
    public_stock_status: str | None
    public_stock_status_exposed: bool
    notes: str | None


def now_pacific() -> datetime:
    return datetime.now(tz=PACIFIC)


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_size(name: str) -> str | None:
    for pattern in SIZE_PATTERNS:
        match = pattern.search(name)
        if match:
            size = match.group("size").strip()
            if size and len(size) <= 40:
                return size
    return None


def extract_brand_guess(name: str) -> str | None:
    headline = name.split(",")[0].strip()
    words = headline.split()
    if not words:
        return None

    brand_words: list[str] = []
    for word in words:
        normalized = word.lower().strip("&").strip("-")
        if brand_words and normalized in BRAND_STOP_WORDS:
            break
        brand_words.append(word)
        if len(brand_words) >= 3:
            break

    guess = " ".join(brand_words).strip()
    return guess or None


def parse_whole_foods_products(html_text: str, category: str) -> list[SnapshotProduct]:
    products: list[SnapshotProduct] = []
    seen_asins: set[str] = set()

    for match in WHOLE_FOODS_CARD_RE.finditer(html_text):
        asin = match.group("asin").strip()
        if asin in seen_asins:
            continue

        name = html.unescape(match.group("name")).strip()
        href = html.unescape(match.group("href")).strip()
        image_url = html.unescape(match.group("image")).strip()

        seen_asins.add(asin)
        products.append(
            SnapshotProduct(
                retailer="wholefoods",
                category=category,
                asin=asin,
                name=name,
                brand_guess=extract_brand_guess(name),
                size_guess=extract_size(name),
                product_url=urljoin("https://www.wholefoodsmarket.com", href),
                image_url=image_url,
                public_stock_status=None,
                public_stock_status_exposed=False,
                notes=(
                    "Category page exposes catalog cards publicly, but not a clean anonymous "
                    "stock signal on this route."
                ),
            )
        )

    return products


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, products: list[SnapshotProduct]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(products[0]).keys()) if products else [])
        if products:
            writer.writeheader()
            for product in products:
                writer.writerow(asdict(product))


def capture_once(category: str, snapshot_dir: Path, public_json: Path | None) -> dict[str, object]:
    if category not in WHOLE_FOODS_CATEGORY_URLS:
        raise ValueError(f"Unsupported category '{category}'. Supported categories: {sorted(WHOLE_FOODS_CATEGORY_URLS)}")

    source_url = WHOLE_FOODS_CATEGORY_URLS[category]
    captured_at = now_pacific().isoformat()
    html_text = fetch_html(source_url)
    products = parse_whole_foods_products(html_text, category)

    snapshot = {
        "captured_at": captured_at,
        "timezone": "America/Los_Angeles",
        "retailer": "wholefoods",
        "category": category,
        "source_url": source_url,
        "product_count": len(products),
        "public_stock_signal_available": False,
        "notes": [
            "This prototype captures a public coffee category page from Whole Foods Market.",
            "Product names, URLs, images, and size guesses are available anonymously.",
            "Exact stock availability is not exposed cleanly on this anonymous category route.",
            "You cannot reconstruct the previous 24 hours from public HTML alone; you must start collecting now.",
        ],
        "products": [asdict(product) for product in products],
    }

    timestamp_slug = now_pacific().strftime("%Y%m%d-%H%M%S")
    retailer_dir = snapshot_dir / "wholefoods" / category
    write_json(retailer_dir / f"{timestamp_slug}.json", snapshot)
    write_json(retailer_dir / "latest.json", snapshot)

    if products:
        write_csv(retailer_dir / "latest.csv", products)

    if public_json is not None:
        write_json(public_json, snapshot)

    return snapshot


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture repeated category snapshots from public retailer pages."
    )
    parser.add_argument("--category", default="coffee", help="Category slug to capture.")
    parser.add_argument(
        "--snapshot-dir",
        default=".context/category_snapshots",
        help="Directory for raw snapshot files.",
    )
    parser.add_argument(
        "--public-json",
        default="frontend/public/data/wholefoods-coffee-latest.json",
        help="Optional public JSON path for the latest snapshot.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=0,
        help="If greater than zero, keep capturing at this interval.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="How many snapshots to capture. Use 0 for unbounded when interval is set.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    snapshot_dir = Path(args.snapshot_dir)
    public_json = Path(args.public_json) if args.public_json else None

    run_count = 0
    while True:
        run_count += 1
        try:
            snapshot = capture_once(args.category, snapshot_dir, public_json)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            print(f"snapshot_error: {exc}", file=sys.stderr)
            return 1

        print(
            json.dumps(
                {
                    "captured_at": snapshot["captured_at"],
                    "retailer": snapshot["retailer"],
                    "category": snapshot["category"],
                    "product_count": snapshot["product_count"],
                    "public_stock_signal_available": snapshot["public_stock_signal_available"],
                }
            )
        )

        if args.interval_seconds <= 0:
            return 0

        if args.iterations > 0 and run_count >= args.iterations:
            return 0

        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
