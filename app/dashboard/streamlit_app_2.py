import os
from datetime import date
from pathlib import Path

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


# ---------------- API HELPERS ----------------

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


# ---------------- UI HELPERS ----------------

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


def count_missing_days(df_dates: pd.Series) -> int:
    if df_dates.empty:
        return 0
    dmin = min(df_dates)
    dmax = max(df_dates)
    full = pd.date_range(dmin, dmax, freq="D").date
    present = set(df_dates)
    return sum(1 for d in full if d not in present)


def build_dataframe(data: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(data)

    if "date" not in df.columns:
        raise ValueError("API response has no 'date' field.")

    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce").dt.date
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    if df.empty:
        raise ValueError("All records had invalid dates.")

    return df


def prepare_plot_df(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    df_plot = df.copy()
    for col in df_plot.columns:
        if col != "date":
            df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce")
    df_plot = df_plot.set_index("date")
    numeric_cols = df_plot.select_dtypes(include="number").columns.tolist()
    return df_plot, numeric_cols


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


def render_pipeline_overview(api_base_url: str):
    st.markdown(
        """
        ### What this app demonstrates

        This demo shows an end-to-end analytics pipeline:

        1. Upload a daily health metrics CSV  
        2. Backend validates and persists the input  
        3. KPI calculations run server-side  
        4. Streamlit fetches persisted KPIs from the API and visualizes them

        The dashboard is a client of the API, not a direct database reader.
        """
    )
    st.info(
        f"API base URL: {api_base_url}\n\n"
        f"Upload endpoint: {api_base_url}/api/upload-csv\n\n"
        f"KPI endpoint: {api_base_url}/api/kpis/"
    )


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
                use_container_width=True,
            )
            return

    st.caption("Sample CSV not found locally in this deployment.")


def render_dataset_status(df: pd.DataFrame, requested_start: date, requested_end: date):
    total_records = len(df)
    dataset_min = df["date"].min()
    dataset_max = df["date"].max()
    missing_days = count_missing_days(df["date"])
    total_kpis = max(0, len(df.columns) - 1)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total records", total_records)
    col2.metric("Dataset range", f"{dataset_min} → {dataset_max}")
    col3.metric("Missing days", missing_days)
    col4.metric("KPI columns", total_kpis)

    st.caption(
        f"Current query window: {requested_start.isoformat()} → {requested_end.isoformat()}"
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


def render_overview_tab(df: pd.DataFrame, df_plot: pd.DataFrame, numeric_cols: list[str], requested_start: date, requested_end: date):
    render_dataset_status(df, requested_start, requested_end)
    st.divider()
    render_latest_snapshot(df, df_plot)
    st.divider()

    st.subheader("Main trends")

    preferred = [
        "weight_7d_avg",
        "balance_7d_average",
        "protein_per_kg",
        "healthy_food_pct",
    ]
    overview_cols = [c for c in preferred if c in numeric_cols]

    if overview_cols:
        st.line_chart(df_plot[overview_cols], use_container_width=True)
    elif numeric_cols:
        st.line_chart(df_plot[numeric_cols[:4]], use_container_width=True)
    else:
        st.warning("No numeric KPI columns to plot.")

    st.divider()
    st.subheader("Latest records")
    st.dataframe(df.tail(10), use_container_width=True)


def render_upload_tab(api_base_url: str):
    st.subheader("Upload CSV to the API")
    st.write(
        "Use this page to test the ingestion pipeline directly from the UI. "
        "The file is sent to the existing backend upload endpoint."
    )

    try_render_sample_csv_download()

    with st.expander("Expected flow", expanded=False):
        st.markdown(
            """
            - Select a CSV file
            - Send it to `POST /api/upload-csv`
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

        if st.button("Upload and process CSV", type="primary", use_container_width=True):
            with st.spinner("Uploading file and waiting for the API response..."):
                try:
                    result = upload_csv(api_base_url, uploaded_file.name, file_bytes)

                    st.success("Data successfully ingested and KPIs recomputed.")
                    st.info(
                        """
Your CSV has been:
- validated
- persisted in PostgreSQL
- used to recompute KPIs

Refreshing data automatically...
                        """
                    )

                    render_upload_result(result)

                    st.session_state["upload_success_message"] = (
                        f"Latest upload processed successfully: {uploaded_file.name}"
                    )
                    st.session_state["reload_after_upload"] = True
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


def render_dashboard_tab(df: pd.DataFrame, df_plot: pd.DataFrame, numeric_cols: list[str], requested_start: date, requested_end: date):
    st.subheader("Export data")

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download KPIs as CSV",
        data=csv_data,
        file_name=f"kpis_{requested_start.isoformat()}_{requested_end.isoformat()}.csv",
        mime="text/csv",
    )

    st.divider()
    st.caption("Dashboard data reflects the latest successfully ingested CSV data.")

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

    st.subheader("Trends (choose KPIs)")

    if not numeric_cols:
        st.warning("No numeric KPI columns to plot.")
    else:
        default_cols = [
            c for c in [
                "weight_7d_avg",
                "balance_7d_average",
                "protein_per_kg",
                "healthy_food_pct",
            ]
            if c in numeric_cols
        ]

        selected = st.multiselect(
            "Select KPIs to plot",
            options=numeric_cols,
            default=default_cols if default_cols else numeric_cols[:6],
        )

        if selected:
            st.line_chart(df_plot[selected], use_container_width=True)
        else:
            st.info("Select at least one KPI to plot.")

    st.divider()
    st.subheader("KPIs (table)")
    st.dataframe(df, use_container_width=True)


def render_architecture_tab(api_base_url: str):
    st.subheader("Architecture")
    st.markdown(
        """
        ```text
        CSV file
           ↓
        Streamlit upload UI
           ↓
        FastAPI POST /api/upload-csv
           ↓
        Validation + persistence + KPI computation
           ↓
        FastAPI GET /api/kpis/
           ↓
        Streamlit dashboard
        ```
        """
    )

    st.markdown(
        """
        ### Why this demo is useful

        - It shows an API-first architecture
        - KPI computation stays in the backend
        - The frontend acts as a thin client
        - The same API can serve both Swagger and Streamlit
        """
    )

    st.markdown("### Useful links")
    st.code(f"{api_base_url}/docs")
    st.code(f"{api_base_url}/api/upload-csv")
    st.code(f"{api_base_url}/api/kpis/")


# ---------------- MAIN ----------------

def main():
    st.set_page_config(page_title="Health Metrics Hub", layout="wide")
    st.title("Health Metrics Hub")
    st.caption("Portfolio analytics demo: CSV ingestion → persisted KPIs → interactive dashboard")

    api_base_url = get_api_base_url()

    if "reload_after_upload" not in st.session_state:
        st.session_state["reload_after_upload"] = False

    if "upload_success_message" not in st.session_state:
        st.session_state["upload_success_message"] = None

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

        reload_btn = st.button("Reload data", use_container_width=True)

        st.divider()
        st.caption("Tip")
        st.write("Upload a CSV in the Upload tab. Data refreshes automatically after success.")

    if reload_btn:
        st.cache_data.clear()

    if st.session_state.get("upload_success_message"):
        st.success(st.session_state["upload_success_message"])
        st.session_state["upload_success_message"] = None

    render_pipeline_overview(api_base_url)

    try:
        data = fetch_kpis(api_base_url, start, end)
    except httpx.HTTPError as e:
        st.error("Could not fetch KPIs from the API.")
        st.write("Details:", str(e))

        tab_overview, tab_upload, tab_dashboard, tab_arch = st.tabs(
            ["Overview", "Upload CSV", "Dashboard", "Architecture"]
        )

        with tab_overview:
            st.warning("Overview unavailable until KPI data can be fetched.")

        with tab_upload:
            render_upload_tab(api_base_url)

        with tab_dashboard:
            st.warning("Dashboard unavailable until KPI data can be fetched.")

        with tab_arch:
            render_architecture_tab(api_base_url)

        return

    tab_overview, tab_upload, tab_dashboard, tab_arch = st.tabs(
        ["Overview", "Upload CSV", "Dashboard", "Architecture"]
    )

    if not data:
        with tab_overview:
            st.warning("No KPI records returned for this date range.")

        with tab_upload:
            render_upload_tab(api_base_url)

        with tab_dashboard:
            st.info("No KPI data available yet.")

        with tab_arch:
            render_architecture_tab(api_base_url)

        return

    try:
        df = build_dataframe(data)
        df_plot, numeric_cols = prepare_plot_df(df)
    except ValueError as e:
        st.error(str(e))
        return

    with tab_overview:
        render_overview_tab(df, df_plot, numeric_cols, start, end)

    with tab_upload:
        render_upload_tab(api_base_url)

    with tab_dashboard:
        render_dashboard_tab(df, df_plot, numeric_cols, start, end)

    with tab_arch:
        render_architecture_tab(api_base_url)


if __name__ == "__main__":
    main()