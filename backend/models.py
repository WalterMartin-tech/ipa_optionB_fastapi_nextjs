
from pydantic import BaseModel, Field, conint, confloat
from typing import List, Optional
from datetime import date

class TSFItemModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    amount_monthly: float = Field(ge=0, default=0.0)
    vatable: bool = True

class InsuranceModel(BaseModel):
    y1_amount: float = 0.0
    y2_amount: float = 0.0
    y3_amount: float = 0.0
    cap_y1: bool = True
    cap_y2: bool = True
    cap_y3: bool = True
    vatable: bool = True
    y2_cap_month: conint(ge=2) = 12
    y3_cap_month: conint(ge=3) = 24

class TSFConfigModel(BaseModel):
    tse_rate: confloat(ge=0) = 0.001
    tapr_fixed: confloat(ge=0) = 25000.0
    stamp_duty_fixed: confloat(ge=0) = 30000.0
    online_reg_fixed: confloat(ge=0) = 6650.0
    filing_minutes_fixed: confloat(ge=0) = 5000.0
    cprf_rate_effective: confloat(ge=0) = 0.0003
    tee_rate: confloat(ge=0) = 0.05
    apply_tee: bool = True
    loan_reg_rate: confloat(ge=0) = 0.01
    telematics_install_Q: confloat(ge=0) = 58500.0
    telematics_monthly_R: confloat(ge=0) = 10000.0
    irc_rate: confloat(ge=0) = 0.18
    banking_fee_rate: confloat(ge=0) = 0.026
    vat_telematics: bool = True
    vat_upfront_taxes: bool = False

class CalculateRequest(BaseModel):
    asset_net: confloat(ge=0)
    vat_rate: confloat(ge=0, le=1) = 0.18
    tenure_months: conint(ge=1) = 36
    annual_rate: confloat(ge=0, le=1) = 0.20
    funding_rate: confloat(ge=0, le=1) = 0.12
    grace_months: conint(ge=0) = 0
    balloon_percent: confloat(ge=0, le=1) = 0.0

    vendor_payment_date_T: date = date(2025, 9, 15)
    first_due_date_S: date = date(2025, 10, 1)

    monthly_tsf: List[TSFItemModel] = []
    tsf: TSFConfigModel = TSFConfigModel()
    insurance: InsuranceModel = InsuranceModel()

    vat_on_tsf: bool = True
    vat_on_insurance: bool = True
    round_decimals: conint(ge=0, le=2) = 0
    solve_equilibrium: bool = True

class ScheduleRow(BaseModel):
    Per: int
    PeriodStart: str
    DueDate: str
    Days: int
    OB_Start: float
    Interest: float
    Amortization: float
    Annuity_net: float
    IRC_N_monthly: float
    Bank_O_monthly: float
    Telematics_R_monthly: float
    Generic_TSF_monthly: float
    TSF_Upfront_M1: float
    VAT_on_TSF_Upfront: float
    VAT_on_TSF_Monthly: float
    VAT_on_Insurance_Cap: float
    VAT_on_Annuity: float
    OB_End: float

class CalculateResponse(BaseModel):
    totals: dict
    schedule: List[ScheduleRow]
