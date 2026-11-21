"""3_Analysis.py - Part 3: where are we high or low, and what are we missing?"""

import os

import pandas as pd
import streamlit as st

from rivals import (
    ABOVE_ALL,
    ABOVE_AVERAGE,
    BELOW_ALL,
    BELOW_AVERAGE,
    DECISIONS_FILE,
    MENUS_FILE,
    add_canonical,
    compare_prices,
    gap_analysis,
    match_items,
    price_table,
)
from rivals.settings import DECISION_COLUMNS

# 1. HEADING AND DATA
st.set_page_config(layout="wide")
st.title("Salt City: Prices and Gaps")

if not os.path.exists(MENUS_FILE):
    st.info("No menus yet - scrape the rivals first.")
    st.stop()

menus = pd.read_csv(MENUS_FILE)
if os.path.exists(DECISIONS_FILE):
    decisions = pd.read_csv(DECISIONS_FILE)
else:
    decisions = pd.DataFrame(columns=DECISION_COLUMNS)
matches = match_items(menus, decisions)

waiting = int((matches["status"] == "unreviewed").sum())
if waiting:
    st.warning(
        f"{waiting} items have not been reviewed yet, so they are left out. "
        "Finish them on the Review Matches page."
    )

# 2. THE ANALYSIS
menus = add_canonical(menus, matches)
prices = price_table(menus)
comparison = compare_prices(prices)
gaps = gap_analysis(menus)

# 3. TWO TABS
prices_tab, gaps_tab = st.tabs(["Prices", "Gaps"])

# 4. THE PRICES TAB
with prices_tab:
    below = comparison["our_position"].isin([BELOW_ALL, BELOW_AVERAGE]).sum()
    above = comparison["our_position"].isin([ABOVE_ALL, ABOVE_AVERAGE]).sum()
    col_below, col_above = st.columns(2)
    col_below.metric("Priced below the market", int(below))
    col_above.metric("Priced above the market", int(above))

    products = st.multiselect(
        "Products",
        sorted(comparison["canonical"].unique()),
        key="products",
        placeholder="All products",
    )
    if products:
        shown = comparison[comparison["canonical"].isin(products)]
    else:
        shown = comparison
    st.dataframe(shown, hide_index=True)
    st.caption(
        "👍👍 lower than all of them · 👍 lower than their average · "
        "👉👈 average · 👎 higher than their average · "
        "👎👎 higher than all of them"
    )

# 5. THE GAPS TAB
with gaps_tab:
    st.subheader("Only them - what we don't sell yet")
    st.dataframe(gaps[gaps["where"] == "only them"], hide_index=True)
    st.subheader("Only us - what sets us apart")
    st.dataframe(gaps[gaps["where"] == "only us"], hide_index=True)
