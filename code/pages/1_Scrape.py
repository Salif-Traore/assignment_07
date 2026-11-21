"""1_Scrape.py - Part 1: scrape the rivals' menus into one dataset."""

import os

import pandas as pd
import streamlit as st

from rivals import CAFES, MENUS_FILE, OUR_CAFE, run_scraper

# 1. HEADING
st.title("Salt City: Scrape the Rivals")
st.markdown("Pick the cafés to scrape. Each run replaces the saved dataset.")

# 2. PICK AND SCRAPE
cafes = st.multiselect("Cafés", options=list(CAFES), default=list(CAFES), key="cafes")
if st.button("Scrape", key="scrape"):
    if not cafes:
        st.warning("Pick at least one café.")
    else:
        with st.spinner("Visiting the cafés - this takes a few seconds each..."):
            result = run_scraper(cafes)
        if result.returncode == 0:
            st.success(result.stdout.strip().splitlines()[-1])
        else:
            st.error("The scraper failed.")
            st.code(result.stderr[-1500:])

# 3. NOTHING TO SHOW YET?
if not os.path.exists(MENUS_FILE):
    st.info("No menus yet - pick the cafés and click Scrape.")
    st.stop()

# 4. THE DATASET
menus = pd.read_csv(MENUS_FILE)
theirs = menus[menus["cafe"] != OUR_CAFE]

col_cafes, col_items, col_rows = st.columns(3)
col_cafes.metric("Cafés", theirs["cafe"].nunique())
col_items.metric("Items", len(theirs[["cafe", "item"]].drop_duplicates()))
col_rows.metric("Rows", len(theirs))

st.dataframe(menus, hide_index=True)
st.download_button(
    "Download the dataset",
    menus.to_csv(index=False),
    file_name="menus.csv",
    mime="text/csv",
    key="download",
)
