
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
import pandas as pd
from typing import List

from models import CalculateRequest, CalculateResponse, ScheduleRow
from ipa_engine.engine import IPAInputs, TSFItem, TSFConfig, InsurancePolicy, build_schedule
from utils_export import schedule_to_xlsx_bytes, schedule_to_pdf_bytes

app = FastAPI(title="IPA API", version="1.0.0")

# CORS for local Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _to_inputs(m: CalculateRequest) -> IPAInputs:
    cfg = TSFConfig(**m.tsf.model_dump())
    ins = InsurancePolicy(**m.insurance.model_dump())
    items = [TSFItem(**x.model_dump()) for x in m.monthly_tsf]
    return IPAInputs(
        asset_net=m.asset_net, vat_rate=m.vat_rate, tenure_months=m.tenure_months,
        annual_rate=m.annual_rate, funding_rate=m.funding_rate, grace_months=m.grace_months,
        balloon_percent=m.balloon_percent, vendor_payment_date_T=m.vendor_payment_date_T,
        first_due_date_S=m.first_due_date_S, monthly_tsf=items, tsf=cfg, insurance=ins,
        vat_on_tsf=m.vat_on_tsf, vat_on_insurance=m.vat_on_insurance, round_decimals=m.round_decimals,
        solve_equilibrium=m.solve_equilibrium, override_ipa_net_d=None, bank_base_b_override=None
    )

def _df_to_model_rows(df: pd.DataFrame) -> List[ScheduleRow]:
    df2 = df.copy()
    df2.rename(columns={
        "Per#": "Per",
        "Period Start": "PeriodStart",
        "Due Date": "DueDate",
        "OB Start": "OB_Start",
        "Annuity (net)": "Annuity_net",
        "IRC N' (Monthly)": "IRC_N_monthly",
        "Bank Fee O' (Monthly)": "Bank_O_monthly",
        "Telematics R (Monthly)": "Telematics_R_monthly",
        "Generic TSF (Monthly)": "Generic_TSF_monthly",
        "TSF Upfront (Month 1)": "TSF_Upfront_M1",
        "VAT on TSF Upfront": "VAT_on_TSF_Upfront",
        "VAT on TSF Monthly": "VAT_on_TSF_Monthly",
        "VAT on Insurance Cap": "VAT_on_Insurance_Cap",
        "VAT on Annuity": "VAT_on_Annuity",
        "OB End": "OB_End",
    }, inplace=True)
    for col in ["PeriodStart", "DueDate"]:
        df2[col] = pd.to_datetime(df2[col]).dt.strftime("%Y-%m-%d")
    return [ScheduleRow(**row) for row in df2.to_dict(orient="records")]

@app.post("/calculate", response_model=CalculateResponse)
def calculate(payload: CalculateRequest):
    try:
        inputs = _to_inputs(payload)
        df, totals = build_schedule(inputs)
        rows = _df_to_model_rows(df)
        return CalculateResponse(totals=totals, schedule=rows)
    except ValidationError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export/xlsx")
def export_xlsx(payload: CalculateRequest):
    try:
        inputs = _to_inputs(payload)
        df, totals = build_schedule(inputs)
        xlsx = schedule_to_xlsx_bytes(df)
        headers = {"Content-Disposition": 'attachment; filename="schedule.xlsx"'}
        return Response(content=xlsx, headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export/pdf")
def export_pdf(payload: CalculateRequest):
    try:
        inputs = _to_inputs(payload)
        df, totals = build_schedule(inputs)
        pdf = schedule_to_pdf_bytes(df, title="IPA Schedule")
        headers = {"Content-Disposition": 'attachment; filename="schedule.pdf"'}
        return Response(content=pdf, headers=headers, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
