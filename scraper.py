"""Scrape Ulta product listings and store products + ingredients.

Usage: python scraper.py [shampoo|conditioner|leave-in ...]   (default: all)
Replaces shampoo.py / conditionerwebscrape.py / leavein.py.
Check Ulta's robots.txt / terms before running at scale.
"""
import re
import sys
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import db

BASE = "https://www.ulta.com"
CATEGORIES = {
    "shampoo": "/shop/hair/shampoo-conditioner/shampoo",
    "conditioner": "/shop/hair/shampoo-conditioner/conditioner",
    "leave-in": "/shop/hair/treatment/leave-in-conditioner",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (haircare-research-project)"}
DELAY_SECONDS = 1.5
MAX_PAGES = 30

session = requests.Session()
session.headers.update(HEADERS)


def fetch(url):
    resp = session.get(url, timeout=20)
    resp.raise_for_status()
    time.sleep(DELAY_SECONDS)
    return BeautifulSoup(resp.text, "html.parser")


def split_ingredients(text):
    """Split on commas that aren't inside parentheses or between digits (e.g. 1,2-Hexanediol)."""
    parts, depth, current = [], 0, ""
    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(depth - 1, 0)
        if ch == "," and depth == 0:
            prev_digit = i > 0 and text[i - 1].isdigit()
            next_digit = i + 1 < len(text) and text[i + 1].isdigit()
            if not (prev_digit and next_digit):
                parts.append(current)
                current = ""
                continue
        current += ch
    parts.append(current)
    cleaned = []
    for p in parts:
        p = re.sub(r"\s+", " ", p).strip().rstrip(".").strip()
        if p:
            cleaned.append(p)
    return cleaned


def find_ingredients_text(soup):
    """Prefer the block following an 'Ingredients' heading; fall back to the old positional rule."""
    heading = soup.find(lambda t: t.name in ("h2", "h3", "h4", "button", "span")
                        and t.get_text(strip=True).lower() == "ingredients")
    if heading:
        block = heading.find_next("div", class_=re.compile("Markdown"))
        if block and block.get_text(strip=True):
            return block.get_text(" ", strip=True)
    blocks = soup.find_all("div", {"class": "Markdown Markdown--body-2 Markdown--left"})
    if len(blocks) >= 3:
        p = blocks[2].find("p")
        if p:
            return p.get_text(" ", strip=True)
    return None


def scrape_product(url):
    soup = fetch(url)
    title = soup.find("h1")
    name = title.get_text(" ", strip=True) if title else url
    brand_tag = soup.find(class_=re.compile("ProductInformation__brand|brand", re.I))
    brand = brand_tag.get_text(" ", strip=True) if brand_tag else None
    text = find_ingredients_text(soup)
    return name, brand, split_ingredients(text) if text else []


def scrape_category(conn, category):
    path = CATEGORIES[category]
    seen = set()
    for page in range(1, MAX_PAGES + 1):
        print(f"[{category}] page {page}")
        try:
            soup = fetch(f"{BASE}{path}?page={page}")
        except requests.RequestException as e:
            print(f"  listing failed: {e}")
            break
        cards = soup.find_all("li", {"class": "ProductListingResults__productCard"})
        if not cards:
            break
        for card in cards:
            link = card.find("a", href=True)
            if not link:
                continue
            url = urljoin(BASE, link["href"]).split("?")[0]
            if url in seen:
                continue
            seen.add(url)
            try:
                name, brand, ingredients = scrape_product(url)
            except requests.RequestException as e:
                print(f"  skip {url}: {e}")
                continue
            if not ingredients:
                print(f"  no ingredients: {url}")
                continue
            db.save_product(conn, name, brand, category, url, ingredients)
            print(f"  saved {name} ({len(ingredients)} ingredients)")


def main(argv):
    categories = argv or list(CATEGORIES)
    unknown = [c for c in categories if c not in CATEGORIES]
    if unknown:
        sys.exit(f"Unknown category: {', '.join(unknown)}. Choose from {list(CATEGORIES)}")
    conn = db.connect()
    try:
        for c in categories:
            scrape_category(conn, c)
    finally:
        conn.close()


if __name__ == "__main__":
    main(sys.argv[1:])
