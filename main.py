# main.py
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from forecast_service import run_forecast_pipeline

app = FastAPI(
    title="Telecom KPI Forecast Service",
    version="1.0.0",
    description="Upload a ZIP of monthly KPI Excel files + parameters, get back forecasts."
)

@app.post("/forecast", response_model=dict)
async def forecast(
    file: UploadFile = File(..., description="A ZIP file containing your KPI Excel workbooks"),
    country: str = Form(..., description="Country name to filter on"),
    tech: str = Form(..., description="Technology filter, e.g. '4G'"),
    zone: str = Form(..., description="Zone name, e.g. 'North'"),
    kpi: str = Form(..., description="KPI to forecast, e.g. 'Call Completion Rate'"),
    forecast_months: Optional[int] = Form(3, ge=1, le=12, description="How many months to forecast (1–12)")
):
    # read bytes
    body = await file.read()
    plot_json, summary, error = run_forecast_pipeline(body, country, tech, zone, kpi, forecast_months)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"plot": plot_json, "summary": summary}

@app.get("/health", response_model=dict)
async def health():
    return {"status": "ok"}
