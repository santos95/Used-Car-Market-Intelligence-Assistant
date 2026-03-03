import streamlit as st
from src.rag import retrieve
from src.query_router import is_analytics_query, extract_entities
from src.analytics import load_data, filter_df, summarize_market, top_cheapest

st.title("🚗 Used Car Market Intelligence Assistant")

query = st.text_input("Ask a question about used cars:")
k = st.slider("Results (k)", 3, 10, 5)

@st.cache_data(show_spinner=False)
def get_df():
    return load_data()

def fmt(v, default="N/A"):
    if v is None:
        return default
    if isinstance(v, str) and not v.strip():
        return default
    return v

def fmt_km(v):
    if v is None:
        return "N/A"
    try:
        return f"{int(v):,}".replace(",", ".")
    except Exception:
        return str(v)

if st.button("Search") and query:
    # ROUTE
    if is_analytics_query(query):
        st.subheader("📊 Analytics result")

        df = get_df()
        filters = extract_entities(query, df)

        df_f = filter_df(
            df,
            brand=filters.get("brand"),
            model=filters.get("model"),
            year=filters.get("year"),
            location=filters.get("location"),
        )

        applied = {k: v for k, v in filters.items() if v is not None}
        if applied:
            st.caption(f"Applied filters: {applied}")

        summary = summarize_market(df_f)

        st.write(
            f"Listings found: **{summary['count_listings']}**  "
            f"(with price: **{summary['count_with_price']}**)"
        )

        if summary["count_with_price"] == 0:
            st.warning("No priced listings matched these filters. Try a different query.")
        else:
            st.write(
                f"- Average price: **{summary['avg_price']:.2f}**\n"
                f"- Median price: **{summary['median_price']:.2f}**\n"
                f"- Min price: **{summary['min_price']:.2f}**\n"
                f"- Max price: **{summary['max_price']:.2f}**"
            )

            st.markdown("#### Cheapest listings (sample)")
            st.dataframe(top_cheapest(df_f, n=5), use_container_width=True)

            if filters.get("year"):
                st.caption(f"Applied filter: year={filters['year']}")

        st.divider()

        st.caption("Tip: Next we’ll add extraction for brand/model/location so analytics can answer richer questions.")
    else:
        st.subheader("🔎 Retrieval (semantic search)")

        res = retrieve(query, k=k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]

        if not docs:
            st.warning("No matches found. Try a different query (brand, model, year, location, fuel, etc.).")
        else:
            for i, (d, m) in enumerate(zip(docs, metas), start=1):
                brand = fmt(m.get("brand", "")).title() if isinstance(m.get("brand"), str) else fmt(m.get("brand", ""))
                model = fmt(m.get("model", "")).title() if isinstance(m.get("model"), str) else fmt(m.get("model", ""))
                year = fmt(m.get("year", "N/A"))

                st.markdown(f"### #{i} — {brand} {model} {year}")

                price = fmt(m.get("price"))
                location = fmt(m.get("location"))
                transmission = fmt(m.get("transmission"))
                source = fmt(m.get("source"))
                ingestion_date = fmt(m.get("ingestion_date"))
                url = fmt(m.get("url") or m.get("listing_url"))

                mileage_km = m.get("mileage_km")
                fuel = fmt(m.get("fuel"))
                category = fmt(m.get("category"))
                color = fmt(m.get("color"))

                st.caption(
                    f"Price: {price} | Location: {location} | Transmission: {transmission} | "
                    f"Mileage: {fmt_km(mileage_km)} km | Fuel: {fuel} | Category: {category} | Color: {color}"
                )
                st.caption(f"Source: {source} | Ingestion date: {ingestion_date}")

                if url != "N/A":
                    st.write(f"URL: {url}")

                with st.expander("Show indexed text"):
                    st.write(d)

                st.divider()