"""analysis.py - Part 3: where are we high or low, and what are we missing?"""

import pandas as pd

from .settings import (
    ABOVE_ALL,
    ABOVE_AVERAGE,
    AT_AVERAGE,
    BELOW_ALL,
    BELOW_AVERAGE,
    OUR_CAFE,
    SIZES,
)


def add_canonical(menus: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """`menus` plus a `canonical` column: the one name every café's item goes by."""
    lookup = matches[["cafe", "item", "matched_to"]].rename(
        columns={"matched_to": "canonical"}
    )
    merged = pd.merge(menus, lookup, on=["cafe", "item"], how="left")
    ours = merged["cafe"] == OUR_CAFE
    merged.loc[ours, "canonical"] = merged.loc[ours, "item"]
    return merged


def price_table(menus: pd.DataFrame) -> pd.DataFrame:
    """Price per (canonical item, size) per café.  *(Provided.)*

    Rows are (`canonical`, `size`), sizes in menu order (S, M, L, Each); columns
    are the cafés; values are prices. Rows with no canonical name (not reviewed
    yet) are left out.
    """
    known = menus.dropna(subset=["canonical"])
    table = known.pivot_table(index=["canonical", "size"], columns="cafe",
                              values="price", aggfunc="first")
    order = {size: rank for rank, size in enumerate(SIZES)}
    return table.sort_index(key=lambda level: level.map(order) if level.name == "size"
                            else level)


def price_position(ours: float, low: float, average: float, high: float) -> str:
    """Where our price stands against the rivals' lowest, average and highest."""
    if ours < low:
        return BELOW_ALL
    if ours > high:
        return ABOVE_ALL
    if ours < average:
        return BELOW_AVERAGE
    if ours > average:
        return ABOVE_AVERAGE
    return AT_AVERAGE


def compare_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Our price next to every rival's, for every item and size we both sell."""
    rivals = [cafe for cafe in prices.columns if cafe != OUR_CAFE]
    table = prices.dropna(subset=[OUR_CAFE])
    table = table[table[rivals].notna().any(axis=1)]

    out = table.rename(columns={OUR_CAFE: "our_price"}).reset_index()
    out = out[["canonical", "size", "our_price"] + rivals]
    out["rival_avg"] = out[rivals].mean(axis=1).round(2)
    out["rival_low"] = out[rivals].min(axis=1)
    out["rival_high"] = out[rivals].max(axis=1)
    if out.empty:
        out["our_position"] = pd.Series(dtype=str)
    else:
        out["our_position"] = out.apply(
            lambda row: price_position(
                row["our_price"], row["rival_low"], row["rival_avg"],
                row["rival_high"],
            ),
            axis=1,
        )
    return out.drop(columns=["rival_low", "rival_high"]).reset_index(drop=True)


def gap_analysis(menus: pd.DataFrame) -> pd.DataFrame:
    """Which items only we sell, which only rivals sell, and which we both do."""
    known = menus.dropna(subset=["canonical"])
    ours = known[known["cafe"] == OUR_CAFE][["canonical", "kind"]].drop_duplicates()
    theirs = known[known["cafe"] != OUR_CAFE]

    rivals = (
        theirs.groupby(["canonical", "kind"])["cafe"]
        .agg(rivals="nunique", sold_by=lambda cafes: ", ".join(sorted(cafes.unique())))
        .reset_index()
    )
    merged = pd.merge(ours, rivals, on=["canonical", "kind"], how="outer",
                      indicator=True)
    merged["where"] = merged["_merge"].astype(str).map(
        {"left_only": "only us", "right_only": "only them", "both": "both"}
    )
    merged["rivals"] = merged["rivals"].fillna(0).astype(int)
    merged["sold_by"] = merged["sold_by"].fillna("")
    merged["rank"] = merged["where"].map({"only them": 0, "only us": 1, "both": 2})

    merged = merged.sort_values(
        ["rank", "rivals", "canonical"], ascending=[True, False, True]
    )
    columns = ["canonical", "kind", "where", "rivals", "sold_by"]
    return merged[columns].reset_index(drop=True)
