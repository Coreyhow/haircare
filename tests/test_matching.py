import pytest

import rules


@pytest.mark.parametrize("ingredient, group", [
    ("Triethanolamine", rules.DRYING_ALCOHOLS),       # pH adjuster, not drying alcohol
    ("Sodium Cocoate", rules.SOOTHING),               # 'oat' inside a word
    ("Sodium Cocoyl Goatmilk", rules.SOOTHING),
    ("PEG-12 Dimethicone", rules.SILICONES_NONSOLUBLE),  # water-soluble silicone
    ("Dimethicone Copolyol", rules.SILICONES_NONSOLUBLE),
    ("Hydrolyzed Corn Starch", rules.PROTEINS),
    ("Cetyl Alcohol", rules.DRYING_ALCOHOLS),         # fatty alcohol, not drying
])
def test_false_matches_are_ignored(ingredient, group):
    assert rules._matches(ingredient, group) is None


@pytest.mark.parametrize("ingredient, group", [
    ("Alcohol Denat.", rules.DRYING_ALCOHOLS),
    ("Ethanol", rules.DRYING_ALCOHOLS),
    ("Avena Sativa (Oat) Kernel Extract", rules.SOOTHING),
    ("Dimethicone", rules.SILICONES_NONSOLUBLE),
    ("Hydrolyzed Wheat Protein", rules.PROTEINS),
    ("Wheat Amino Acids", rules.PROTEINS),            # plural
    ("Butyrospermum Parkii (Shea) Butter", rules.HEAVY_OILS_BUTTERS),
    ("Sodium Laureth Sulfate", rules.SULFATES),
    ("Argania Spinosa Kernel Oil", rules.LIGHT_OILS),
    ("Simmondsia Chinensis (Jojoba) Seed Oil", rules.LIGHT_OILS),
    ("Cetostearyl Alcohol", rules.FATTY_ALCOHOLS),
    # combined entry: plain dimethicone still counts even though PEG appears later
    ("Dimethicone (and) Amodimethicone (and) PEG-7 Propylheptyl Ether", rules.SILICONES_NONSOLUBLE),
])
def test_real_matches_still_work(ingredient, group):
    assert rules._matches(ingredient, group) is not None
