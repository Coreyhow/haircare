"""SQLite connection and data-access helpers.

The database is a single file (default: haircare.db next to this file).
Override with the HAIRCARE_DB_PATH environment variable.
"""
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.join(HERE, "haircare.db")
SCHEMA_PATH = os.path.join(HERE, "schema.sql")


def connect(path=None):
    conn = sqlite3.connect(path or os.environ.get("HAIRCARE_DB_PATH", DEFAULT_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    return conn


def get_or_create_ingredient(conn, name):
    conn.execute("INSERT OR IGNORE INTO ingredients (ingredientName) VALUES (?)", (name,))
    return conn.execute(
        "SELECT ingredientID FROM ingredients WHERE ingredientName = ?", (name,)
    ).fetchone()[0]


def clean_brand(brand):
    """Turn tag-style brands ('california-naturals') into 'California Naturals'."""
    brand = (brand or "").strip()
    if brand and brand == brand.lower() and " " not in brand:
        brand = brand.replace("-", " ").title()
    return brand or None


def save_product(conn, name, brand, category, url, ingredient_names):
    """Insert or refresh a product and its ingredient list."""
    brand = clean_brand(brand)
    with conn:
        conn.execute(
            """INSERT INTO products (name, brand, category, url) VALUES (?, ?, ?, ?)
               ON CONFLICT(url) DO UPDATE SET name = excluded.name,
                   brand = excluded.brand, category = excluded.category""",
            (name, brand, category, url),
        )
        product_id = conn.execute(
            "SELECT productID FROM products WHERE url = ?", (url,)
        ).fetchone()[0]
        conn.execute("DELETE FROM product_ingredients WHERE productID = ?", (product_id,))
        for position, ingredient in enumerate(ingredient_names, start=1):
            if not ingredient or len(ingredient) > 255:
                continue
            ingredient_id = get_or_create_ingredient(conn, ingredient)
            conn.execute(
                "INSERT OR IGNORE INTO product_ingredients (productID, ingredientID, position) "
                "VALUES (?, ?, ?)",
                (product_id, ingredient_id, position),
            )
    return product_id


def load_products(conn, category=None):
    """Return [{id, name, brand, category, url, ingredients:[...]}], ingredients in label order."""
    query = """SELECT p.productID, p.name, p.brand, p.category, p.url, i.ingredientName
               FROM products p
               JOIN product_ingredients pi ON pi.productID = p.productID
               JOIN ingredients i ON i.ingredientID = pi.ingredientID"""
    params = ()
    if category:
        query += " WHERE p.category = ?"
        params = (category,)
    query += " ORDER BY p.productID, pi.position"
    products = {}
    for row in conn.execute(query, params):
        p = products.setdefault(row["productID"], {
            "id": row["productID"], "name": row["name"], "brand": row["brand"],
            "category": row["category"], "url": row["url"], "ingredients": [],
        })
        p["ingredients"].append(row["ingredientName"])
    return list(products.values())
