"""Flask web app: collect a hair profile, recommend products, check an ingredient list.

Run: flask --app app run   (see README for env vars)
"""
from flask import Flask, render_template, request

import db
import rules
import stores

app = Flask(__name__)
app.jinja_env.globals["store_links"] = stores.store_links
CATEGORIES = ["shampoo", "conditioner", "hair-mask", "hair-oil", "leave-in"]


@app.get("/")
def index():
    return render_template("index.html", options=rules.OPTIONS, categories=CATEGORIES)


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


if __name__ == "__main__":
    app.run(debug=True)
