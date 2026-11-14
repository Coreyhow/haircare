# Haircare

A site that recommends shampoos, conditioners and leave-ins based on your hair profile (curl pattern 1A–4C, porosity, strand thickness, density, scalp) and checks ingredient lists you paste in.

## How it works
- `scraper.py` – scrapes Ulta product pages into `haircare.db` (products + ingredients, in label order)
- `rules.py` – maps hair traits to ingredients to prefer/avoid; scores products (ingredients near the top of the label count more)
- `app.py` – Flask app: form at `/`, recommendations at `/results`
- `db.py` / `schema.sql` – SQLite database (one file, created automatically)

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Moving existing MySQL data (one time)
```powershell
pip install mysql-connector-python
$env:MYSQL_USER="corey"; $env:MYSQL_PASSWORD="<password>"
python migrate_mysql_to_sqlite.py
```

## Run locally
```bash
python openbeautyfacts.py            # load products from Open Beauty Facts (a few minutes)
flask --app app run                   # open http://127.0.0.1:5000
pytest
```

`scraper.py` (Ulta) is kept for reference but Ulta blocks automated requests.

## Store products (Sephora, Ulta) from Kaggle datasets
1. Download these (free Kaggle account) and unzip into `data/`:
   - [Sephora Products and Skincare Reviews](https://www.kaggle.com/datasets/nadyinky/sephora-products-and-skincare-reviews) by nadyinky (CC BY 4.0) → `data/product_info.csv` (the review files aren't needed)
   - [E-commerce Cosmetic Products](https://www.kaggle.com/datasets/devi5723/e-commerce-cosmetics-dataset) by devi5723 (MIT) → `data/E-commerce  cosmetic dataset.csv`
2. `python import_datasets.py`

`data/` is git-ignored; only `haircare.db` needs to be committed.
The CC BY license requires crediting the Sephora dataset; that credit is in `templates/_credits.html`, so keep it there.

## Free hosting (PythonAnywhere)
1. Scrape locally so `haircare.db` is filled, then commit it (or upload it).
2. Create a free account at pythonanywhere.com and open a Bash console:
   `git clone <your repo>` then `pip install --user flask`
3. Web tab → Add a new web app → Manual configuration → Python 3.x.
4. Edit the WSGI file so it contains:
   ```python
   import sys
   sys.path.insert(0, "/home/<username>/haircare")
   from app import app as application
   ```
5. Reload. Your site is at `https://<username>.pythonanywhere.com`.

To update products later: rerun the scraper locally, then upload the new `haircare.db` and reload.

Recommendations are general guidance, not medical advice.
