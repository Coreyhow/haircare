import db


def test_save_and_load_roundtrip(tmp_path):
    conn = db.connect(str(tmp_path / "test.db"))
    db.save_product(conn, "Curl Cream", "Brand", "leave-in", "https://x/1",
                    ["Water", "Shea Butter", "Glycerin"])
    # Re-saving the same URL updates instead of duplicating
    db.save_product(conn, "Curl Cream v2", "Brand", "leave-in", "https://x/1",
                    ["Water", "Glycerin"])
    db.save_product(conn, "Shampoo", None, "shampoo", "https://x/2", ["Water"])

    products = db.load_products(conn)
    assert len(products) == 2
    cream = next(p for p in products if p["url"] == "https://x/1")
    assert cream["name"] == "Curl Cream v2"
    assert cream["ingredients"] == ["Water", "Glycerin"]
    assert [p["name"] for p in db.load_products(conn, "shampoo")] == ["Shampoo"]
    conn.close()
