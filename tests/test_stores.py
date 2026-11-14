import stores


def test_store_links_include_brand_once_and_encode():
    links = dict(stores.store_links("Curl & Shine Conditioner", "SheaMoisture"))
    assert links["Ulta"] == "https://www.ulta.com/search?search=SheaMoisture+Curl+%26+Shine+Conditioner"
    assert set(links) == {"Ulta", "Target", "Sally Beauty", "Walmart"}
    # brand already in the name is not repeated
    assert "Cantu+Cantu" not in dict(stores.store_links("Cantu Shea Butter Leave-In", "Cantu"))["Target"]
