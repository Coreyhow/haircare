import db
import feedback
from app import app, safe_return_path


def setup(tmp_path, monkeypatch):
    path = str(tmp_path / "t.db")
    monkeypatch.setenv("HAIRCARE_DB_PATH", path)
    monkeypatch.setenv("HAIRCARE_FEEDBACK_PATH", str(tmp_path / "fb.db"))
    db.save_product(db.connect(path), "Curl Cream", "Brand", "styling", "https://x/1",
                    ["Water", "Glycerin", "Cetyl Alcohol"])


def votes(tmp_path):
    return [tuple(r) for r in feedback.connect(str(tmp_path / "fb.db")).execute(
        "SELECT product_url, vote, label, profile FROM feedback")]


def test_vote_is_saved_and_redirects_back_with_thanks(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    r = app.test_client().post("/feedback", data={
        "product_url": "https://x/1", "vote": "up", "label": "Great match",
        "profile": "curl_pattern=4C&porosity=high&email=someone@example.com",
        "next": "/search?q=curl&curl_pattern=4C"})
    assert r.status_code == 303
    assert r.headers["Location"].startswith("/search?q=curl&curl_pattern=4C&voted=")
    assert r.headers["Location"].endswith("#product-1")  # scrolls back to the voted card
    # unknown fields (like an email) are dropped from the stored profile
    assert votes(tmp_path) == [("https://x/1", 1, "Great match", "curl_pattern=4C&porosity=high")]


def test_thanks_message_shows_on_the_voted_card(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    html = app.test_client().get("/search?q=curl&voted=https://x/1").get_data(as_text=True)
    assert "Thanks! Your feedback" in html


def test_bad_votes_are_rejected(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    client = app.test_client()
    assert client.post("/feedback", data={"product_url": "https://x/1", "vote": "maybe"}).status_code == 400
    assert client.post("/feedback", data={"product_url": "https://nope", "vote": "up"}).status_code == 400
    assert votes(tmp_path) == []


def test_redirect_never_leaves_the_site():
    for evil in ["https://evil.example/x", "//evil.example/x", "javascript:alert(1)", "evil"]:
        assert safe_return_path(evil, "u").startswith("/?voted=")
    assert safe_return_path("/results?voted=old&q=1", "new") == "/results?q=1&voted=new"
