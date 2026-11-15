"""Print label distribution for a set of test profiles (run before and after editing rules.py)."""
import db
import rules

PROFILES = {
    "4C high porosity": {"curl_pattern": "4C", "porosity": "high"},
    "2A fine oily": {"curl_pattern": "2A", "thickness": "fine", "scalp": "oily"},
    "low porosity": {"porosity": "low"},
    "sensitive scalp": {"scalp": "sensitive"},
    "dandruff": {"scalp": "dandruff"},
    "high porosity + dandruff": {"porosity": "high", "scalp": "dandruff"},
}
LABELS = ["Great match", "Good match", "Okay", "Not for you"]

products = db.load_products(db.connect())
print(f"{'profile':26}" + "".join(f"{label:>13}" for label in LABELS))
for name, form in PROFILES.items():
    profile = rules.build_profile(form)
    counts = dict.fromkeys(LABELS, 0)
    for p in products:
        label = rules.score_ingredients(p["ingredients"], profile, p["category"])["label"]
        if label in counts:
            counts[label] += 1
    print(f"{name:26}" + "".join(f"{counts[label] * 100 / len(products):12.0f}%" for label in LABELS))
