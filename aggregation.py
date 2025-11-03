# Robust monthly product-market build that keeps ALL branded UPCs
# and labels brand as "Generic" ONLY when generic_hardcoded == 1.

import pandas as pd
import numpy as np

# ================================
# Helpers
# ================================
def to_num_col(df, col, default=0):
    """Numeric series aligned to df.index; fill with default if missing."""
    if col in df.columns:
        return pd.to_numeric(df[col], errors="coerce").fillna(default)
    return pd.Series(default, index=df.index, dtype="float64")

def coerce_binary(series):
    """Coerce to 0/1 int8 from numeric or Y/N/T/F strings."""
    s_num = pd.to_numeric(series, errors="coerce")
    s_txt = (series.astype("string").str.upper().str.strip()
             .map({"Y":1, "YES":1, "T":1, "TRUE":1, "N":0, "NO":0, "F":0, "FALSE":0}))
    s = s_num.fillna(s_txt).fillna(0)
    return (s > 0).astype("int8")

def first_nonnull(s):
    return s.dropna().iloc[0] if s.notna().any() else np.nan

def pick_col(cols, *cands):
    for c in cands:
        if c in cols: return c
    low = {c.lower(): c for c in cols}
    for c in cands:
        if c.lower() in low: return low[c.lower()]
    return None

# ================================
# 0) Load
# ================================
df = pd.read_csv("cigarettes.csv", low_memory=False, encoding="utf-8")

# Normalize brand string early (but DO NOT drop blanks here)
df["brand"] = df.get("brand", "").astype("string").str.strip()

# ================================
# 1) Keep cigarettes (robust)
#    Treat as cigarette if ANY of:
#      - explicit cigarettes flag == 1
#      - brand non-empty
#      - generic_hardcoded == 1
# ================================
brand_nonempty   = df["brand"].ne("")
generic_flag_raw = to_num_col(df, "generic_hardcoded").gt(0)
cig_flag_raw     = to_num_col(df, "cigarettes").gt(0)
is_cigarette     = cig_flag_raw | brand_nonempty | generic_flag_raw

df = df.loc[is_cigarette].copy()
df["cigarettes"] = 1  # normalize

# ================================
# 2) Normalize keys & validity
# ================================
df["store"]    = pd.to_numeric(df["store"], errors="coerce").astype("Int64")
df["week"]     = pd.to_numeric(df["week"],  errors="coerce").astype("Int64")
df["upc_norm"] = df["upc"].astype("string").str.replace(r"\D", "", regex=True)

df = df.loc[
    df["store"].notna() & df["week"].notna()
    & df["upc_norm"].notna() & df["upc_norm"].ne("")
].copy()

# ================================
# 3) Convert to PACKS (10PK / 10CT / CARTON)
# ================================
carton_col = pick_col(df.columns, "carton", "Carton", "CARTON")

s = df.get("size_carton_pack", df.get("size","")).astype("string")\
      .str.upper().str.replace(r"\s+"," ", regex=True).str.strip()
looks_10 = s.str.contains(r"\b10\s*CT\b|\b10\s*PK\b|\bCARTON\b", regex=True, na=False)

if carton_col is None:
    df["packs_per_item"] = np.where(looks_10, 10.0, 1.0)
else:
    c = to_num_col(df, carton_col).astype(int)
    df["packs_per_item"] = np.where(c == 1, 10.0, 1.0)
    df.loc[(c != 1) & looks_10, "packs_per_item"] = 10.0

df["price"] = to_num_col(df, "price")
df["move"]  = to_num_col(df, "move")
df["qty"]   = to_num_col(df, "qty")

df = df.loc[(df["qty"] > 0) & (df["packs_per_item"] > 0)].copy()
df["row_revenue"] = df["price"] * df["move"] / df["qty"]
df["pack_sales"]  = df["move"]  * df["packs_per_item"]

# ================================
# 4) Monthly time index
# ================================
date_col = pick_col(df.columns, "date", "week_end", "weekend", "week_end_date", "start_date")
if date_col is not None:
    df["__date"] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.loc[df["__date"].notna()].copy()
    df["cal_year"]   = df["__date"].dt.year.astype("Int64")
    df["cal_month"]  = df["__date"].dt.month.astype("Int64")
    y0 = int(df["cal_year"].min())
    m0 = int(df.loc[df["cal_year"] == y0, "cal_month"].min())
    df["month_idx"]  = ((df["cal_year"] - y0) * 12 + (df["cal_month"] - m0) + 1).astype("Int64")
    df["month_label"] = df["__date"].dt.to_period("M").astype(str)
    time_cols = ["month_idx","cal_year","cal_month","month_label"]
else:
    base_week = int(df["week"].min())
    df["year52"] = ((df["week"] - base_week) // 52 + 1).astype("Int64")
    df["m4"]     = (((df["week"] - base_week) % 52) // 4 + 1).astype("Int64")
    df["month_idx"]  = ((df["year52"] - 1) * 13 + df["m4"]).astype("Int64")
    df["month_label"] = "Y" + df["year52"].astype(str) + "-M" + df["m4"].astype(str)
    time_cols = ["month_idx","year52","m4","month_label"]

# ================================
# 5) Product & brand labeling
#    - product_id = UPC for ALL cigarettes
#    - brand = "Generic" ONLY when generic_hardcoded == 1
# ================================
orig_brand      = df.get("brand","").astype("string").str.strip()
is_generic_flag = to_num_col(df, "generic_hardcoded").gt(0)  # recompute on current df

df["brand"] = orig_brand.mask(is_generic_flag, other="Generic")

df["brand_clean"] = (df["brand"].astype("string")
                     .str.strip()
                     .str.replace(r"\s+"," ", regex=True)
                     .str.lower())

df["prod_type"] = "cigarette"
df["prod_id"]   = df["upc_norm"]                      # UPC for everyone
df["prod_key"]  = df["prod_type"] + "|" + df["prod_id"]

# ================================
# 6) Characteristics
# ================================
known_dummies = [
    "menthol","dlx","special","supslim","slim","generic","single","carton","pack_kw",
    "value","generic_automated","generic_hardcoded","flavored","premium","cigarettes","ok","sale"
]
dummy_cols = [c for c in known_dummies if c in df.columns]
for c in dummy_cols:
    df[c] = coerce_binary(df[c])

known_continuous = [
    "tar_mean","nic_mean","co_mean",
    "income","educ","hsizeavg","age9","age60","ethnic","nocar","custcount"
]
if "implied discount" in df.columns:
    known_continuous.append("implied discount")

cat_cols = [c for c in ["brand","brand_clean","size","size_carton_pack"] if c in df.columns]

# ================================
# 7) Aggregate to product × (store, month)
# ================================
group_cols = ["store","month_idx","prod_key","prod_type","prod_id"] + [c for c in time_cols if c != "month_idx"]

agg_dict = {
    "pack_sales": ("pack_sales","sum"),
    "row_revenue": ("row_revenue","sum"),
}
for c in dummy_cols:
    agg_dict[c] = (c, "max")
for c in known_continuous:
    agg_dict[c] = (c, first_nonnull)
for c in cat_cols + ["upc_norm"]:
    if c in df.columns:
        agg_dict[c] = (c, first_nonnull)

prod_market_m = (
    df.groupby(group_cols, as_index=False, observed=True)
      .agg(**agg_dict)
      .rename(columns={"pack_sales":"total_packs","row_revenue":"total_rev"})
)

# sales-weighted packs_per_item
if "packs_per_item" in df.columns:
    w = (
        df.groupby(group_cols, observed=True)
          .apply(lambda g: np.average(g["packs_per_item"], weights=g["pack_sales"])
                 if g["pack_sales"].sum() > 0 else np.nan)
          .reset_index(name="packs_per_item_wavg")
    )
    prod_market_m = prod_market_m.merge(w, on=group_cols, how="left")

# price per pack
prod_market_m["avg_pack_price"] = prod_market_m["total_rev"] / prod_market_m["total_packs"]
prod_market_m.loc[~np.isfinite(prod_market_m["avg_pack_price"]), "avg_pack_price"] = np.nan

# ================================
# 8) Market size & shares (store × month)
# ================================
store_month_total = (
    prod_market_m.groupby(["store","month_idx"], observed=True)["total_packs"]
                 .sum().reset_index(name="store_month_total_packs")
)
m_max_store = (
    store_month_total.groupby("month_idx", observed=True)["store_month_total_packs"]
                     .max().reset_index(name="max_store_total_in_month")
)
m_max_store["market_size_month"] = 1.5 * m_max_store["max_store_total_in_month"]

prod_market_m = prod_market_m.merge(
    m_max_store[["month_idx","market_size_month"]],
    on="month_idx", how="left", validate="many_to_one"
)

prod_market_m["prod_mkt_share"] = prod_market_m["total_packs"] / prod_market_m["market_size_month"]

# ================================
# 9) Diagnostics
# ================================
n_markets = df[["store","month_idx"]].drop_duplicates().shape[0]
n_rows    = prod_market_m.shape[0]
print(f"Product–market rows (monthly): {n_rows:,}")
print(f"Store–month markets: {n_markets:,}")
print(f"Avg products per market: {n_rows / max(n_markets,1):.2f}")

counts = prod_market_m.groupby(["store","month_idx"]).size()
print(counts.describe())

sum_share_storem = (
    prod_market_m.groupby(["store","month_idx"], observed=True)["prod_mkt_share"].sum()
)
print("Mean ∑ shares per (store,month):", float(sum_share_storem.mean()))
print("Max  ∑ shares per (store,month):",  float(sum_share_storem.max()))

# ================================
# 10) Save CSV
# ================================
out_path = "prod_market_m.csv"
prod_market_m.to_csv(out_path, index=False)
print(f"Wrote {out_path}  |  rows: {prod_market_m.shape[0]:,}, cols: {prod_market_m.shape[1]}")
