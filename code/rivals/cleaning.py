"""
cleaning.py - Part 1, Step 1: turn scraped text into clean values.

A scraper hands you whatever the page shows a person, and pages are written for
people. These functions turn raw menu-card text into rows a DataFrame can hold.
They are plain Python - no browser - so they are quick to test and quick to fix.

Every café names its drink sizes S, M and L (Lakeshore pours only S and L); food
has one price, which we call "Each".
"""

import re

# Lines on a menu card that are decoration, not data.
NOISE = {"NEW!", "NEW", "V", "GF"}


def clean_price(text: str) -> float:
    """A price as a number: "$4.75" -> 4.75, " $1,029.00 " -> 1029.0."""
    cleaned = text.replace("$", "").replace(",", "").strip()
    return float(cleaned)


def clean_card_lines(text: str) -> list[str]:
    """The useful lines of a menu card, in order, with the decoration removed."""
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if all(word in NOISE for word in line.split()):
            continue
        lines.append(line)
    return lines


def parse_price_line(line: str) -> list[tuple[str, float]]:
    """Every (size, price) pair on a price line; a price with no size is "Each"."""
    pairs = []
    for size, price in re.findall(r"([SML])?\s*(\$[\d.,]+)", line):
        pairs.append((size or "Each", clean_price(price)))
    return pairs


def card_rows(cafe: str, category: str, card_text: str) -> list[dict]:
    """One row per size for one menu card: cafe, category, item, size, price."""
    lines = clean_card_lines(card_text)
    item = lines[0]
    price_line = next(line for line in lines if "$" in line)
    rows = []
    for size, price in parse_price_line(price_line):
        rows.append({
            "cafe": cafe,
            "category": category,
            "item": item,
            "size": size,
            "price": price,
        })
    return rows
