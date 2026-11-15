# Strand Match

A site that recommends hair products for your hair: curl pattern 1A–4C, porosity, strand thickness, density and scalp. It also checks products you already own, by name or by pasting the ingredient list.

## How it works
- `app.py` is the Flask web app. Pages: `/` (questions), `/results` (recommendations), `/search` (check a product by name). It also handles `/feedback` (👍/👎 votes). The site name is set at the top of the file.
- `rules.py` maps hair traits to ingredients to prefer and to avoid, and scores products. Ingredients near the top of the label count more. The evidence behind each rule is in `RESEARCH.md`.
- `db.py` / `schema.sql`: the product database, `haircare.db` (SQLite, a single file, committed to git).
- `feedback.py`: visitor votes, stored in `feedback.db`. **This file is git-ignored, so votes on the live site are never overwritten.**
- `stores.py`: the "Find at Ulta / Target / Sally Beauty / Walmart" search links.
- `templates/`: `base.html` (shared header and footer), `_product_card.html`, one template per page.

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Run locally
```bash
flask --app app run      # open http://127.0.0.1:5000
pytest                   # run the tests
```

## Updating products
- `python openbeautyfacts.py` loads products from the free Open Beauty Facts API.
- `python import_datasets.py` loads Sephora and Ulta products from the Kaggle datasets:
  1. Download these (free Kaggle account) and unzip into `data/`:
     - [Sephora Products and Skincare Reviews](https://www.kaggle.com/datasets/nadyinky/sephora-products-and-skincare-reviews) by nadyinky (CC BY 4.0) → `data/product_info.csv`. The review files aren't needed.
     - [E-commerce Cosmetic Products](https://www.kaggle.com/datasets/devi5723/e-commerce-cosmetics-dataset) by devi5723 (MIT) → `data/E-commerce  cosmetic dataset.csv`.
  2. Run `python import_datasets.py`.
- `data/` is git-ignored; only `haircare.db` needs to be committed.
- The CC BY license requires crediting the Sephora dataset. That credit is in `templates/_credits.html`, so keep it there.
- `scraper.py` holds the ingredient-list splitter the loaders share. Its old Ulta scraper no longer works because Ulta blocks automated requests.

## Changing the rules
1. Run `python label_report.py` to see how labels are spread across all products.
2. Edit `rules.py`.
3. Run `python label_report.py` again to compare, and run `pytest`.

## Reading visitor feedback
On PythonAnywhere, open a Bash console and run:
```bash
cd haircare
python feedback_report.py
```
It shows how often each label ("Great match", "Okay"…) actually worked for people, and which "matches" got 👎.

## Free hosting (PythonAnywhere)
1. Commit and push your code and `haircare.db` to GitHub.
2. In a PythonAnywhere Bash console: `git clone <your repo>` then `pip install --user flask`.
3. Web tab → Add a new web app → Manual configuration → Python 3.x.
4. Edit the WSGI file so it contains:
   ```python
   import sys
   sys.path.insert(0, "/home/<username>/haircare")
   from app import app as application
   ```
5. Reload. Your site is at `https://<username>.pythonanywhere.com`.

To deploy updates: `git push` on your computer, then `cd haircare && git pull` on PythonAnywhere, then Reload.

Recommendations are general guidance, not medical advice.
