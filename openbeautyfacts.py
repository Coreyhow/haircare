"""Load hair products from Open Beauty Facts (free, open data) into haircare.db.

Usage: python openbeautyfacts.py [shampoo conditioner hair-mask hair-oil]  (default: all)
Data: https://world.openbeautyfacts.org  (Open Database License)
"""
import sys
import time

try:  # Use the OS certificate store (needed on networks that inspect HTTPS)
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import requests

import db
from scraper import split_ingredients

API = "https://world.openbeautyfacts.org/api/v2/search"
PRODUCT_URL = "https://world.openbeautyfacts.org/product/{code}"
CATEGORIES = {
    "shampoo": ["en:shampoos"],
    "conditioner": ["en:hair-conditioners", "en:conditioners"],
    "hair-mask": ["en:hair-masks"],
    "hair-oil": ["en:hair-oils"],
}
FIELDS = "code,lang,product_name,product_name_en,brands,ingredients_text_en,ingredients_text"
PAGE_SIZE = 100
DELAY_SECONDS = 1.0

session = requests.Session()
session.headers["User-Agent"] = "haircare-personal-project/1.0"


# Extra searches per English-speaking country: the API stops at ~1,000 results per
# query, so these reach English products the global search can't.
COUNTRIES = [None, "en:united-states", "en:united-kingdom", "en:canada", "en:australia"]


def fetch_page(tag, page, country=None):
    params = {"categories_tags": tag, "fields": FIELDS, "page_size": PAGE_SIZE, "page": page}
    if country:
        params["countries_tags"] = country
    resp = session.get(API, params=params, timeout=30)
    resp.raise_for_status()
    time.sleep(DELAY_SECONDS)
    return resp.json()


def english_name(p):
    """English product name, or None if the product isn't listed in English."""
    if p.get("product_name_en"):
        return p["product_name_en"]
    if p.get("lang") == "en":
        return p.get("product_name")
    return None


def load_category(conn, category):
    saved = skipped = 0
    seen = set()
    queries = [(tag, country) for tag in CATEGORIES[category] for country in COUNTRIES]
    for tag, country in queries:
        page = 1
        while True:
            try:
                data = fetch_page(tag, page, country)
            except requests.RequestException as e:
                print(f"  [{category}] page {page} failed: {e}")
                break
            products = data.get("products", [])
            if not products:
                break
            for p in products:
                if p.get("code") in seen:
                    continue
                seen.add(p.get("code"))
                text = p.get("ingredients_text_en") or p.get("ingredients_text")
                name = english_name(p)
                ingredients = split_ingredients(text) if text else []
                if not name or not p.get("code") or len(ingredients) < 3:
                    skipped += 1
                    continue
                db.save_product(conn, name.strip(), (p.get("brands") or "").split(",")[0].strip(),
                                category, PRODUCT_URL.format(code=p["code"]), ingredients)
                saved += 1
            print(f"  [{category}] {tag} {country or 'all'} page {page}: total saved {saved}")
            if page * PAGE_SIZE >= data.get("count", 0):
                break
            page += 1
    print(f"[{category}] saved {saved}, skipped {skipped} (not English, or no ingredient list)")


def main(argv):
    categories = argv or list(CATEGORIES)
    unknown = [c for c in categories if c not in CATEGORIES]
    if unknown:
        sys.exit(f"Unknown category: {', '.join(unknown)}. Choose from {list(CATEGORIES)}")
    conn = db.connect()
    try:
        for c in categories:
            load_category(conn, c)
    finally:
        conn.close()


if __name__ == "__main__":
    main(sys.argv[1:])
