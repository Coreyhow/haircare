"""One-time copy of your existing MySQL data into haircare.db.

Usage (PowerShell):
    $env:MYSQL_USER="corey"; $env:MYSQL_PASSWORD="<password>"
    python migrate_mysql_to_sqlite.py
Requires: pip install mysql-connector-python
"""
import os

import mysql.connector

import db


def main():
    src = mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ.get("MYSQL_DB", "haircare"),
    )
    cur = src.cursor()
    dest = db.connect()

    cur.execute("SELECT ingredientID, ingredientName FROM ingredients")
    rows = [(i, n.strip()) for i, n in cur.fetchall() if n and n.strip() and len(n) <= 255]
    with dest:
        dest.executemany(
            "INSERT OR IGNORE INTO ingredients (ingredientID, ingredientName) VALUES (?, ?)", rows
        )
    print(f"Copied {len(rows)} ingredients.")

    cur.execute("SHOW TABLES LIKE 'products'")
    if cur.fetchone():
        cur.execute("SELECT productID, name, brand, category, url FROM products")
        products = cur.fetchall()
        cur.execute("SELECT productID, ingredientID, position FROM product_ingredients")
        links = cur.fetchall()
        with dest:
            dest.executemany(
                "INSERT OR IGNORE INTO products (productID, name, brand, category, url) "
                "VALUES (?, ?, ?, ?, ?)", products)
            dest.executemany(
                "INSERT OR IGNORE INTO product_ingredients (productID, ingredientID, position) "
                "VALUES (?, ?, ?)", links)
        print(f"Copied {len(products)} products.")

    src.close()
    dest.close()


if __name__ == "__main__":
    main()
