"""Hair-profile -> ingredient rules and product scoring.

Rules are general guidance, not medical advice. Each rule lists ingredient
keyword patterns (case-insensitive substrings) that are good ("prefer") or
bad ("avoid") for a given trait. Edit freely as you learn more.
"""

# Ingredient keyword groups
SULFATES = ["sodium lauryl sulfate", "sodium laureth sulfate", "ammonium lauryl sulfate",
            "ammonium laureth sulfate", "sodium coco sulfate"]
SILICONES_NONSOLUBLE = ["dimethicone", "amodimethicone", "cyclomethicone", "cyclopentasiloxane",
                        "trimethylsilylamodimethicone"]
DRYING_ALCOHOLS = ["alcohol denat", "isopropyl alcohol", "sd alcohol", "ethanol"]
FATTY_ALCOHOLS = ["cetyl alcohol", "cetearyl alcohol", "stearyl alcohol", "behenyl alcohol"]
HUMECTANTS = ["glycerin", "aloe", "honey", "panthenol", "propanediol", "sodium pca", "hyaluronic"]
PROTEINS = ["keratin", "hydrolyzed", "protein", "amino acid", "silk", "collagen"]
HEAVY_OILS_BUTTERS = ["shea butter", "butyrospermum", "cocoa butter", "mango butter",
                      "castor oil", "ricinus", "olive oil", "avocado oil", "mineral oil", "petrolatum"]
LIGHT_OILS = ["argan", "grapeseed", "jojoba", "sweet almond", "sunflower", "squalane"]
SOOTHING = ["aloe", "niacinamide", "allantoin", "chamomile", "bisabolol", "oat"]
ANTI_DANDRUFF = ["zinc pyrithione", "ketoconazole", "salicylic acid", "selenium sulfide",
                 "piroctone olamine", "tea tree"]
FRAGRANCE = ["fragrance", "parfum"]
CLARIFYING = ["sodium cocoyl isethionate", "cocamidopropyl betaine", "decyl glucoside",
              "coco-glucoside"]

OPTIONS = {
    "porosity": ["low", "medium", "high"],
    "curl_pattern": ["1A", "1B", "1C", "2A", "2B", "2C", "3A", "3B", "3C", "4A", "4B", "4C"],
    "thickness": ["fine", "medium", "coarse"],
    "density": ["thin", "medium", "thick"],
    "scalp": ["balanced", "oily", "dry", "sensitive", "dandruff"],
}

# (trait, value) -> {"prefer": [...], "avoid": [...], "why": "..."}
RULES = {
    ("porosity", "low"): {
        "prefer": LIGHT_OILS + HUMECTANTS,
        "avoid": HEAVY_OILS_BUTTERS + PROTEINS,
        "why": "Low-porosity cuticles resist absorption; lightweight moisture works, heavy butters and protein build up.",
    },
    ("porosity", "high"): {
        "prefer": PROTEINS + HEAVY_OILS_BUTTERS + FATTY_ALCOHOLS,
        "avoid": DRYING_ALCOHOLS + SULFATES,
        "why": "High-porosity hair loses moisture fast; protein fills gaps and richer oils seal moisture in.",
    },
    ("porosity", "medium"): {
        "prefer": FATTY_ALCOHOLS,
        "avoid": DRYING_ALCOHOLS,
        "why": "Medium porosity is the most forgiving; mainly avoid drying ingredients.",
    },
    ("curl_family", "straight"): {
        "prefer": LIGHT_OILS,
        "avoid": HEAVY_OILS_BUTTERS,
        "why": "Natural oils travel easily down straight hair, so heavy products weigh it down.",
    },
    ("curl_family", "wavy"): {
        "prefer": LIGHT_OILS + HUMECTANTS,
        "avoid": HEAVY_OILS_BUTTERS + SILICONES_NONSOLUBLE,
        "why": "Waves are easily weighed down and silicones can flatten them over time.",
    },
    ("curl_family", "curly"): {
        "prefer": HUMECTANTS + FATTY_ALCOHOLS,
        "avoid": SULFATES + SILICONES_NONSOLUBLE + DRYING_ALCOHOLS,
        "why": "Curls are prone to dryness; gentle cleansers and moisture help define them.",
    },
    ("curl_family", "coily"): {
        "prefer": HEAVY_OILS_BUTTERS + FATTY_ALCOHOLS + HUMECTANTS,
        "avoid": SULFATES + DRYING_ALCOHOLS,
        "why": "Coily hair is the driest and most fragile; rich butters and gentle cleansing are key.",
    },
    ("thickness", "fine"): {
        "prefer": LIGHT_OILS,
        "avoid": HEAVY_OILS_BUTTERS,
        "why": "Fine strands are easily weighed down.",
    },
    ("thickness", "coarse"): {
        "prefer": HEAVY_OILS_BUTTERS + FATTY_ALCOHOLS,
        "avoid": DRYING_ALCOHOLS,
        "why": "Coarse strands can handle and benefit from richer conditioning.",
    },
    ("density", "thin"): {
        "prefer": [],
        "avoid": HEAVY_OILS_BUTTERS,
        "why": "Less hair on the head means heavy products show and flatten quickly.",
    },
    ("density", "thick"): {
        "prefer": FATTY_ALCOHOLS,
        "avoid": [],
        "why": "More hair needs more slip to detangle.",
    },
    ("scalp", "oily"): {
        "prefer": CLARIFYING,
        "avoid": HEAVY_OILS_BUTTERS,
        "why": "Oily scalps benefit from effective cleansing and lighter products.",
    },
    ("scalp", "dry"): {
        "prefer": HUMECTANTS + SOOTHING,
        "avoid": SULFATES + DRYING_ALCOHOLS,
        "why": "Harsh surfactants strip a dry scalp further.",
    },
    ("scalp", "sensitive"): {
        "prefer": SOOTHING,
        "avoid": FRAGRANCE + SULFATES + DRYING_ALCOHOLS,
        "why": "Fragrance and harsh surfactants are common irritants.",
    },
    ("scalp", "dandruff"): {
        "prefer": ANTI_DANDRUFF,
        "avoid": HEAVY_OILS_BUTTERS,
        "why": "Active anti-dandruff ingredients help; heavy oils can feed flaking.",
    },
}

AVOID_TOGGLES = {
    "avoid_sulfates": SULFATES,
    "avoid_silicones": SILICONES_NONSOLUBLE,
    "avoid_fragrance": FRAGRANCE,
    "avoid_protein": PROTEINS,
}


def curl_family(pattern):
    if not pattern:
        return None
    return {"1": "straight", "2": "wavy", "3": "curly", "4": "coily"}.get(pattern[0])


def build_profile(form):
    """Validate form input into a clean profile dict (unknown values dropped)."""
    profile = {}
    for field, allowed in OPTIONS.items():
        value = (form.get(field) or "").strip()
        if field == "curl_pattern":
            value = value.upper()
        else:
            value = value.lower()
        if value in allowed:
            profile[field] = value
    profile["curl_family"] = curl_family(profile.get("curl_pattern"))
    profile["hard_avoid"] = [k for k in AVOID_TOGGLES if form.get(k)]
    return profile


def active_rules(profile):
    rules = []
    for trait in ("porosity", "curl_family", "thickness", "density", "scalp"):
        rule = RULES.get((trait, profile.get(trait)))
        if rule:
            rules.append((trait, profile[trait], rule))
    return rules


def _matches(ingredient, keywords):
    low = ingredient.lower()
    return next((k for k in keywords if k in low), None)


def score_ingredients(ingredients, profile):
    """Score an ingredient list. Earlier label position = bigger effect."""
    rules = active_rules(profile)
    hard = [kw for toggle in profile.get("hard_avoid", []) for kw in AVOID_TOGGLES[toggle]]
    score, good, bad, blocked = 0.0, [], [], []
    for pos, ing in enumerate(ingredients):
        weight = 2.0 if pos < 5 else 1.0 if pos < 15 else 0.5
        if _matches(ing, hard):
            blocked.append(ing)
            continue
        for _, _, rule in rules:
            if _matches(ing, rule["avoid"]):
                score -= weight
                if ing not in bad:
                    bad.append(ing)
            elif _matches(ing, rule["prefer"]):
                score += weight
                if ing not in good:
                    good.append(ing)
    return {"score": round(score, 1), "good": good, "bad": bad, "blocked": blocked}


def rank_products(products, profile, limit=10):
    results = []
    for p in products:
        s = score_ingredients(p["ingredients"], profile)
        if s["blocked"]:
            continue
        results.append({**p, **s})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def parse_ingredient_text(text):
    from scraper import split_ingredients
    return split_ingredients(text or "")
