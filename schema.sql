-- Haircare SQLite schema. Applied automatically by db.connect().
CREATE TABLE IF NOT EXISTS ingredients (
    ingredientID   INTEGER PRIMARY KEY,
    ingredientName TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    productID INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL,
    brand     TEXT,
    category  TEXT NOT NULL,   -- shampoo | conditioner | leave-in | hair-mask | hair-oil | ...
    url       TEXT NOT NULL UNIQUE,  -- product page, or a unique id like 'sephora:P123'
    source    TEXT                   -- where the data came from, e.g. 'Sephora', 'Ulta'
);

CREATE TABLE IF NOT EXISTS product_ingredients (
    productID    INTEGER NOT NULL REFERENCES products(productID) ON DELETE CASCADE,
    ingredientID INTEGER NOT NULL REFERENCES ingredients(ingredientID),
    position     INTEGER NOT NULL,   -- order on the label (lower = more of it)
    PRIMARY KEY (productID, ingredientID)
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
