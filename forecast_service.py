# forecast_service.py

import zipfile
import os
import tempfile
import json
import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
import traceback
from calendar import month_abbr
from datetime import datetime

# === Month mapping for filename → date conversion
month_map = {abbr: f"{i:02d}" for i, abbr in enumerate(month_abbr) if abbr}

# === (Optional) KPI reasons dictionary for summaries or annotations
kpi_reasons = {
    "Call Completion Rate": ["Congestion", "Dropped handover", "High user traffic"],
    "Drop call rate": ["Weak signal", "Tower issue", "Interference"],
    "Block call rate": ["All channels busy", "Call setup delay"],
}

def extract_date_from_filename(filename: str) -> str | None:
    """
    Extract a YYYY-MM-01 date string from filenames like 'Jan2023.xlsx'.
    Returns None if no match.
    """
    name = os.path.basename(filename)
    base, _ext = os.path.splitext(name)
    match = pd.Series([base]).str.extract(r'([A-Za-z]{3})(\d{4})')
    if not match.isnull().values.any():
        mon, year = match.iloc[0]
        mm = month_map.get(mon.capitalize())
        if mm:
            return f"{year}-{mm}-01"
    return None

"""
def forecast_kpi(
    df: pd.DataFrame,
    country: str,
    tech: str,
    zone: str,
    kpi: str,
    forecast_months: int
):
    """
    Filters df by the given identifiers, fits Prophet, returns (fig, summary, error).
    """
    try:
        # Exact-match filtering
        filtered = df[
            (df['Country'] == country) &
            (df['Technology'] == tech) &
            (df['Zone'] == zone) &
            (df['KPI'] == kpi)
        ]
        if filtered.empty:
            return None, None, "No data available for the selected inputs"

        # Our actual value column in these sheets
        value_col = 'Actual Value MAPS Networks'
        if value_col not in filtered.columns:
            return None, None, f"Expected column '{value_col}' not found"

        # Build time series
        ts = (
            filtered
            .groupby('Date')[value_col]
            .mean()
            .reset_index()
            .rename(columns={'Date': 'ds', value_col: 'y'})
        )

        # Fit Prophet
        model = Prophet()
        model.fit(ts)

        # Forecast forward
        future = model.make_future_dataframe(periods=forecast_months, freq='MS')
        forecast = model.predict(future)

        # Build Plotly figure
        fig = go.Figure([
            go.Scatter(x=ts['ds'], y=ts['y'], mode='lines+markers', name='Actual'),
            go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Forecast'),
            go.Scatter(
                x=forecast['ds'], y=forecast['yhat_upper'],
                mode='lines', name='Upper Bound', line=dict(dash='dot')
            ),
            go.Scatter(
                x=forecast['ds'], y=forecast['yhat_lower'],
                mode='lines', name='Lower Bound', line=dict(dash='dot')
            ),
        ])
        fig.update_layout(
            title=f"Forecast for {kpi} — {zone} | {tech} | {country}",
            xaxis_title="Date",
            yaxis_title=kpi,
        )

        # Summary lines (last N forecast points)
        tail = forecast[['ds', 'yhat']].tail(forecast_months)
        summary = "\n".join(
            f"{row['ds'].date()}: {row['yhat']:.2f}"
            for _, row in tail.iterrows()
        )

        return fig, summary, None

    except Exception as e:
        return None, None, f"Forecast failed: {e}\n{traceback.format_exc()}"

"""



def forecast_kpi(
    df: pd.DataFrame,
    country: str,
    tech: str,
    zone: str,
    kpi: str,
    forecast_months: int
):
    """
    Filters df by the given identifiers, fits Prophet, returns (fig, summary, error).
    """
    try:
        # Exact-match filtering
        filtered = df[
            (df['Country'] == country) &
            (df['Technology'] == tech) &
            (df['Zone'] == zone) &
            (df['KPI'] == kpi)
        ]
        if filtered.empty:
            return None, None, "No data available for the selected inputs"

        value_col = 'Actual Value MAPS Networks'
        if value_col not in filtered.columns:
            return None, None, f"Expected column '{value_col}' not found"

        # Prepare time series for Prophet
        ts = (
            filtered
            .groupby('Date')[value_col]
            .mean()
            .reset_index()
            .rename(columns={'Date': 'ds', value_col: 'y'})
        )
        ts['ds'] = pd.to_datetime(ts['ds'])

        # Train Prophet
        model = Prophet()
        model.fit(ts)

        # Forecast into future
        future = model.make_future_dataframe(periods=forecast_months, freq='MS')
        forecast = model.predict(future)

        # Filter only future forecast for plotting
        last_actual_date = ts['ds'].max()
        forecast_future = forecast[forecast['ds'] > last_actual_date]

        # Plotting
        fig = go.Figure()

        # Actual values
        fig.add_trace(go.Scatter(x=ts['ds'], y=ts['y'], mode='lines+markers', name='Actual'))

        # Forecasted values
        fig.add_trace(go.Scatter(x=forecast_future['ds'], y=forecast_future['yhat'], mode='lines', name='Forecast'))

        # Upper and lower bounds
        fig.add_trace(go.Scatter(
            x=forecast_future['ds'], y=forecast_future['yhat_upper'],
            mode='lines', name='Upper Bound', line=dict(dash='dot')
        ))
        fig.add_trace(go.Scatter(
            x=forecast_future['ds'], y=forecast_future['yhat_lower'],
            mode='lines', name='Lower Bound', line=dict(dash='dot')
        ))

        # Optional: Vertical line for forecast start
        fig.add_vline(
            x=last_actual_date,
            line=dict(color="gray", dash="dash"),
            annotation_text="Forecast starts",
            annotation_position="top right"
        )

        # Layout
        fig.update_layout(
            title=f"Forecast for {kpi} — {zone} | {tech} | {country}",
            xaxis_title="Date",
            yaxis_title=kpi,
            template="plotly_white"
        )

        # Summary text for forecast
        tail = forecast_future[['ds', 'yhat']].tail(forecast_months)
        summary = "\n".join(
            f"{row['ds'].date()}: {row['yhat']:.2f}"
            for _, row in tail.iterrows()
        )

        return fig, summary, None

    except Exception as e:
        return None, None, f"Forecast failed: {e}\n{traceback.format_exc()}"


def run_forecast_pipeline(
    zip_buffer: bytes,
    country: str,
    tech: str,
    zone: str,
    kpi: str,
    forecast_months: int = 3
):
    """
    1. Extracts the uploaded ZIP into a single TemporaryDirectory.
    2. Reads all .xlsx/.xls files into DataFrames, adding 'Date' & 'source_file'.
    3. Concatenates them, then calls forecast_kpi().
    4. Returns (plot_json, summary, error_msg).
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # → Write the raw ZIP bytes
            zip_path = os.path.join(tmpdir, "upload.zip")
            with open(zip_path, "wb") as f:
                f.write(zip_buffer)

            # → Extract all excels
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(tmpdir)

            # → Locate Excel files
            excel_files = []
            for root, _, files in os.walk(tmpdir):
                for fn in files:
                    if fn.lower().endswith((".xlsx", ".xls")):
                        excel_files.append(os.path.join(root, fn))

            if not excel_files:
                return None, None, "No Excel files found in ZIP archive"

            # → Read and assemble
            records = []
            for path in excel_files:
                try:
                    df = pd.read_excel(path)
                    # clean column names
                    df.columns = df.columns.str.strip()
                    date_str = extract_date_from_filename(path)
                    if date_str:
                        df['Date'] = pd.to_datetime(date_str)
                        df['source_file'] = os.path.basename(path)
                        records.append(df)
                except Exception:
                    continue

            if not records:
                return None, None, "No valid data found in Excel files"

            df_all = pd.concat(records, ignore_index=True)

            # → Forecast
            fig, summary, err = forecast_kpi(
                df_all, country, tech, zone, kpi, forecast_months
            )
            if err:
                return None, None, err

            # ← NEW: emit pure JSON
            plot_json_str = fig.to_json()            # JSON string
            plot_json = json.loads(plot_json_str)    # pure Python dict

            return plot_json, summary, None

    except Exception as e:
        return None, None, f"Pipeline error: {e}\n{traceback.format_exc()}"
