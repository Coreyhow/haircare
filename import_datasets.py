"""Import hair products from downloaded Kaggle datasets into haircare.db.

Usage: python import_datasets.py
Expects these files in data/ (download from Kaggle, see README):
  - product_info.csv                  "Sephora Products and Skincare Reviews" by nadyinky (CC BY 4.0)
  - E-commerce  cosmetic dataset.csv  "E-commerce Cosmetic Products" by devi5723 (MIT)
Missing files are skipped.
"""
import ast
import csv
import os
import re

import db
from scraper import split_ingredients

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SEPHORA_FILE = os.path.join(DATA, "product_info.csv")
ECOMMERCE_FILE = os.path.join(DATA, "E-commerce  cosmetic dataset.csv")

# Sephora tertiary_category -> our category (anything else is skipped: tools, sets, supplements...)
SEPHORA_CATEGORIES = {
    "Shampoo": "shampoo",
    "Conditioner": "conditioner",
    "Leave-In Conditioner": "leave-in",
    "Hair Primers": "leave-in",
    "Hair Masks": "hair-mask",
    "Hair Oil": "hair-oil",
    "Scalp Treatments": "scalp-treatment",
    "Hair Styling Products": "styling",
    "Hair Spray": "styling",
}
# E-commerce subcategory -> our category
ECOMMERCE_CATEGORIES = {
    "shampoo": "shampoo",
    "conditioner": "conditioner",
    "hairmask": "hair-mask",
    "oil": "hair-oil",
    "serum": "leave-in",
    "hairstyling": "styling",
}
ECOMMERCE_STORES = {"ulta": "Ulta", "sephora": "Sephora"}

# Text that retailers append after the real ingredient list
BOILERPLATE = re.compile(
    r"please be aware|ingredient lists? (may|are subject)|may change|refer to the product packaging"
    r"|for the most (complete and )?up.to.date|clean at sephora",
    re.IGNORECASE,
)
MIN_INGREDIENTS = 3


def clean_ingredient_text(text):
    """Cut off retailer disclaimers and drop sentence-like fragments."""
    match = BOILERPLATE.search(text)
    if match:
        text = text[:match.start()]
    ingredients = split_ingredients(text)
    # Real ingredient names are short; long phrases are marketing copy that slipped in
    return [i for i in ingredients if len(i.split()) <= 8 and not i.endswith(":")]


def sephora_ingredient_text(raw):
    """The Sephora column is a Python-style list that can hold several variations
    (e.g. ['Shampoo:', 'Water, ...', 'Conditioner:', 'Water, ...']). Use the longest list."""
    try:
        parts = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        parts = [raw]
    if isinstance(parts, str):
        parts = [parts]
    candidates = [p for p in parts if isinstance(p, str) and p.count(",") >= 2]
    return max(candidates, key=lambda p: p.count(","), default="")


def product_key(brand, name):
    """Normalized brand+name so the same product from two datasets is stored once."""
    return re.sub(r"[^a-z0-9]", "", f"{brand}{name}".lower())


def read_csv(path):
    csv.field_size_limit(10_000_000)
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        yield from csv.DictReader(f)


def sephora_products(path):
    for row in read_csv(path):
        category = SEPHORA_CATEGORIES.get(row.get("tertiary_category"))
        if row.get("primary_category") != "Hair" or not category:
            continue
        ingredients = clean_ingredient_text(sephora_ingredient_text(row.get("ingredients") or ""))
        yield {
            "name": row["product_name"].strip(),
            "brand": row["brand_name"].strip(),
            "category": category,
            "url": f"sephora:{row['product_id']}",  # no product page URL in this dataset
            "source": "Sephora",
            "ingredients": ingredients,
        }


def ecommerce_products(path):
    for row in read_csv(path):
        store = ECOMMERCE_STORES.get((row.get("website") or "").strip().lower())
        category = ECOMMERCE_CATEGORIES.get((row.get("subcategory") or "").strip().lower())
        if row.get("category") != "hair" or not store or not category:
            continue
        url = (row.get("title-href") or "").strip()
        if not url.startswith("http"):
            continue
        yield {
            "name": row["product_name"].strip(),
            "brand": (row.get("brand") or "").strip(),
            "category": category,
            "url": url.split("?")[0],
            "source": store,
            "ingredients": clean_ingredient_text(row.get("ingredients") or ""),
        }


def main():
    sources = [(SEPHORA_FILE, sephora_products), (ECOMMERCE_FILE, ecommerce_products)]
    conn = db.connect()
    seen = {product_key(r["brand"] or "", r["name"])
            for r in conn.execute("SELECT brand, name FROM products")}
    try:
        for path, reader in sources:
            if not os.path.exists(path):
                print(f"Skipping {os.path.basename(path)} (not found in data/)")
                continue
            saved, duplicates, no_ingredients = {}, 0, 0
            for p in reader(path):
                if not p["name"] or len(p["ingredients"]) < MIN_INGREDIENTS:
                    no_ingredients += 1
                    continue
                key = product_key(p["brand"], p["name"])
                if key in seen:
                    duplicates += 1
                    continue
                seen.add(key)
                db.save_product(conn, p["name"], p["brand"], p["category"], p["url"],
                                p["ingredients"], source=p["source"])
                saved[p["category"]] = saved.get(p["category"], 0) + 1
            print(f"{os.path.basename(path)}: saved {sum(saved.values())} {dict(sorted(saved.items()))}")
            print(f"  skipped {duplicates} duplicates, {no_ingredients} without a usable ingredient list")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
