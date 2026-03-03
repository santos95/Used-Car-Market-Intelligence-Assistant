import os
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
    "ingestion_date"
]

# Read ONLY header
df = pd.read_csv(DATA_PATH, usecols=REQUIRED_COLUMNS)

df_head = pd.read_csv(DATA_PATH, nrows=0, encoding="utf-8", sep=",")
print("Columns found:", df_head.columns.tolist())
print("Total columns:", len(df_head.columns))