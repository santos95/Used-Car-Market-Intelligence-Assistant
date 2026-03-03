import os
import re
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(BASE_DIR, "data", "data.csv")
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma")
COLLECTION_NAME = "used_cars"

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
        # new fields to synthesize description
    "product_mileage",
    "product_fuel",
    "vehicle_category",
    "color",
    "option_features_en",
]

def safe_str(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()

def normalize_text(x: str) -> str:
    return safe_str(x).lower()

def clean_price_to_float(x):
    if pd.isna(x):
        return None
    s = re.sub(r"[^\d.]", "", str(x))
    try:
        return float(s) if s else None
    except:
        return None

def make_title(row):
    parts = [
        safe_str(row["product_brand"]),
        safe_str(row["product_model"]),
        safe_str(row["product_manuf_year"]),
        safe_str(row["product_transmission"]),
    ]
    return " ".join([p for p in parts if p]).strip()

def synth_description(row) -> str:
    mileage = safe_str(row.get("product_mileage"))
    fuel = safe_str(row.get("product_fuel"))
    category = safe_str(row.get("vehicle_category"))
    color = safe_str(row.get("color"))
    features = safe_str(row.get("option_features_en"))

    parts = []
    if mileage:
        parts.append(f"Mileage: {mileage} km")
    if fuel:
        parts.append(f"Fuel: {fuel}")
    if category:
        parts.append(f"Category: {category}")
    if color:
        parts.append(f"Color: {color}")
    if features:
        parts.append(f"Features: {features}")

    return " | ".join(parts).strip()

def make_doc(row):
    title = make_title(row)
    synthetic = synth_description(row)

    return (
        f"{title}\n"
        f"Brand: {safe_str(row['product_brand'])}\n"
        f"Model: {safe_str(row['product_model'])}\n"
        f"Year: {safe_str(row['product_manuf_year'])}\n"
        f"Transmission: {safe_str(row['product_transmission'])}\n"
        f"Price: {clean_price_to_float(row['clean_price'])}\n"
        f"Location: {safe_str(row['department'])}\n"
        f"Source: {safe_str(row['source'])}\n"
        f"Ingestion date: {safe_str(row['ingestion_date'])}\n"
        f"Details: {synthetic}\n"
        f"URL: {safe_str(row['product_link'])}"
        
    )

def main():
    print("Reading CSV from:", DATA_PATH)

    df = pd.read_csv(DATA_PATH, usecols=REQUIRED_COLUMNS)

    df = df.dropna(subset=["product_link"]).copy()
    df = df.drop_duplicates(subset=["product_link"])

    print("Rows loaded:", len(df))

    ids = df["product_link"].astype(str).tolist()
    docs = [make_doc(r) for _, r in df.iterrows()]

    metadatas = []
    for _, r in df.iterrows():
        metadatas.append({
            "brand": normalize_text(r["product_brand"]),
            "model": normalize_text(r["product_model"]),
            "year": int(r["product_manuf_year"]) if pd.notna(r["product_manuf_year"]) else None,
            "location": normalize_text(r["department"]),
            "price": clean_price_to_float(r["clean_price"]),
            "source": normalize_text(r["source"]),
            "ingestion_date": safe_str(r["ingestion_date"]),
            "transmission": normalize_text(r["product_transmission"]),
            "url": safe_str(r["product_link"]),
            "mileage": safe_str(r.get("product_mileage")),
            "fuel": normalize_text(r.get("product_fuel")),
            "category": normalize_text(r.get("vehicle_category")),
            "color": normalize_text(r.get("color")),
            "features": safe_str(r.get("option_features_en")),
        })

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        client.delete_collection(COLLECTION_NAME)
    except:
        pass

    col = client.get_or_create_collection(name=COLLECTION_NAME)

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embs = model.encode(docs, show_progress_bar=True).tolist()

    col.add(ids=ids, documents=docs, metadatas=metadatas, embeddings=embs)

    print(f"✅ Indexed {len(docs)} listings into Chroma")

if __name__ == "__main__":
    main()