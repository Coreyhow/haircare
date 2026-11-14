import rules


def test_great_match_with_reason():
    profile = rules.build_profile({"curl_pattern": "4C", "porosity": "high"})
    r = rules.score_ingredients(["Water", "Shea Butter", "Cetyl Alcohol", "Glycerin", "Hydrolyzed Keratin"], profile)
    assert r["label"] == "Great match"
    assert r["reason"].startswith("Has Shea Butter and Cetyl Alcohol")


def test_not_for_you():
    profile = rules.build_profile({"curl_pattern": "3B"})
    r = rules.score_ingredients(["Water", "Sodium Lauryl Sulfate", "Alcohol Denat.", "Dimethicone"], profile)
    assert r["label"] == "Not for you"
    assert "may not suit your hair" in r["reason"]


def test_bad_ingredient_near_top_caps_at_good():
    profile = rules.build_profile({"curl_pattern": "4A"})
    r = rules.score_ingredients(
        ["Water", "Sodium Laureth Sulfate", "Shea Butter", "Cetyl Alcohol", "Glycerin", "Castor Oil"], profile)
    assert r["label"] in ("Good match", "Okay")
    assert "Sodium Laureth Sulfate" in r["reason"]


def test_excluded_and_no_traits():
    r = rules.score_ingredients(["Water", "Dimethicone"], rules.build_profile({"avoid_silicones": "1"}))
    assert r["label"] == "Excluded"
    r = rules.score_ingredients(["Water", "Glycerin"], rules.build_profile({}))
    assert r["label"] is None and r["reason"] is None
