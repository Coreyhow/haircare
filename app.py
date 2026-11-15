"""Flask web app: collect a hair profile, recommend products, check an ingredient list.

Run: flask --app app run   (see README)
"""
from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from flask import Flask, abort, redirect, render_template, request

import db
import feedback
import rules
import stores

SITE_NAME = "Strand Match"  # change the name here; it's used on every page
TAGLINE = "Find hair products that actually suit your hair"

app = Flask(__name__)
app.jinja_env.globals["store_links"] = stores.store_links
CATEGORIES = ["shampoo", "conditioner", "leave-in", "hair-mask", "hair-oil",
              "scalp-treatment", "styling"]
# Query-string fields that make up a hair profile; carried between pages so answers aren't lost
PROFILE_KEYS = list(rules.OPTIONS) + list(rules.AVOID_TOGGLES)
SEARCH_LIMIT = 30


def current_profile_args():
    return {k: request.args[k] for k in PROFILE_KEYS if request.args.get(k)}


@lru_cache(maxsize=1)
def product_count():
    try:
        conn = db.connect()
        try:
            return f"{conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]:,}"
        finally:
            conn.close()
    except Exception:
        return "over a thousand"


@app.context_processor
def site_context():
    profile_args = current_profile_args()
    return {"site_name": SITE_NAME, "tagline": TAGLINE, "profile_args": profile_args,
            "profile_query": urlencode(profile_args)}


@app.get("/")
def index():
    return render_template("index.html", options=rules.OPTIONS, categories=CATEGORIES,
                           product_count=product_count())


@app.get("/results")
def results():
    profile = rules.build_profile(request.args)
    category = request.args.get("category")
    if category not in CATEGORIES:
        category = None

    pasted = request.args.get("ingredients", "").strip()
    check = None
    if pasted:
        check = rules.score_ingredients(rules.parse_ingredient_text(pasted), profile)
        check["name"] = request.args.get("productname", "").strip() or "Your product"

    recommendations, db_error = [], None
    try:
        conn = db.connect()
        try:
            recommendations = rules.rank_products(db.load_products(conn, category), profile)
        finally:
            conn.close()
    except Exception as e:  # DB not configured / unreachable: still show the ingredient check
        app.logger.warning("Database unavailable: %s", e)
        db_error = "Product database is unavailable right now."

    return render_template(
        "results.html",
        profile=profile,
        rules=rules.active_rules(profile),
        check=check,
        recommendations=recommendations,
        category=category,
        db_error=db_error,
    )


@app.get("/search")
def search():
    query = request.args.get("q", "").strip()[:100]
    profile = rules.build_profile(request.args)
    products, db_error = [], None
    if query:
        try:
            conn = db.connect()
            try:
                found = db.search_products(conn, query, limit=SEARCH_LIMIT)
            finally:
                conn.close()
            products = [{**p, **rules.score_ingredients(p["ingredients"], profile, p["category"])}
                        for p in found]
        except Exception as e:
            app.logger.warning("Database unavailable: %s", e)
            db_error = "Product database is unavailable right now."
    return render_template(
        "search.html",
        query=query,
        products=products,
        limit=SEARCH_LIMIT,
        has_profile=bool(rules.active_rules(profile) or profile["hard_avoid"]),
        db_error=db_error,
    )


def safe_return_path(next_path, voted_url, anchor=""):
    """Only redirect back to a page on this site (never an outside URL), marking which
    product was voted on so its card can say thanks, and scrolling back to that card."""
    parts = urlsplit(next_path or "/")
    if parts.scheme or parts.netloc or not parts.path.startswith("/") or parts.path.startswith("//"):
        parts = urlsplit("/")
    query = [(k, v) for k, v in parse_qsl(parts.query) if k != "voted"] + [("voted", voted_url)]
    return urlunsplit(("", "", parts.path, urlencode(query), anchor))


@app.post("/feedback")
def give_feedback():
    product_url = request.form.get("product_url", "")
    vote = request.form.get("vote")
    if vote not in feedback.VOTES or not product_url:
        abort(400)
    conn = db.connect()
    try:
        exists = conn.execute("SELECT productID FROM products WHERE url = ?", (product_url,)).fetchone()
    finally:
        conn.close()
    if not exists:
        abort(400)
    # Keep only recognized hair-profile fields; nothing personal is stored
    profile = urlencode([(k, v) for k, v in parse_qsl(request.form.get("profile", ""))
                         if k in PROFILE_KEYS])
    fconn = feedback.connect()
    try:
        feedback.record(fconn, product_url, vote, request.form.get("label"), profile)
    finally:
        fconn.close()
    return redirect(safe_return_path(request.form.get("next"), product_url, f"product-{exists[0]}"),
                    code=303)


if __name__ == "__main__":
    app.run(debug=True)
