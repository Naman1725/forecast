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
from typing import Optional  # ✅ Python 3.9-compatible typing

# === Month mapping for filename → date conversion
month_map = {abbr: f"{i:02d}" for i, abbr in enumerate(month_abbr) if abbr}

# ✅ Use Optional[str] instead of str | None for Python 3.9
def extract_date_from_filename(filename: str) -> Optional[str]:
    name = os.path.basename(filename)
    base, _ = os.path.splitext(name)
    match = pd.Series([base]).str.extract(r'([A-Za-z]{3})(\d{4})')
    if not match.isnull().values.any():
        mon, year = match.iloc[0]
        mm = month_map.get(mon.capitalize())
        if mm:
            return f"{year}-{mm}-01"
    return None

# === (Optional) KPI reasons dictionary for summaries or annotations
kpi_reasons = {
    "Call Completion Rate": ["Congestion", "Dropped handover", "High user traffic"],
    "Drop call rate": ["Weak signal", "Tower issue", "Interference"],
    "Block call rate": ["All channels busy", "Call setup delay"],
}


def forecast_kpi(
    df: pd.DataFrame,
    country: str,
    tech: str,
    zone: str,
    kpi: str,
    forecast_months: int
):
    try:
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

        ts = (
            filtered
            .groupby('Date')[value_col]
            .mean()
            .reset_index()
            .rename(columns={'Date': 'ds', value_col: 'y'})
        )

        model = Prophet()
        model.fit(ts)

        future = model.make_future_dataframe(periods=forecast_months, freq='MS')
        forecast = model.predict(future)

        # Only include forecast after the last actual date
        last_actual_date = ts['ds'].max()
        forecast_future = forecast[forecast['ds'] > last_actual_date].head(forecast_months)

        fig = go.Figure([
            go.Scatter(x=ts['ds'], y=ts['y'], mode='lines+markers', name='Actual'),
            go.Scatter(x=forecast_future['ds'], y=forecast_future['yhat'], mode='lines', name='Forecast'),
            go.Scatter(
                x=forecast_future['ds'], y=forecast_future['yhat_upper'],
                mode='lines', name='Upper Bound', line=dict(dash='dot')
            ),
            go.Scatter(
                x=forecast_future['ds'], y=forecast_future['yhat_lower'],
                mode='lines', name='Lower Bound', line=dict(dash='dot')
            ),
        ])
        fig.update_layout(
            title=f"Forecast for {kpi} — {zone} | {tech} | {country}",
            xaxis_title="Date",
            yaxis_title=kpi,
        )

        summary = "\n".join(
            f"{row['ds'].date()}: {row['yhat']:.2f}"
            for _, row in forecast_future.iterrows()
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
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "upload.zip")
            with open(zip_path, "wb") as f:
                f.write(zip_buffer)

            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(tmpdir)

            excel_files = []
            for root, _, files in os.walk(tmpdir):
                for fn in files:
                    if fn.lower().endswith((".xlsx", ".xls")):
                        excel_files.append(os.path.join(root, fn))

            if not excel_files:
                return None, None, "No Excel files found in ZIP archive"

            records = []
            for path in excel_files:
                try:
                    df = pd.read_excel(path)
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

            fig, summary, err = forecast_kpi(
                df_all, country, tech, zone, kpi, forecast_months
            )
            if err:
                return None, None, err

            plot_json_str = fig.to_json()
            plot_json = json.loads(plot_json_str)

            return plot_json, summary, None

    except Exception as e:
        return None, None, f"Pipeline error: {e}\n{traceback.format_exc()}"
