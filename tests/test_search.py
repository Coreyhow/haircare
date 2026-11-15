import db
from app import app


def make_db(tmp_path, monkeypatch):
    path = str(tmp_path / "t.db")
    monkeypatch.setenv("HAIRCARE_DB_PATH", path)
    conn = db.connect(path)
    db.save_product(conn, "Shea Butter Leave-In Conditioning Cream", "Cantu", "leave-in", "https://x/1",
                    ["Water", "Butyrospermum Parkii (Shea) Butter", "Cetyl Alcohol", "Glycerin"])
    db.save_product(conn, "Curl Activator Cream", "Cantu", "styling", "https://x/2",
                    ["Water", "Glycerin", "Cetearyl Alcohol"])
    db.save_product(conn, "100% Natural Shampoo", "Other_Brand", "shampoo", "https://x/3",
                    ["Water", "Sodium Laureth Sulfate", "Fragrance"])
    return conn


def test_search_matches_all_words_across_brand_and_name(tmp_path, monkeypatch):
    conn = make_db(tmp_path, monkeypatch)
    assert [p["name"] for p in db.search_products(conn, "cantu leave-in")] == \
        ["Shea Butter Leave-In Conditioning Cream"]
    assert len(db.search_products(conn, "CANTU")) == 2
    assert db.search_products(conn, "   ") == []


def test_search_treats_like_wildcards_literally(tmp_path, monkeypatch):
    conn = make_db(tmp_path, monkeypatch)
    assert [p["name"] for p in db.search_products(conn, "100%")] == ["100% Natural Shampoo"]
    assert len(db.search_products(conn, "%")) == 1  # only the product with a literal '%'
    assert [p["brand"] for p in db.search_products(conn, "other_brand")] == ["Other_Brand"]
    # As a wildcard, '_' would match the space after "Other_Brand" in "brand 100%..."
    assert db.search_products(conn, "brand_") == []


def test_search_page_scores_results_with_profile(tmp_path, monkeypatch):
    make_db(tmp_path, monkeypatch)
    html = app.test_client().get("/search?q=cantu&curl_pattern=4C").get_data(as_text=True)
    assert "Shea Butter Leave-In Conditioning Cream" in html
    assert "Great match" in html or "Good match" in html
    # profile is carried in the hidden form fields so the next search keeps it
    assert 'name="curl_pattern" value="4C"' in html


def test_search_page_without_profile_suggests_answering_questions(tmp_path, monkeypatch):
    make_db(tmp_path, monkeypatch)
    html = app.test_client().get("/search?q=nothingmatches").get_data(as_text=True)
    assert "No products found" in html
    assert "answer the hair questions first" in html
