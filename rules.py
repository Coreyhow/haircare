"""Hair-profile -> ingredient rules and product scoring.

Rules are general guidance, not medical advice. Each rule lists ingredient
keywords (case-insensitive, matched as whole words, plural 's' allowed):
  prefer      - good for this trait
  avoid       - bad for this trait
  avoid_mild  - minor concern, counts half
  avoid_top   - only a problem when it's one of the first 5 ingredients (a main ingredient)
  rinse_off_factor - how much avoid hits count in rinse-off products (shampoo, conditioner,
                     mask), which touch the scalp briefly; leave-on products count fully
If any active rule says to avoid an ingredient, the warning wins over any rule that prefers it.

Evidence notes are in RESEARCH.md. Edit freely as you learn more.
"""
import re
from functools import lru_cache

# Ingredient keyword groups
SULFATES = ["sodium lauryl sulfate", "sodium laureth sulfate", "ammonium lauryl sulfate",
            "ammonium laureth sulfate", "sodium coco sulfate"]
SILICONES_NONSOLUBLE = ["dimethicone", "amodimethicone", "cyclomethicone", "cyclopentasiloxane",
                        "trimethylsilylamodimethicone"]
DRYING_ALCOHOLS = ["alcohol denat", "isopropyl alcohol", "sd alcohol", "ethanol"]
FATTY_ALCOHOLS = ["cetyl alcohol", "cetearyl alcohol", "cetostearyl alcohol", "stearyl alcohol",
                  "behenyl alcohol"]
HUMECTANTS = ["glycerin", "aloe", "honey", "panthenol", "propanediol", "sodium pca", "hyaluronic"]
PROTEINS = ["keratin", "hydrolyzed", "protein", "amino acid", "silk", "collagen"]
HEAVY_OILS_BUTTERS = ["shea butter", "butyrospermum", "cocoa butter", "theobroma cacao seed butter",
                      "mango butter", "mangifera indica seed butter", "castor oil", "ricinus",
                      "olive oil", "olea europaea", "avocado oil", "persea gratissima",
                      "mineral oil", "paraffinum liquidum", "petrolatum"]
LIGHT_OILS = ["argan", "argania", "grapeseed", "vitis vinifera", "jojoba", "simmondsia",
              "sweet almond", "prunus amygdalus dulcis", "sunflower", "helianthus annuus",
              "squalane"]
SOOTHING = ["aloe", "niacinamide", "allantoin", "chamomile", "bisabolol", "oat"]
ANTI_DANDRUFF = ["zinc pyrithione", "ketoconazole", "salicylic acid", "selenium sulfide",
                 "piroctone olamine", "tea tree"]
FRAGRANCE = ["fragrance", "parfum"]
CLARIFYING = ["sodium cocoyl isethionate", "cocamidopropyl betaine", "decyl glucoside",
              "coco-glucoside"]
# Coconut oil is the oil with the best evidence of entering the strand and reducing protein loss
COCONUT_OIL = ["coconut oil", "cocos nucifera"]
# Positively charged conditioners that help tight curls detangle and hold their pattern
CATIONIC_CONDITIONERS = ["polyquaternium", "behentrimonium", "cetrimonium", "stearamidopropyl dimethylamine",
                         "guar hydroxypropyltrimonium"]

# Contact allergens (North American Contact Dermatitis Group data; see RESEARCH.md)
ISOTHIAZOLINONES = ["methylisothiazolinone", "methylchloroisothiazolinone"]
FORMALDEHYDE_RELEASERS = ["quaternium-15", "dmdm hydantoin", "imidazolidinyl urea", "diazolidinyl urea",
                          "sodium hydroxymethylglycinate", "bronopol", "2-bromo-2-nitropropane-1,3-diol"]
COCAMIDOPROPYL_BETAINE = ["cocamidopropyl betaine"]
PROPYLENE_GLYCOL = ["propylene glycol"]
# Fragrance chemicals that must be listed on EU labels; weaker evidence, so counted lightly
FRAGRANCE_ALLERGENS = ["linalool", "limonene", "benzyl salicylate", "hexyl cinnamal", "citronellol",
                       "geraniol", "eugenol", "isoeugenol", "coumarin", "hydroxycitronellal",
                       "cinnamal", "alpha-isomethyl ionone", "benzyl benzoate"]

# Dandruff/seborrheic dermatitis yeast (Malassezia) feeds on the fatty acids in plant oils and butters
MALASSEZIA_FOOD = ["shea butter", "butyrospermum", "cocoa butter", "theobroma cacao seed butter",
                   "mango butter", "mangifera indica seed butter", "castor oil", "ricinus", "olive oil",
                   "olea europaea", "avocado oil", "persea gratissima", "coconut oil", "cocos nucifera",
                   "argan", "argania", "grapeseed", "vitis vinifera", "jojoba", "simmondsia",
                   "sweet almond", "prunus amygdalus dulcis", "sunflower", "helianthus annuus",
                   "soybean oil", "glycine soja", "corn oil", "zea mays", "oleic acid"]
# Oils the yeast can't use
MALASSEZIA_SAFE = ["caprylic/capric triglyceride", "mct oil", "squalane"]

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
        "avoid": HEAVY_OILS_BUTTERS,
        "avoid_top": PROTEINS,
        "why": "Low-porosity hair is easily coated: heavy butters and thick oils build up. "
               "Protein is fine in small amounts, but a protein-heavy formula can feel stiff.",
    },
    ("porosity", "high"): {
        "prefer": PROTEINS + COCONUT_OIL + HEAVY_OILS_BUTTERS + FATTY_ALCOHOLS,
        "avoid": DRYING_ALCOHOLS + SULFATES,
        "why": "High-porosity hair is usually damaged and loses moisture fast; protein and coconut oil "
               "help limit protein loss, and richer conditioners protect it.",
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
        "prefer": HUMECTANTS + FATTY_ALCOHOLS + CATIONIC_CONDITIONERS,
        "avoid": SULFATES + SILICONES_NONSOLUBLE + DRYING_ALCOHOLS,
        "why": "Curls are prone to dryness; gentle cleansers, moisture and detangling conditioners help.",
    },
    ("curl_family", "coily"): {
        "prefer": HEAVY_OILS_BUTTERS + FATTY_ALCOHOLS + HUMECTANTS + CATIONIC_CONDITIONERS,
        "avoid": SULFATES + DRYING_ALCOHOLS,
        "why": "Coily hair is the driest and most fragile: harsh sulfates leave it brittle, while "
               "humectants, rich butters and detangling conditioners help prevent breakage.",
    },
    ("thickness", "fine"): {
        "prefer": LIGHT_OILS,
        "avoid": HEAVY_OILS_BUTTERS + SILICONES_NONSOLUBLE,
        "why": "Fine strands are easily weighed down by heavy oils, butters and build-up silicones.",
    },
    ("thickness", "coarse"): {
        "prefer": HEAVY_OILS_BUTTERS + FATTY_ALCOHOLS,
        "avoid": DRYING_ALCOHOLS,
        "why": "Coarse strands can handle and benefit from richer conditioning.",
    },
    ("density", "thin"): {
        "prefer": [],
        "avoid": HEAVY_OILS_BUTTERS + SILICONES_NONSOLUBLE,
        "why": "Less hair on the head means heavy products and build-up show and flatten quickly.",
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
        "avoid": ISOTHIAZOLINONES + FORMALDEHYDE_RELEASERS + FRAGRANCE + COCAMIDOPROPYL_BETAINE
                 + PROPYLENE_GLYCOL + SULFATES + DRYING_ALCOHOLS,
        "avoid_mild": FRAGRANCE_ALLERGENS,
        "rinse_off_factor": 0.5,
        "why": "The most common hair-product allergens are the preservatives methylisothiazolinone and "
               "formaldehyde releasers, fragrance, cocamidopropyl betaine and propylene glycol. They "
               "matter most in leave-in products.",
    },
    ("scalp", "dandruff"): {
        "prefer": ANTI_DANDRUFF + MALASSEZIA_SAFE,
        "avoid": MALASSEZIA_FOOD,
        "rinse_off_factor": 0.5,
        "why": "The yeast behind dandruff feeds on plant oils and butters (including coconut and olive oil), "
               "so keep them off the scalp. Medicated ingredients help; MCT oil and squalane are safe oils.",
    },
}

AVOID_TOGGLES = {
    "avoid_sulfates": SULFATES,
    "avoid_silicones": SILICONES_NONSOLUBLE,
    "avoid_fragrance": FRAGRANCE,
    "avoid_protein": PROTEINS,
    "avoid_isothiazolinones": ISOTHIAZOLINONES,
    "avoid_formaldehyde": FORMALDEHYDE_RELEASERS,
}

# Product types that are rinsed off soon after applying (see rinse_off_factor)
RINSE_OFF = {"shampoo", "conditioner", "hair-mask"}


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


# Ingredients that contain a keyword but don't belong to its group.
# keyword -> regex; if the regex matches the ingredient, the keyword is ignored.
EXCEPTIONS = {
    # Water-soluble silicones (PEG/PPG/copolyol) rinse out and don't build up
    "dimethicone": r"\b(peg|ppg)\b|copolyol",
    "amodimethicone": r"\b(peg|ppg)\b|copolyol",
    # Protein words in non-protein ingredients
    "hydrolyzed": r"hydrolyzed (corn|wheat|rice)? ?starch|hydrolyzed jojoba",
}

# Plant names that mark an oil or butter only when the ingredient isn't an extract,
# starch, protein, plant water, etc. (e.g. "Zea Mays (Corn) Starch" has no oil).
NOT_AN_OIL = r"\b(extract|water|juice|protein|starch|flour|powder|peptides?|amino acids?|seed meal)\b"
for _plant in ["argan", "argania", "grapeseed", "vitis vinifera", "jojoba", "simmondsia", "sweet almond",
               "prunus amygdalus dulcis", "sunflower", "helianthus annuus", "olea europaea",
               "persea gratissima", "cocos nucifera", "ricinus", "butyrospermum", "glycine soja", "zea mays",
               "theobroma cacao seed butter", "mangifera indica seed butter"]:
    EXCEPTIONS.setdefault(_plant, NOT_AN_OIL)


@lru_cache(maxsize=None)
def _pattern(keyword):
    return re.compile(r"\b" + re.escape(keyword) + r"s?\b")


def _matches(ingredient, keywords):
    # Labels sometimes combine several ingredients in one entry ("A (and) B"),
    # so check each part separately; exceptions only apply to their own part.
    parts = re.split(r"\(and\)|\band\b|&", ingredient.lower())
    for k in keywords:
        for part in parts:
            if _pattern(k).search(part):
                exception = EXCEPTIONS.get(k)
                if exception and re.search(exception, part):
                    continue
                return k
    return None


def score_ingredients(ingredients, profile, category=None):
    """Score an ingredient list. Earlier label position = bigger effect.

    category (e.g. 'shampoo') lets scalp rules go easier on rinse-off products; when it's
    unknown (a pasted ingredient list) every product is treated as leave-on.
    """
    rules = active_rules(profile)
    rinse_off = category in RINSE_OFF
    hard = [kw for toggle in profile.get("hard_avoid", []) for kw in AVOID_TOGGLES[toggle]]
    score, good, bad, blocked = 0.0, [], [], []
    bad_near_top = False
    for pos, ing in enumerate(ingredients):
        weight = 2.0 if pos < 5 else 1.0 if pos < 15 else 0.5
        if _matches(ing, hard):
            blocked.append(ing)
            continue
        penalty = reward = 0.0
        for _, _, rule in rules:
            factor = rule.get("rinse_off_factor", 1.0) if rinse_off else 1.0
            if _matches(ing, rule["avoid"]):
                penalty += weight * factor
            elif _matches(ing, rule.get("avoid_mild", [])):
                penalty += weight * 0.5 * factor
            elif pos < 5 and _matches(ing, rule.get("avoid_top", [])):
                penalty += weight
            elif _matches(ing, rule["prefer"]):
                reward += weight
        # When traits disagree about an ingredient (e.g. coconut oil: good for high porosity,
        # bad for dandruff), the warning wins.
        if penalty:
            score -= penalty
            bad_near_top = bad_near_top or pos < 5
            if ing not in bad:
                bad.append(ing)
        elif reward:
            score += reward
            if ing not in good:
                good.append(ing)
    result = {"score": round(score, 1), "good": good, "bad": bad, "blocked": blocked}
    result.update(verdict(score, len(rules), good, bad, blocked, bad_near_top))
    return result


# Cutoffs are per active rule, so picking more hair traits doesn't inflate scores.
GREAT_AT, GOOD_AT, POOR_AT = 4.0, 1.5, -1.5


def verdict(score, rule_count, good, bad, blocked, bad_near_top=False):
    """Plain-language label and one-line reason for a scored product."""
    if blocked:
        return {"label": "Excluded", "label_class": "poor",
                "reason": f"Contains {_list(blocked[:2])}, which you chose to exclude."}
    if rule_count == 0:
        return {"label": None, "label_class": None, "reason": None}
    per_rule = score / rule_count
    if per_rule >= GREAT_AT and not bad_near_top:
        label, css = "Great match", "great"
    elif per_rule >= GOOD_AT:
        label, css = "Good match", "good"
    elif per_rule > POOR_AT:
        label, css = "Okay", "okay"
    else:
        label, css = "Not for you", "poor"

    if good and (css in ("great", "good") or not bad):
        reason = f"Has {_list(good[:2])}, which suit your hair."
        if bad:
            reason += f" Also contains {_list(bad[:1])}, which may not."
    elif bad:
        reason = f"Contains {_list(bad[:2])}, which may not suit your hair."
        if good:
            reason += f" It does have {_list(good[:1])}."
    else:
        reason = "Nothing in it stands out as especially good or bad for your hair."
    return {"label": label, "label_class": css, "reason": reason}


def _list(items):
    return " and ".join(items) if len(items) <= 2 else ", ".join(items[:-1]) + " and " + items[-1]


def rank_products(products, profile, limit=10):
    results = []
    for p in products:
        s = score_ingredients(p["ingredients"], profile, p.get("category"))
        if s["blocked"]:
            continue
        results.append({**p, **s})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def parse_ingredient_text(text):
    from scraper import split_ingredients
    return split_ingredients(text or "")
