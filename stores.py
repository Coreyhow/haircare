"""'Find at <store>' search links. Only builds URLs; no store data is fetched."""
from urllib.parse import quote_plus

STORES = [
    ("Ulta", "https://www.ulta.com/search?search={q}"),
    ("Target", "https://www.target.com/s?searchTerm={q}"),
    ("Sally Beauty", "https://www.sallybeauty.com/search?q={q}"),
    ("Walmart", "https://www.walmart.com/search?q={q}"),
]


def store_links(name, brand=None):
    query = f"{brand} {name}" if brand and brand.lower() not in name.lower() else name
    q = quote_plus(query.strip())
    return [(store, url.format(q=q)) for store, url in STORES]
