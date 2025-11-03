# RUN IT IN LONGLEAF, DONT RUN IN YOU PC
# build_cigarettes.py
import pandas as pd
import numpy as np

# -----------------------------
# helpers
# -----------------------------
def read_upccig(path):
    """Robust CSV reader for UPC file (handles non-UTF8)."""
    for enc in ("latin1", "cp1252", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="utf-8", errors="replace", low_memory=False)

def downcast(df, ints=(), floats=()):
    for c in ints:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce", downcast="integer")
    for c in floats:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce", downcast="float")
    return df

# -----------------------------
# 1) read raw files
# -----------------------------
wcig   = pd.read_csv("wcig.csv", low_memory=False)            # movement
upccig = read_upccig("upccig_with_tnco_HARD_imputed.csv")     # UPC attributes
ccount = pd.read_stata("ccount.dta")                          # store-week counts
demo   = pd.read_stata("demo.dta")                            # store demographics

# normalize names
for _df in (wcig, upccig, ccount, demo):
    _df.columns = _df.columns.str.strip().str.lower()

# -----------------------------
# 2) keep manual fields only
# -----------------------------
mv_keep  = ["upc","store","week","move","price","qty","profit","sale","ok"]
#upc_keep = ["upc","com_code","nitem","descrip","size","case"]
wcig   = wcig[[c for c in mv_keep  if c in wcig.columns]].copy()
#upccig = upccig[[c for c in upc_keep if c in upccig.columns]].copy()

# ccount: detect customer-count column name (varies)
custcount_col = next((c for c in ccount.columns if c.startswith("cust") and "coun" in c), None)
cc_keep = ["store","week"] + ([custcount_col] if custcount_col else [])
ccount  = ccount[[c for c in cc_keep if c in ccount.columns]].copy()
if custcount_col:
    ccount = ccount.rename(columns={custcount_col: "custcount"})

# demo: keep common documented subset if present
demo_keep = ["store","income","educ","hsizeavg","age9","age60","ethnic","nocar","poverty","zone"]
demo = demo[[c for c in demo_keep if c in demo.columns]].copy()

# -----------------------------
# 3) keys & dtypes per manual
# -----------------------------
# UPC -> 11-digit numeric string
for _df in (wcig, upccig):
    if "upc" in _df.columns:
        _df["upc"] = _df["upc"].astype(str).str.extract(r"(\d+)")[0].fillna("")
        _df["upc"] = _df["upc"].str.zfill(11)

# downcast numerics (saves RAM)
wcig = downcast(wcig, ints=["store","week","ok"], floats=["move","price","qty","profit"])
if "sale" in wcig.columns:
    wcig["sale"] = wcig["sale"].astype("category")

upccig["descrip"] = upccig.get("descrip", pd.Series(index=upccig.index, dtype="object")).astype("string")
for c in ["upc","com_code","nitem","size"]:
    if c in upccig.columns:
        upccig[c] = upccig[c].astype("category")

ccount = downcast(ccount, ints=["store","week"], floats=["custcount"] if "custcount" in ccount.columns else [])
demo   = downcast(demo,   ints=["store"],       floats=[c for c in demo.columns if c != "store"])

# ensure RHS uniqueness
upccig = upccig.drop_duplicates(subset=["upc"])
ccount = ccount.drop_duplicates(subset=["store","week"])
demo   = demo.drop_duplicates(subset=["store"])

# -----------------------------
# 4) validity filters (manual)
# -----------------------------
if "ok" in wcig.columns:
    wcig = wcig[wcig["ok"] == 1].copy()

wcig = wcig.dropna(subset=["move","price"])
wcig = wcig[(wcig["move"] > 0) & (wcig["price"] > 0)].copy()

# -----------------------------
# 5) price & quantity (bundle rule)
# -----------------------------
wcig["qty"] = wcig.get("qty", 1).replace(0, 1)
wcig["quantity"]   = wcig["move"].astype("float32")  # actual items sold

# -----------------------------
# 6) merges per manual keys
# -----------------------------
# a) by UPC
df = pd.merge(wcig, upccig, on="upc", how="inner", validate="m:1")
# b) by store + week
df = pd.merge(df, ccount, on=["store","week"], how="left", validate="m:1")
# c) by store
df = pd.merge(df, demo, on="store", how="left", validate="m:1")

# -----------------------------
# 7) write final compact file
# -----------------------------
df.to_csv("cigarettes.csv", index=False)

print("Wrote cigarettes.csv")
