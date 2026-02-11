import os
from datetime import date, timedelta

import httpx
import pandas as pd
import streamlit as st


# ---------------- CONFIG / DISPLAY ----------------

KPI_META: dict[str, dict[str, object]] = {
    "weight_7d_avg": {"label": "Weight (7d avg)", "unit": "kg", "fmt": "{:.2f}"},
    "balance_7d_average": {"label": "Energy balance (7d avg)", "unit": "kcal/day", "fmt": "{:.0f}"},
    "balance_kcal": {"label": "Energy balance (today)", "unit": "kcal", "fmt": "{:.0f}"},
    "protein_per_kg": {"label": "Protein", "unit": "g/kg", "fmt": "{:.2f}"},
    "healthy_food_pct": {"label": "Healthy food", "unit": "%", "fmt": "{:.1f}"},
    "adherence_steps": {"label": "Steps met", "unit": "", "fmt": "{}"},
}


def get_api_base_url() -> str:
    return os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=30)
def fetch_kpis(api_base_url: str, start: date, end: date):
    url = f"{api_base_url}/api/kpis/"
    params = {"start_date": start.isoformat(), "end_date": end.isoformat()}
    r = httpx.get(url, params=params, timeout=20.0)
    r.raise_for_status()
    return r.json()


def prettify_kpi_name(col: str) -> str:
    meta = KPI_META.get(col)
    if meta and meta.get("label"):
        return str(meta["label"])
    return col.replace("_", " ").strip().title()


def format_value(col: str, value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"

    if col == "adherence_steps":
        try:
            return "✅" if int(value) == 1 else "❌"
        except Exception:
            return "—"

    meta = KPI_META.get(col, {})
    fmt = meta.get("fmt")
    unit = meta.get("unit", "")

    try:
        if fmt:
            s = fmt.format(float(value)) if "{}" not in str(fmt) else str(value)
        else:
            s = f"{float(value):.2f}"
    except Exception:
        s = str(value)

    return f"{s} {unit}".strip()


def compute_delta(df_plot: pd.DataFrame, col: str, rows_back: int = 7):
    """
    Delta between latest and value N valid rows back (not necessarily exact calendar days).
    """
    if col not in df_plot.columns:
        return None

    series = df_plot[col].dropna()
    if len(series) < 2:
        return None

    latest_val = series.iloc[-1]
    idx = max(0, len(series) - 1 - rows_back)
    past_val = series.iloc[idx]

    try:
        return float(latest_val) - float(past_val)
    except Exception:
        return None


def count_missing_days(df_dates: pd.Series) -> int:
    if df_dates.empty:
        return 0
    dmin = min(df_dates)
    dmax = max(df_dates)
    full = pd.date_range(dmin, dmax, freq="D").date
    present = set(df_dates)
    return sum(1 for d in full if d not in present)


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

    if "date" not in df.columns:
        st.error("API response has no 'date' field.")
        st.stop()

    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce").dt.date
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    if df.empty:
        st.warning("All records had invalid dates.")
        return

    # ---------------- TOP SUMMARY ROW ----------------
    # ---------------- EXPORT ----------------
    st.subheader("Export data")

    csv_data = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download KPIs as CSV",
        data=csv_data,
        file_name=f"kpis_{start.isoformat()}_{end.isoformat()}.csv",
        mime="text/csv",
    )

    st.divider()
    total_records = len(df)
    last_date = df["date"].max()
    missing_days = count_missing_days(df["date"])

    top1, top2, top3 = st.columns(3)
    top1.metric("Total records", total_records)
    top2.metric("Date range", f"{start.isoformat()} → {end.isoformat()}")
    top3.metric("Missing days", missing_days)

    st.divider()

    # ---------------- PREPARE PLOTTING DF ----------------
    df_plot = df.copy()
    for col in df_plot.columns:
        if col != "date":
            df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce")
    df_plot = df_plot.set_index("date")

    numeric_cols = df_plot.select_dtypes(include="number").columns.tolist()

    latest = df.iloc[-1]

    # ---------------- LATEST SNAPSHOT + DELTAS ----------------
    st.subheader(f"Latest snapshot — {latest['date']}")

    snapshot_cols = []
    for c in ["weight_7d_avg", "balance_7d_average", "balance_kcal", "protein_per_kg", "healthy_food_pct", "adherence_steps"]:
        if c in df_plot.columns:
            snapshot_cols.append(c)

    cols = st.columns(min(6, max(1, len(snapshot_cols))))
    for i, col in enumerate(snapshot_cols):
        label = prettify_kpi_name(col)
        val = latest.get(col, None)
        delta = compute_delta(df_plot, col, rows_back=7)

        if col == "adherence_steps":
            cols[i].metric(label, format_value(col, val))
            continue

        if delta is None or pd.isna(delta):
            cols[i].metric(label, format_value(col, val))
        else:
            unit = KPI_META.get(col, {}).get("unit", "")
            delta_str = f"{delta:+.2f} {unit}".strip() if abs(delta) < 100 else f"{delta:+.0f} {unit}".strip()
            cols[i].metric(label, format_value(col, val), delta_str)

    st.caption("Δ compares the latest value to the closest earlier value ~7 valid records back (not guaranteed exact calendar days).")
    st.divider()

    # ---------------- ALL KPI CHARTS (FIRST, NO TOGGLE) ----------------
    st.subheader("All KPI charts")

    if not numeric_cols:
        st.warning("No numeric KPI columns to plot.")
    else:
        charts_per_row = st.select_slider("Charts per row", options=[2, 3, 4], value=3)

        cols = st.columns(charts_per_row)
        for i, kpi in enumerate(numeric_cols):
            with cols[i % charts_per_row]:
                st.caption(prettify_kpi_name(kpi))
                st.line_chart(df_plot[[kpi]], use_container_width=True)

    st.divider()

    # ---------------- TRENDS (USER SELECT) ----------------
    st.subheader("Trends (choose KPIs)")

    if not numeric_cols:
        st.warning("No numeric KPI columns to plot.")
    else:
        default_cols = [c for c in ["weight_7d_avg", "balance_7d_average", "protein_per_kg", "healthy_food_pct"] if c in numeric_cols]
        selected = st.multiselect(
            "Select KPIs to plot",
            options=numeric_cols,
            default=default_cols if default_cols else numeric_cols[:6],
        )

        if selected:
            st.line_chart(df_plot[selected], use_container_width=True)
        else:
            st.info("Select at least one KPI to plot.")

    

    # ---------------- TABLE ----------------
    st.subheader("KPIs (table)")
    st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
