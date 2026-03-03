import os
import re
import pandas as pd
        
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(BASE_DIR, "data", "data.csv")

REQUIRED_COLUMNS = [
    "product_link",
    "product_brand",
    "product_model",
    "product_manuf_year",
    "product_transmission",
    "clean_price",
    "department",
    "source",
    "ingestion_date",
    "product_mileage",
    "product_fuel",
    "vehicle_category",
    "color",
]

def safe_str(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()

def normalize_text(x) -> str:
    return safe_str(x).lower()

def clean_price_to_float(x):
    if pd.isna(x):
        return None
    s = re.sub(r"[^\d.]", "", str(x))
    try:
        return float(s) if s else None
    except:
        return None

def parse_mileage_km(x):
    if pd.isna(x):
        return None
    s = str(x).strip().lower()
    if not s:
        return None
    s = s.replace("km", "").replace("kms", "").strip()
    if s.endswith("k"):
        num = re.sub(r"[^\d.]", "", s[:-1])
        try:
            return int(float(num) * 1000)
        except:
            return None
    s = re.sub(r"[^\d]", "", s)
    try:
        return int(s) if s else None
    except:
        return None

def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, usecols=[c for c in REQUIRED_COLUMNS if c])
    # normalize fields
    df["brand"] = df["product_brand"].apply(normalize_text)
    df["model"] = df["product_model"].apply(normalize_text)
    df["location"] = df["department"].apply(normalize_text)
    df["fuel"] = df["product_fuel"].apply(normalize_text)
    df["category"] = df["vehicle_category"].apply(normalize_text)
    df["color_norm"] = df["color"].apply(normalize_text)
    df["transmission"] = df["product_transmission"].apply(normalize_text)

    df["year"] = pd.to_numeric(df["product_manuf_year"], errors="coerce").astype("Int64")
    df["price"] = df["clean_price"].apply(clean_price_to_float)
    df["mileage_km"] = df["product_mileage"].apply(parse_mileage_km)

    # keep only rows with a URL id
    df = df.dropna(subset=["product_link"]).drop_duplicates(subset=["product_link"]).copy()
    return df

def filter_df(
    df: pd.DataFrame,
    brand: str | None = None,
    model: str | None = None,
    year: int | None = None,
    location: str | None = None,
):
    out = df
    if brand:
        out = out[out["brand"] == brand.lower().strip()]
    if model:
        out = out[out["model"] == model.lower().strip()]
    if year is not None:
        out = out[out["year"] == int(year)]
    if location:
        out = out[out["location"] == location.lower().strip()]
    return out

def summarize_market(df_f: pd.DataFrame) -> dict:
    df_p = df_f.dropna(subset=["price"]).copy()

    result = {
        "count_listings": int(len(df_f)),
        "count_with_price": int(len(df_p)),
        "avg_price": None,
        "median_price": None,
        "min_price": None,
        "max_price": None,
    }

    if len(df_p) > 0:
        result["avg_price"] = float(df_p["price"].mean())
        result["median_price"] = float(df_p["price"].median())
        result["min_price"] = float(df_p["price"].min())
        result["max_price"] = float(df_p["price"].max())

    return result

def top_cheapest(df_f: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    return (
        df_f.dropna(subset=["price"])
           .sort_values("price", ascending=True)
           .head(n)[[
               "product_link", "product_brand", "product_model", "product_manuf_year",
               "department", "price", "product_fuel", "vehicle_category", "color", "product_mileage"
           ]]
    )