import os
from datetime import date, timedelta

import httpx
import pandas as pd
import streamlit as st


def get_api_base_url() -> str:
    # Local default if env var is not set
    return os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=30)
def fetch_kpis(api_base_url: str, start: date, end: date):
    url = f"{api_base_url}/api/kpis/"
    params = {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    r = httpx.get(url, params=params, timeout=20.0)
    r.raise_for_status()
    return r.json()


def main():
    # ---------------- UI SETUP ----------------
    st.set_page_config(page_title="Health Metrics Hub", layout="wide")
    st.title("Health Metrics Hub — KPIs Dashboard")

    api_base_url = get_api_base_url()

    # ---------------- SIDEBAR ----------------
    with st.sidebar:
        st.header("Settings")
        st.caption("API base URL")
        st.code(api_base_url)

        today = date.today()
        default_start = today - timedelta(days=30)

        start = st.date_input("Start date", value=default_start)
        end = st.date_input("End date", value=today)

        if start > end:
            st.error("Start date must be before end date.")
            st.stop()

        reload_btn = st.button("Reload")

    # ---------------- DATA FETCH ----------------
    try:
        if reload_btn:
            st.cache_data.clear()

        data = fetch_kpis(api_base_url, start, end)

    except httpx.HTTPError as e:
        st.error("Could not fetch KPIs from the API.")
        st.write("Details:", str(e))
        st.stop()

    if not data:
        st.warning("No KPI records returned for this date range.")
        return

    # ---------------- DATAFRAME ----------------
    df = pd.DataFrame(data)

    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce").dt.date
    df = df.sort_values("date").reset_index(drop=True)

    latest = df.iloc[-1]

    # ---------------- LATEST SNAPSHOT ----------------
    st.subheader(f"Latest snapshot — {latest['date']}")

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("Weight 7d avg (kg)", f"{latest.get('weight_7d_avg', 0):.2f}")
    c2.metric("Balance 7d avg (kcal)", f"{latest.get('balance_7d_average', 0):.0f}")
    c3.metric("Balance today (kcal)", f"{latest.get('balance_kcal', 0):.0f}")
    c4.metric("Protein / kg", f"{latest.get('protein_per_kg', 0):.2f}")
    c5.metric("Healthy food %", f"{latest.get('healthy_food_pct', 0):.1f}")
    c6.metric(
        "Steps met",
        "✅" if int(latest.get("adherence_steps", 0) or 0) == 1 else "❌",
    )

    st.divider()

    # ---------------- CHARTS ----------------
    st.subheader("Trends")

    col1, col2 = st.columns(2)

    with col1:
        st.caption("Weight trend (7d avg)")
        st.line_chart(df.set_index("date")[["weight_7d_avg"]])

        st.caption("Healthy food %")
        st.line_chart(df.set_index("date")[["healthy_food_pct"]])

    with col2:
        st.caption("Energy balance (7d avg)")
        st.line_chart(df.set_index("date")[["balance_7d_average"]])

        st.caption("Protein per kg")
        st.line_chart(df.set_index("date")[["protein_per_kg"]])

    st.divider()

    # ---------------- TABLE ----------------
    st.subheader("KPIs (table)")
    st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
