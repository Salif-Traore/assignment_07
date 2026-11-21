"""scrapers.py - Part 1, Step 2: one scraper per rival café."""

from io import StringIO
from urllib.parse import urljoin

import pandas as pd

from .cleaning import card_rows, clean_price
from .settings import CANAL_SHOP, cafe_url


def scrape_lakeshore(page) -> list[dict]:
    """Lakeshore Lattes: section headings, each followed by a grid of menu cards."""
    page.goto(cafe_url("Lakeshore Lattes"))
    rows = []
    for heading in page.query_selector_all("h2.menu-section__title"):
        category = heading.inner_text().strip()
        grid = heading.query_selector("~ div.menu-grid")
        for card in grid.query_selector_all("article.menu-card"):
            rows.extend(card_rows("Lakeshore Lattes", category, card.inner_text()))
    return rows


def scrape_hilltop(page) -> list[dict]:
    """Hilltop Grind: an <h2> and a <table> per category, melted to one row per size."""
    page.goto(cafe_url("Hilltop Grind"))
    categories = [h.inner_text().strip() for h in page.query_selector_all("#menu h2")]
    tables = pd.read_html(StringIO(page.content()))
    rows = []
    for category, table in zip(categories, tables):
        table = table.drop(columns="Description")
        melted = table.melt(id_vars="Item", var_name="size", value_name="price")
        melted = melted.dropna(subset=["price"])
        for record in melted.to_dict("records"):
            rows.append({
                "cafe": "Hilltop Grind",
                "category": category,
                "item": record["Item"],
                "size": record["size"],
                "price": clean_price(str(record["price"])),
            })
    return rows


def scrape_canal(page, shop: str = CANAL_SHOP) -> list[dict]:
    """Canal Street Coffee: drive the order-ahead app, then crawl every item page."""
    menu_url = cafe_url("Canal Street Coffee")
    page.goto(menu_url)
    page.get_by_label("Choose your shop").select_option(shop)
    page.get_by_role("button", name="Show full menu").click()
    page.wait_for_selector("a.result-card")

    more = page.get_by_role("button", name="Show more")
    while more.is_visible():
        count = page.locator("a.result-card").count()
        more.click()
        page.wait_for_function(
            f"document.querySelectorAll('a.result-card').length > {count}"
        )

    links = [card.get_attribute("href") for card in page.locator("a.result-card").all()]

    rows = []
    for href in links:
        page.goto(urljoin(menu_url, href))
        page.wait_for_selector("#sizes")
        item = page.locator("#item-name").inner_text().strip()
        category = page.locator("#item-category").inner_text().split(" · ")[0].strip()
        for tr in page.locator("#sizes tbody tr").all():
            cells = tr.locator("td")
            rows.append({
                "cafe": "Canal Street Coffee",
                "category": category,
                "item": item,
                "size": cells.nth(0).inner_text().strip(),
                "price": clean_price(cells.nth(1).inner_text()),
            })
    return rows
