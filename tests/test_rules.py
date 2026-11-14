import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rules
from scraper import split_ingredients


def test_split_keeps_numeric_commas_and_parentheses():
    text = "Water (Aqua), 1,2-Hexanediol, Fragrance (Parfum, Natural), Glycerin."
    assert split_ingredients(text) == [
        "Water (Aqua)", "1,2-Hexanediol", "Fragrance (Parfum, Natural)", "Glycerin",
    ]


def test_build_profile_drops_invalid_values():
    p = rules.build_profile({"porosity": "HIGH", "curl_pattern": "4c", "scalp": "weird"})
    assert p["porosity"] == "high"
    assert p["curl_pattern"] == "4C"
    assert p["curl_family"] == "coily"
    assert "scalp" not in p


def test_coily_prefers_butter_over_sulfate():
    profile = rules.build_profile({"curl_pattern": "4B"})
    good = rules.score_ingredients(["Water", "Shea Butter", "Cetyl Alcohol"], profile)
    bad = rules.score_ingredients(["Water", "Sodium Lauryl Sulfate", "Alcohol Denat"], profile)
    assert good["score"] > 0 > bad["score"]


def test_hard_avoid_excludes_products():
    profile = rules.build_profile({"avoid_silicones": "1"})
    products = [
        {"name": "A", "ingredients": ["Water", "Dimethicone"]},
        {"name": "B", "ingredients": ["Water", "Glycerin"]},
    ]
    assert [p["name"] for p in rules.rank_products(products, profile)] == ["B"]
