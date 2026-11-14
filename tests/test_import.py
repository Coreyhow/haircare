import import_datasets as imp


def test_sephora_picks_longest_variation_list():
    raw = "['Shampoo:', 'Water, Glycerin, Sodium Cocoyl Isethionate, Fragrance', 'Mini:', 'Water, Glycerin']"
    assert imp.sephora_ingredient_text(raw) == "Water, Glycerin, Sodium Cocoyl Isethionate, Fragrance"


def test_sephora_handles_plain_text():
    assert imp.sephora_ingredient_text("Water, Glycerin, Panthenol") == "Water, Glycerin, Panthenol"


def test_clean_strips_disclaimer_and_marketing():
    text = ("Water, Cetearyl Alcohol, Shea Butter. Please be aware that ingredient lists may change, "
            "Glycerin")
    assert imp.clean_ingredient_text(text) == ["Water", "Cetearyl Alcohol", "Shea Butter"]
    long_phrase = "Water, Glycerin, this amazing formula leaves your hair feeling soft and shiny all day"
    assert imp.clean_ingredient_text(long_phrase) == ["Water", "Glycerin"]


def test_product_key_matches_across_datasets():
    assert imp.product_key("SheaMoisture", "Curl & Shine Shampoo") == \
        imp.product_key("Shea Moisture", "Curl and Shine Shampoo".replace(" and ", " & "))
