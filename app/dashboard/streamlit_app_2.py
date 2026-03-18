import os
import time
from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import streamlit as st


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


def upload_csv(api_base_url: str, file_name: str, file_bytes: bytes):
    url = f"{api_base_url}/api/upload-csv"
    files = {"file": (file_name, file_bytes, "text/csv")}
    r = httpx.post(url, files=files, timeout=60.0)
    r.raise_for_status()

    try:
        return r.json()
    except Exception:
        return {"status_code": r.status_code, "raw_response": r.text}


def count_missing_days(df_dates: pd.Series) -> int:
    if df_dates.empty:
        return 0
    dmin = min(df_dates)
    dmax = max(df_dates)
    full = pd.date_range(dmin, dmax, freq="D").date
    present = set(df_dates)
    return sum(1 for d in full if d not in present)


@st.cache_data(ttl=30)
def build_dataframe_cached(data: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(data)

    if "date" not in df.columns:
        raise ValueError("API response has no 'date' field.")

    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce").dt.date
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    if df.empty:
        raise ValueError("All records had invalid dates.")

    return df


@st.cache_data(ttl=30)
def prepare_plot_df_cached(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    df_plot = df.copy()
    for col in df_plot.columns:
        if col != "date":
            df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce")
    df_plot = df_plot.set_index("date")
    numeric_cols = df_plot.select_dtypes(include="number").columns.tolist()
    return df_plot, numeric_cols


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


def render_upload_result(result: object):
    st.subheader("Ingestion result")

    if isinstance(result, dict):
        primitive_items = {
            k: v for k, v in result.items()
            if isinstance(v, (str, int, float, bool)) or v is None
        }

        if primitive_items:
            cols = st.columns(min(4, max(1, len(primitive_items))))
            for i, (k, v) in enumerate(primitive_items.items()):
                cols[i % len(cols)].metric(
                    k.replace("_", " ").title(),
                    str(v) if v is not None else "—"
                )

        nested_items = {
            k: v for k, v in result.items()
            if isinstance(v, (list, dict))
        }

        if nested_items:
            st.markdown("**Full response**")
            st.json(result)
    else:
        st.json(result)


def try_render_sample_csv_download():
    possible_paths = [
        Path("samples/sample_data.csv"),
        Path(__file__).resolve().parent.parent.parent / "samples" / "sample_data.csv",
        Path(__file__).resolve().parent / "samples" / "sample_data.csv",
    ]

    for path in possible_paths:
        if path.exists() and path.is_file():
            data = path.read_bytes()
            st.download_button(
                label="Download sample CSV",
                data=data,
                file_name="sample_data.csv",
                mime="text/csv",
                width="stretch",
            )
            return

    st.caption("Sample CSV not found locally in this deployment.")


def render_info_tab(api_base_url: str):
    left, right = st.columns(2)

    with left:
        st.subheader("How to use this app")
        st.markdown(
            """
            This app lets you test the full health analytics workflow from ingestion to visualization.

            **How to use it:**
            - Go to **Upload CSV**
            - Upload a daily health metrics CSV
            - The backend validates, persists, and computes KPIs
            - Go to **Dashboard** to inspect the resulting KPI charts

            The dashboard is a client of the API, not a direct database reader.
            """
        )
        st.caption(f"Swagger: {api_base_url}/docs")

    with right:
        st.subheader("Architecture")
        st.markdown(
            """
            ```text
            CSV file
               ↓
            Streamlit upload UI
               ↓
            FastAPI backend
               ↓
            Validation + persistence + KPI computation
               ↓
            Streamlit dashboard
            ```
            """
        )

        st.markdown(
            """
            - API-first architecture  
            - KPI computation stays in the backend  
            - Frontend acts as a thin client  
            - Same backend powers both Swagger and Streamlit
            """
        )


def render_latest_snapshot(df: pd.DataFrame, df_plot: pd.DataFrame):
    latest = df.iloc[-1]
    st.subheader(f"Latest snapshot — {latest['date']}")

    snapshot_cols = [
        c for c in [
            "weight_7d_avg",
            "balance_7d_average",
            "balance_kcal",
            "protein_per_kg",
            "healthy_food_pct",
            "adherence_steps",
        ]
        if c in df_plot.columns
    ]

    if not snapshot_cols:
        st.info("No snapshot KPI columns available.")
        return

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

    st.caption(
        "Δ compares the latest value to the closest earlier value "
        "~7 valid records back (not guaranteed exact calendar days)."
    )


def render_dataset_summary(df: pd.DataFrame, requested_start: date, requested_end: date):
    total_records = len(df)
    dataset_min = df["date"].min()
    dataset_max = df["date"].max()
    missing_days = count_missing_days(df["date"])
    total_kpis = max(0, len(df.columns) - 1)

    st.subheader("Dataset summary")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total records", total_records)
    c2.metric("Dataset range", f"{dataset_min} → {dataset_max}")
    c3.metric("Missing days", missing_days)
    c4.metric("KPI columns", total_kpis)

    st.caption(
        f"Query window: {requested_start.isoformat()} → {requested_end.isoformat()}"
    )


def render_dashboard_tab(
    df: pd.DataFrame,
    df_plot: pd.DataFrame,
    numeric_cols: list[str],
    requested_start: date,
    requested_end: date,
):
    render_dataset_summary(df, requested_start, requested_end)
    st.divider()
    render_latest_snapshot(df, df_plot)
    st.divider()

    st.caption("Dashboard data reflects the latest successfully ingested CSV data.")

    if not numeric_cols:
        st.warning("No numeric KPI columns to plot.")
        return

    charts_per_row = st.select_slider("Charts per row", options=[2, 3, 4], value=3)
    cols = st.columns(charts_per_row)

    for i, kpi in enumerate(numeric_cols):
        with cols[i % charts_per_row]:
            st.caption(prettify_kpi_name(kpi))
            st.line_chart(df_plot[[kpi]], width="stretch")


def render_upload_tab(api_base_url: str):
    st.subheader("Upload CSV")
    st.write(
        "Use this page to test the ingestion pipeline directly from the UI. "
        "The file is sent to the backend upload endpoint."
    )

    try_render_sample_csv_download()

    with st.expander("Expected flow", expanded=False):
        st.markdown(
            """
            - Select a CSV file
            - Send it to the backend
            - Backend parses, validates, persists, and computes KPIs
            - The dashboard refreshes automatically after a successful upload
            """
        )

    uploaded_file = st.file_uploader("Select CSV file", type=["csv"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()

        col1, col2 = st.columns([1, 1])
        col1.metric("File name", uploaded_file.name)
        col2.metric("Size (KB)", f"{len(file_bytes) / 1024:.1f}")

        preview_text = file_bytes[:1500].decode("utf-8", errors="ignore")
        with st.expander("Preview file content", expanded=False):
            st.code(preview_text or "(empty preview)", language="text")

        if st.button("Upload and process CSV", type="primary", width="stretch"):
            with st.spinner("Uploading file and waiting for the API response..."):
                try:
                    result = upload_csv(api_base_url, uploaded_file.name, file_bytes)

                    st.success("Data successfully ingested and KPIs recomputed.")
                    render_upload_result(result)

                    st.session_state["upload_success_message"] = (
                        f"Latest upload processed successfully: {uploaded_file.name}"
                    )
                    st.session_state["reload_after_upload"] = True
                    st.session_state["active_tab"] = "upload"
                    st.rerun()

                except httpx.HTTPStatusError as e:
                    st.error(f"Upload failed with status {e.response.status_code}.")
                    try:
                        st.json(e.response.json())
                    except Exception:
                        st.code(e.response.text)
                except httpx.HTTPError as e:
                    st.error("Could not connect to the upload endpoint.")
                    st.write("Details:", str(e))


def inject_tabs_css():
    st.markdown(
        """
        <style>
        button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] p {
            font-size: 1.08rem !important;
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_tabs(active_tab: str, api_base_url: str, df=None, df_plot=None, numeric_cols=None, start=None, end=None):
    if active_tab == "upload":
        tab_order = ["Upload CSV", "Dashboard", "Info"]
    else:
        tab_order = ["Info", "Dashboard", "Upload CSV"]

    tab1, tab2, tab3 = st.tabs(tab_order)

    for tab_name, tab in zip(tab_order, [tab1, tab2, tab3]):
        with tab:
            if tab_name == "Dashboard":
                if df is None or df_plot is None or numeric_cols is None:
                    st.warning("Dashboard unavailable until KPI data can be fetched.")
                else:
                    render_dashboard_tab(df, df_plot, numeric_cols, start, end)

            elif tab_name == "Info":
                render_info_tab(api_base_url)

            elif tab_name == "Upload CSV":
                render_upload_tab(api_base_url)


def main():
    st.set_page_config(page_title="Health Metrics Hub", layout="wide")
    st.title("Health Metrics Hub")
    st.caption("Portfolio analytics demo: CSV ingestion → persisted KPIs → interactive dashboard")

    inject_tabs_css()

    api_base_url = get_api_base_url()

    if "reload_after_upload" not in st.session_state:
        st.session_state["reload_after_upload"] = False

    if "upload_success_message" not in st.session_state:
        st.session_state["upload_success_message"] = None

    if "active_tab" not in st.session_state:
        st.session_state["active_tab"] = "dashboard"

    if st.session_state.get("reload_after_upload"):
        st.cache_data.clear()
        st.session_state["reload_after_upload"] = False

    with st.sidebar:
        st.header("Settings")
        st.caption("API base URL")
        st.code(api_base_url)

        default_start = date(2024, 1, 1)
        today = date.today()

        start = st.date_input("Start date", value=default_start)
        end = st.date_input("End date", value=today)

        if start > end:
            st.error("Start date must be before end date.")
            st.stop()

        reload_btn = st.button("Reload data", width="stretch")
        show_debug_timings = st.checkbox("Show debug timings", value=False)

        st.divider()
        st.caption("Tip")
        st.write("Upload a CSV in the Upload CSV tab. Data refreshes automatically after success.")

    if reload_btn:
        st.cache_data.clear()
        st.session_state["active_tab"] = "dashboard"

    if st.session_state.get("upload_success_message"):
        st.success(st.session_state["upload_success_message"])
        st.session_state["upload_success_message"] = None

    t_fetch_start = time.perf_counter()
    try:
        data = fetch_kpis(api_base_url, start, end)
    except httpx.HTTPError as e:
        st.error("Could not fetch KPIs from the API.")
        st.write("Details:", str(e))
        render_tabs(
            active_tab=st.session_state.get("active_tab", "dashboard"),
            api_base_url=api_base_url,
        )
        return

    fetch_seconds = time.perf_counter() - t_fetch_start

    if not data:
        st.info("No KPI data available for the selected date range.")
        render_tabs(
            active_tab=st.session_state.get("active_tab", "dashboard"),
            api_base_url=api_base_url,
        )
        return

    try:
        t_prepare_start = time.perf_counter()
        df = build_dataframe_cached(data)
        df_plot, numeric_cols = prepare_plot_df_cached(df)
        prepare_seconds = time.perf_counter() - t_prepare_start
    except ValueError as e:
        st.error(str(e))
        return

    if show_debug_timings:
        c1, c2 = st.columns(2)
        c1.metric("Fetch KPIs", f"{fetch_seconds:.3f}s")
        c2.metric("Prepare DataFrame", f"{prepare_seconds:.3f}s")
        st.divider()

    render_tabs(
        active_tab=st.session_state.get("active_tab", "dashboard"),
        api_base_url=api_base_url,
        df=df,
        df_plot=df_plot,
        numeric_cols=numeric_cols,
        start=start,
        end=end,
    )


if __name__ == "__main__":
    main()