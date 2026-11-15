import pytest

import rules


def score(ingredients, category=None, **form):
    return rules.score_ingredients(ingredients, rules.build_profile(form), category)


# --- sensitive scalp: real contact allergens ---------------------------------

@pytest.mark.parametrize("allergen", [
    "Methylisothiazolinone", "Methylchloroisothiazolinone", "Quaternium-15", "DMDM Hydantoin",
    "Imidazolidinyl Urea", "Diazolidinyl Urea", "Cocamidopropyl Betaine", "Propylene Glycol",
])
def test_sensitive_scalp_flags_contact_allergens(allergen):
    r = score(["Water", "Glycerin", allergen], scalp="sensitive")
    assert allergen in r["bad"]


def test_fragrance_allergens_count_less_than_main_allergens():
    mild = score(["Water", "Glycerin", "Linalool"], scalp="sensitive")
    strong = score(["Water", "Glycerin", "Methylisothiazolinone"], scalp="sensitive")
    assert "Linalool" in mild["bad"]
    assert strong["score"] < mild["score"] < 0


def test_scalp_allergens_count_less_in_rinse_off_products():
    ingredients = ["Water", "Glycerin", "Methylisothiazolinone"]
    shampoo = score(ingredients, "shampoo", scalp="sensitive")
    leave_in = score(ingredients, "leave-in", scalp="sensitive")
    pasted = score(ingredients, None, scalp="sensitive")  # unknown type is treated as leave-on
    assert leave_in["score"] < shampoo["score"] < 0
    assert pasted["score"] == leave_in["score"]


def test_new_exclude_toggles():
    assert score(["Water", "Methylisothiazolinone"], avoid_isothiazolinones="1")["label"] == "Excluded"
    assert score(["Water", "DMDM Hydantoin"], avoid_formaldehyde="1")["label"] == "Excluded"


# --- dandruff: plant oils feed Malassezia --------------------------------------

@pytest.mark.parametrize("oil", [
    "Cocos Nucifera (Coconut) Oil", "Olea Europaea (Olive) Fruit Oil", "Ricinus Communis (Castor) Seed Oil",
    "Argania Spinosa Kernel Oil", "Butyrospermum Parkii (Shea) Butter", "Helianthus Annuus (Sunflower) Seed Oil",
])
def test_dandruff_flags_plant_oils(oil):
    assert oil in score(["Water", oil], scalp="dandruff")["bad"]


@pytest.mark.parametrize("ingredient", [
    "Caprylic/Capric Triglyceride", "Squalane", "Zinc Pyrithione",
])
def test_dandruff_safe_oils_and_actives_are_good(ingredient):
    assert ingredient in score(["Water", ingredient], scalp="dandruff")["good"]


@pytest.mark.parametrize("not_an_oil", [
    "Zea Mays (Corn) Starch", "Helianthus Annuus (Sunflower) Seed Extract", "Cocos Nucifera (Coconut) Water",
    "Olea Europaea (Olive) Leaf Extract",
])
def test_plant_extracts_and_starches_are_not_oils(not_an_oil):
    assert score(["Water", not_an_oil], scalp="dandruff")["bad"] == []


# --- porosity -------------------------------------------------------------------

def test_high_porosity_likes_coconut_oil():
    assert "Cocos Nucifera (Coconut) Oil" in score(["Water", "Cocos Nucifera (Coconut) Oil"], porosity="high")["good"]


def test_low_porosity_only_penalizes_protein_near_top_of_label():
    low_down = ["Water", "Glycerin", "Cetearyl Alcohol", "Behentrimonium Chloride", "Aloe Barbadensis Leaf Juice",
                "Panthenol", "Hydrolyzed Wheat Protein"]
    assert "Hydrolyzed Wheat Protein" not in score(low_down, porosity="low")["bad"]
    up_top = ["Water", "Hydrolyzed Keratin", "Glycerin"]
    assert "Hydrolyzed Keratin" in score(up_top, porosity="low")["bad"]


# --- conflicts between traits ---------------------------------------------------

def test_warning_wins_when_traits_disagree():
    r = score(["Water", "Cocos Nucifera (Coconut) Oil"], porosity="high", scalp="dandruff")
    assert "Cocos Nucifera (Coconut) Oil" in r["bad"]
    assert "Cocos Nucifera (Coconut) Oil" not in r["good"]


# --- fine hair and coily hair ---------------------------------------------------

def test_fine_hair_avoids_build_up_silicones_but_not_water_soluble_ones():
    assert "Amodimethicone" in score(["Water", "Amodimethicone"], thickness="fine")["bad"]
    assert score(["Water", "PEG-12 Dimethicone"], thickness="fine")["bad"] == []


def test_coily_hair_likes_detangling_conditioners():
    r = score(["Water", "Behentrimonium Chloride", "Polyquaternium-10"], curl_pattern="4B")
    assert {"Behentrimonium Chloride", "Polyquaternium-10"} <= set(r["good"])
