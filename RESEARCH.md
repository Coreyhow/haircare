# Why the rules in `rules.py` say what they say

General guidance only, not medical advice. A dermatologist's patch test is the only reliable way to find someone's personal allergens.

## Sensitive scalp: contact allergens
- After hair dye (PPD), the most common hair-product allergens are the preservatives **methylisothiazolinone (MI)** and **methylchloroisothiazolinone (MCI)**, found in up to 51% of shampoo formulations. Formaldehyde-releasing preservatives such as **Quaternium-15** are also common; one study identified Quaternium-15 as the likely cause of scalp dermatitis in 5% of patients. **Cocamidopropyl betaine** is the third most common allergen in shampoos and conditioners, although it isn't a strong allergen itself. ([Practical Dermatology](https://practicaldermatology.com/topics/feature/contact-dermatitis-and-hair-care/29190/))
- Fragrance, cocamidopropyl betaine, Quaternium-15 and **propylene glycol** are frequent hair-product allergens. Rinse-off products like shampoo and conditioner rarely cause reactions because contact is brief. → `rinse_off_factor`. ([Cosmetics, MDPI 2024](https://www.mdpi.com/2079-9284/11/3/78))
- In a study of textured-hair products, fragrance appeared in 90% of them, linalool in 32% and limonene in 29%. The clinical relevance of linalool and limonene is questionable, though they may worsen scarring hair loss. → `avoid_mild`. ([Williams, Nwosu, Tosti 2025](https://journals.sagepub.com/doi/10.1089/derm.2024.0469))

## Dandruff / seborrheic dermatitis
- The yeast *Malassezia* can't make its own fats. In lab tests it grew well on butter, corn oil, olive oil, coconut oil, oleic acid and castor oil. → `MALASSEZIA_FOOD`. ([PMC10015641](https://pmc.ncbi.nlm.nih.gov/articles/PMC10015641/))
- Dermatologists typically advise keeping oils and heavy, waxy styling products off the scalp. ([Acibadem](https://acibademinternational.com/blog/styling-products-oils-and-dandruff-treatment-what-your-dermatologist-will-ask-you-to-change/))
- MCT oil (caprylic/capric triglyceride) and squalane are commonly cited as oils the yeast can't feed on. → `MALASSEZIA_SAFE`. This comes from skincare formulators rather than clinical trials.

## Curly and coily hair
- Tightly coiled hair is fragile, with lower water content and tensile strength. Lauryl sulfates can leave it "exceedingly dry and unmanageable". Cationic surfactants and polymers such as polyquaternium help detangle and maintain the curl pattern. → `CATIONIC_CONDITIONERS`. ([Cutis 2020](https://www.mdedge.com/cutis/article/220336/hair-nails/hair-care-products-used-women-african-descent-review-ingredients))
- Simple humectants such as glycerin may reduce breakage in tightly curled and coily hair. ([CurlsBot, citing the research literature](https://www.curlsbot.com/blog/hair-porosity-explained))

## Porosity
Evidence here is weaker than internet advice suggests.
- Low porosity: the real issue is weight and build-up from heavy butters and thick oils, not any banned ingredient. ([The Mestiza Muse](https://themestizamuse.com/ingredients-to-avoid-for-low-porosity-hair-a-comprehensive-guide/))
- Avoiding all protein for low porosity isn't supported. Some film-forming proteins can feel stiff when used heavily. → `avoid_top`: protein is only penalized when it's one of the first five ingredients. ([CurlsBot](https://www.curlsbot.com/blog/is-protein-bad-for-low-porosity-hair))
- High porosity: coconut oil has the strongest evidence of any oil for penetrating the strand and reducing protein loss during washing. → `COCONUT_OIL`.

## Fine strands / thin density
- Heavy oils, butters and non-water-soluble silicones build up and weigh fine hair down. Water-soluble (PEG/PPG) silicones rinse out.

## When traits disagree
If any of a person's traits says to avoid an ingredient, it's shown as a warning even when another trait likes it. For example, coconut oil is good for high porosity but feeds dandruff.
