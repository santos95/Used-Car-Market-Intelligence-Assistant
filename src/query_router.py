import re
import unicodedata
from typing import Optional

ANALYTICS_KEYWORDS = [
    "average", "avg", "mean", "median",
    "count", "how many", "number of",
    "min", "minimum", "max", "maximum",
    "cheapest", "most expensive", "price range", "range",
    "trend", "over time"
]

def is_analytics_query(q: str) -> bool:
    ql = q.lower()
    return any(k in ql for k in ANALYTICS_KEYWORDS)

def extract_year(q: str) -> Optional[int]:
    # match 4-digit year 1990-2039-ish
    m = re.search(r"\b(19[9]\d|20[0-3]\d)\b", q)
    return int(m.group(0)) if m else None

def _norm(s: str) -> str:
    """Lowercase, remove accents, keep letters/digits/spaces."""
    s = s.strip().lower()
    s = "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _find_best_match(query_norm: str, candidates: list[str]) -> Optional[str]:
    """
    Returns the longest candidate that appears as a whole-word substring in query_norm.
    candidates are expected already normalized.
    """
    best = None
    best_len = 0

    # longest-first helps avoid matching "san" before "san jose"
    for c in sorted(set(candidates), key=len, reverse=True):
        if not c:
            continue
        # word boundary-ish: match as token sequence
        pattern = r"(?:^|\s)" + re.escape(c) + r"(?:$|\s)"
        if re.search(pattern, query_norm):
            if len(c) > best_len:
                best = c
                best_len = len(c)

    return best

def extract_entities(query: str, df) -> dict:
    """
    Extracts entities using lists derived from the dataset:
    - brand (df['brand'])
    - model (df['model'])
    - location (df['location'])

    Returns canonical values as stored in df (already normalized lower-case in analytics.load_data()).
    """
    qn = _norm(query)

    # candidate lists from df (already normalized in analytics.load_data())
    brands = [b for b in df["brand"].dropna().unique().tolist() if isinstance(b, str)]
    models = [m for m in df["model"].dropna().unique().tolist() if isinstance(m, str)]
    locations = [l for l in df["location"].dropna().unique().tolist() if isinstance(l, str)]

    # normalize candidates to match query normalization
    brands_n = [_norm(b) for b in brands]
    models_n = [_norm(m) for m in models]
    locations_n = [_norm(l) for l in locations]

    brand_match_n = _find_best_match(qn, brands_n)
    location_match_n = _find_best_match(qn, locations_n)

    # For model: optionally prefer models belonging to the matched brand
    if brand_match_n:
        # map back to original df normalized form
        brand_val = brands[brands_n.index(brand_match_n)]
        models_subset = df[df["brand"] == brand_val]["model"].dropna().unique().tolist()
        models_subset_n = [_norm(m) for m in models_subset]
        model_match_n = _find_best_match(qn, models_subset_n)
        model_val = models_subset[models_subset_n.index(model_match_n)] if model_match_n else None
    else:
        model_match_n = _find_best_match(qn, models_n)
        model_val = models[models_n.index(model_match_n)] if model_match_n else None
        brand_val = None

    location_val = locations[locations_n.index(location_match_n)] if location_match_n else None

    return {
        "brand": brand_val,
        "model": model_val,
        "location": location_val,
        "year": extract_year(query),
    }