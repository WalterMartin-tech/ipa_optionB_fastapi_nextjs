<<<<<<< HEAD

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple, Dict
from datetime import date
import pandas as pd

# ---------- Data models (dataclasses, internal) ----------

@dataclass
class TSFItem:
    name: str
    amount_monthly: float = 0.0
    vatable: bool = True

@dataclass
class InsurancePolicy:
    y1_amount: float = 0.0
    y2_amount: float = 0.0
    y3_amount: float = 0.0
    cap_y1: bool = True
    cap_y2: bool = True
    cap_y3: bool = True
    vatable: bool = True
    y2_cap_month: int = 12
    y3_cap_month: int = 24

@dataclass
class TSFConfig:
    tse_rate: float = 0.001
    tapr_fixed: float = 25000.0
    stamp_duty_fixed: float = 30000.0
    online_reg_fixed: float = 6650.0
    filing_minutes_fixed: float = 5000.0
    cprf_rate_effective: float = 0.0003
    tee_rate: float = 0.05
    apply_tee: bool = True
    loan_reg_rate: float = 0.01
    telematics_install_Q: float = 58500.0
    telematics_monthly_R: float = 10000.0
    irc_rate: float = 0.18
    banking_fee_rate: float = 0.026
    vat_telematics: bool = True
    vat_upfront_taxes: bool = False

@dataclass
class IPAInputs:
    asset_net: float
    vat_rate: float
    tenure_months: int
    annual_rate: float
    funding_rate: float = 0.0
    grace_months: int = 0
    balloon_percent: float = 0.0
    vendor_payment_date_T: date = date(2025, 9, 15)
    first_due_date_S: date = date(2025, 10, 1)
    monthly_tsf: List[TSFItem] = field(default_factory=list)
    tsf: TSFConfig = field(default_factory=TSFConfig)
    insurance: InsurancePolicy = field(default_factory=InsurancePolicy)
    vat_on_tsf: bool = True
    vat_on_insurance: bool = True
    round_decimals: int = 0
    solve_equilibrium: bool = True
    override_ipa_net_d: Optional[float] = None
    bank_base_b_override: Optional[float] = None

# ---------- Helpers ----------

def days_between(d1: date, d2: date) -> int:
    return (d2 - d1).days

def add_months(d: date, n: int) -> date:
    year = d.year + (d.month - 1 + n) // 12
    month = (d.month - 1 + n) % 12 + 1
    month_days = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                  31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
    day = min(d.day, month_days)
    return date(year, month, day)

def build_due_dates_from_S(S: date, n_months: int):
    start0 = add_months(S, -1)
    starts = [start0]; dues = [S]
    for _ in range(1, n_months):
        starts.append(dues[-1]); dues.append(add_months(dues[-1], 1))
    return starts, dues

# ---------- Core calculations ----------

def _annuity_payment(inputs: IPAInputs, principal: float, starts, dues, balloon_target: float) -> float:
    rc = inputs.annual_rate if inputs.annual_rate != 0 else 1e-12
    g = inputs.grace_months
    n = len(dues)

    def endbal(pmt: float) -> float:
        ob = principal
        for i in range(n):
            di = days_between(starts[i], dues[i]); ri = rc * (di / 365.0)
            interest = ob * ri
            if i < g:
                ob += round(interest, inputs.round_decimals)
            else:
                amort = pmt - round(interest, inputs.round_decimals)
                ob -= amort
        return ob

    lo, hi = 0.0, principal * (1 + rc)
    for _ in range(80):
        if endbal(hi) <= balloon_target: break
        hi *= 1.3
    for _ in range(140):
        mid = 0.5*(lo+hi); e = endbal(mid)
        if abs(e - balloon_target) <= 1.0: return mid
        if e > balloon_target: lo = mid
        else: hi = mid
    return 0.5*(lo+hi)

def _compute_A(inputs: IPAInputs, f_trial: float):
    d = inputs.override_ipa_net_d if inputs.override_ipa_net_d is not None else inputs.asset_net
    e = d * (1 + inputs.vat_rate)
    ins_y1 = inputs.insurance.y1_amount if inputs.insurance.cap_y1 else 0.0
    base_no_lr = (
        inputs.asset_net + ins_y1 + inputs.tsf.telematics_install_Q
        + inputs.tsf.tse_rate * d + inputs.tsf.tapr_fixed + inputs.tsf.stamp_duty_fixed
        + inputs.tsf.online_reg_fixed + inputs.tsf.filing_minutes_fixed
        + inputs.tsf.cprf_rate_effective * e + (inputs.tsf.tee_rate * e if inputs.tsf.apply_tee else 0.0)
    )
    A = (base_no_lr + inputs.tsf.loan_reg_rate * f_trial) / (1.0 - inputs.tsf.loan_reg_rate)
    parts = {
        "asset_net": inputs.asset_net, "insurance_y1": ins_y1, "telematics_Q": inputs.tsf.telematics_install_Q,
        "tse": inputs.tsf.tse_rate * d, "tapr": inputs.tsf.tapr_fixed, "stamp": inputs.tsf.stamp_duty_fixed,
        "online": inputs.tsf.online_reg_fixed, "filing": inputs.tsf.filing_minutes_fixed,
        "cprf": inputs.tsf.cprf_rate_effective * e, "tee": (inputs.tsf.tee_rate * e if inputs.tsf.apply_tee else 0.0),
        "loan_reg": inputs.tsf.loan_reg_rate * (A + f_trial),
    }
    return A, parts

def _compute_B(inputs: IPAInputs, A: float):
    T = inputs.vendor_payment_date_T; S = inputs.first_due_date_S
    W = max(0, days_between(T, S)); Wp = max(0, W - 30); rf = inputs.funding_rate
    funding_interest_W = A * rf * (Wp / 365.0)
    irc_dd = inputs.tsf.irc_rate * funding_interest_W
    bank_O_dd = inputs.tsf.banking_fee_rate * (A + funding_interest_W)
    B = funding_interest_W + irc_dd + bank_O_dd
    return B, {"W_days": W, "W_prime_days": Wp, "funding_interest_W": funding_interest_W, "IRC_dd": irc_dd, "Bank_O_dd": bank_O_dd}

def _vat_generated(df: pd.DataFrame) -> float:
    total = 0.0
    for c in ["VAT on Annuity", "VAT on TSF Monthly", "VAT on Insurance Cap", "VAT on TSF Upfront"]:
        if c in df.columns: total += float(df[c].sum())
    return total

def build_schedule(inputs: IPAInputs):
    starts, dues = build_due_dates_from_S(inputs.first_due_date_S, inputs.tenure_months)
    balloon_target = inputs.asset_net * inputs.balloon_percent
    vat_asset = inputs.asset_net * inputs.vat_rate

    def residual(f_trial: float):
        A, A_parts = _compute_A(inputs, f_trial)
        b_base = inputs.bank_base_b_override if inputs.bank_base_b_override is not None else A
        B, B_parts = _compute_B(inputs, A)
        C = A + B
        pmt = _annuity_payment(inputs, C, starts, dues, balloon_target)

        rows = []; ob = C; rc = inputs.annual_rate if inputs.annual_rate != 0 else 1e-12; rf = inputs.funding_rate
        generic = sum(x.amount_monthly for x in inputs.monthly_tsf)

        for i in range(inputs.tenure_months):
            m = i+1; d1, d2 = starts[i], dues[i]; di = days_between(d1, d2)
            ri = rc * (di/365.0); interest = round(ob * ri, inputs.round_decimals)

            ins_add = 0.0
            if m == inputs.insurance.y2_cap_month and inputs.insurance.cap_y2 and inputs.insurance.y2_amount > 0:
                ins_add += inputs.insurance.y2_amount; ob += ins_add
            if m == inputs.insurance.y3_cap_month and inputs.insurance.cap_y3 and inputs.insurance.y3_amount > 0:
                ins_add += inputs.insurance.y3_amount; ob += ins_add
            vat_ins = round(ins_add * inputs.vat_rate, inputs.round_decimals) if (ins_add and inputs.vat_on_insurance) else 0.0

            c_prime = (rf/rc) * interest if rc != 0 else 0.0
            irc_n = round(inputs.tsf.irc_rate * c_prime, inputs.round_decimals)
            bank_o = round(inputs.tsf.banking_fee_rate * (b_base/inputs.tenure_months + c_prime), inputs.round_decimals)
            tele_r = inputs.tsf.telematics_monthly_R

            tsf_monthly_vatable = (tele_r if inputs.tsf.vat_telematics else 0.0) + (generic if inputs.vat_on_tsf else 0.0)
            vat_tsf_monthly = round(tsf_monthly_vatable * inputs.vat_rate, inputs.round_decimals)

            if i < inputs.grace_months:
                annuity = 0.0; amort = 0.0; ob += interest
            else:
                annuity = pmt; amort = round(annuity - interest, inputs.round_decimals); ob -= amort

            if i == inputs.tenure_months - 1:
                diff = ob - balloon_target; amort += diff; annuity = interest + amort; ob = balloon_target

            tsf_upfront_this = 0.0; vat_tsf_upfront = 0.0
            if i == 0:
                oneoffs_total = (
                    A_parts["telematics_Q"] + A_parts["tse"] + A_parts["tapr"] + A_parts["stamp"] +
                    A_parts["online"] + A_parts["filing"] + A_parts["cprf"] + A_parts["tee"] + A_parts["loan_reg"]
                )
                tsf_upfront_this = round(oneoffs_total, inputs.round_decimals)
                vatable_upfront = (A_parts["telematics_Q"] if inputs.tsf.vat_telematics else 0.0)
                if inputs.tsf.vat_upfront_taxes:
                    vatable_upfront += (oneoffs_total - A_parts["telematics_Q"])
                vat_tsf_upfront = round(vatable_upfront * inputs.vat_rate, inputs.round_decimals)

            vat_annuity = round(annuity * inputs.vat_rate, inputs.round_decimals)

            rows.append({
                "Per#": m, "Period Start": d1, "Due Date": d2, "Days": di,
                "OB Start": ob + amort - interest,
                "Interest": interest, "Amortization": amort, "Annuity (net)": round(annuity, inputs.round_decimals),
                "IRC N' (Monthly)": irc_n, "Bank Fee O' (Monthly)": bank_o, "Telematics R (Monthly)": tele_r, "Generic TSF (Monthly)": generic,
                "TSF Upfront (Month 1)": tsf_upfront_this, "VAT on TSF Upfront": vat_tsf_upfront,
                "VAT on TSF Monthly": vat_tsf_monthly, "VAT on Insurance Cap": vat_ins, "VAT on Annuity": vat_annuity,
                "OB End": ob,
            })

        df = pd.DataFrame(rows)
        vat_gen = _vat_generated(df)
        resid = vat_gen - (vat_asset + f_trial)
        totals = {"A": A, "B": B, "C": A + B, "balloon_target": balloon_target, "vat_asset": vat_asset,
                  "f_trial": f_trial, "vat_generated": vat_gen}
        return resid, df, totals

    # Solve for f
    if inputs.solve_equilibrium:
        lo, hi = 0.0, max(1.0, vat_asset * 0.5)
        r_lo, _, _ = residual(lo); r_hi, _, _ = residual(hi)
        tries = 0
        while r_lo * r_hi > 0 and tries < 25:
            hi *= 1.5; r_hi, _, _ = residual(hi); tries += 1
        f_star = hi
        if r_lo * r_hi <= 0:
            for _ in range(80):
                mid = 0.5*(lo+hi); r_mid, _, _ = residual(mid)
                if abs(r_mid) <= 1.0: f_star = mid; break
                if r_lo * r_mid <= 0: hi = mid; r_hi = r_mid
                else: lo = mid; r_lo = r_mid
        resid, df, totals = residual(f_star); f_solved = round(f_star, inputs.round_decimals)
    else:
        resid, df, totals = residual(0.0); f_solved = 0.0
||||||| (empty tree)
=======
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple

import pandas as pd

# ---------- Data models (dataclasses, internal) ----------


@dataclass
class TSFItem:
    name: str
    amount_monthly: float = 0.0
    vatable: bool = True


@dataclass
class InsurancePolicy:
    y1_amount: float = 0.0
    y2_amount: float = 0.0
    y3_amount: float = 0.0
    cap_y1: bool = True
    cap_y2: bool = True
    cap_y3: bool = True
    vatable: bool = True
    y2_cap_month: int = 12
    y3_cap_month: int = 24


@dataclass
class TSFConfig:
    tse_rate: float = 0.001
    tapr_fixed: float = 25000.0
    stamp_duty_fixed: float = 30000.0
    online_reg_fixed: float = 6650.0
    filing_minutes_fixed: float = 5000.0
    cprf_rate_effective: float = 0.0003
    tee_rate: float = 0.05
    apply_tee: bool = True
    loan_reg_rate: float = 0.01
    telematics_install_Q: float = 58500.0
    telematics_monthly_R: float = 10000.0
    irc_rate: float = 0.18
    banking_fee_rate: float = 0.026
    vat_telematics: bool = True
    vat_upfront_taxes: bool = False


@dataclass
class IPAInputs:
    asset_net: float
    vat_rate: float
    tenure_months: int
    annual_rate: float
    funding_rate: float = 0.0
    grace_months: int = 0
    balloon_percent: float = 0.0
    vendor_payment_date_T: date = date(2025, 9, 15)
    first_due_date_S: date = date(2025, 10, 1)
    monthly_tsf: List[TSFItem] = field(default_factory=list)
    tsf: TSFConfig = field(default_factory=TSFConfig)
    insurance: InsurancePolicy = field(default_factory=InsurancePolicy)
    vat_on_tsf: bool = True
    vat_on_insurance: bool = True
    round_decimals: int = 0
    solve_equilibrium: bool = True
    override_ipa_net_d: Optional[float] = None
    bank_base_b_override: Optional[float] = None


# ---------- Helpers ----------


def days_between(d1: date, d2: date) -> int:
    return (d2 - d1).days


def add_months(d: date, n: int) -> date:
    year = d.year + (d.month - 1 + n) // 12
    month = (d.month - 1 + n) % 12 + 1
    month_days = [
        31,
        29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ][month - 1]
    day = min(d.day, month_days)
    return date(year, month, day)


def build_due_dates_from_S(S: date, n_months: int):
    start0 = add_months(S, -1)
    starts = [start0]
    dues = [S]
    for _ in range(1, n_months):
        starts.append(dues[-1])
        dues.append(add_months(dues[-1], 1))
    return starts, dues


# ---------- Core calculations ----------


def _annuity_payment(
    inputs: IPAInputs, principal: float, starts, dues, balloon_target: float
) -> float:
    rc = inputs.annual_rate if inputs.annual_rate != 0 else 1e-12
    g = inputs.grace_months
    n = len(dues)

    def endbal(pmt: float) -> float:
        ob = principal
        for i in range(n):
            di = days_between(starts[i], dues[i])
            ri = rc * (di / 365.0)
            interest = ob * ri
            if i < g:
                ob += round(interest, inputs.round_decimals)
            else:
                amort = pmt - round(interest, inputs.round_decimals)
                ob -= amort
        return ob

    lo, hi = 0.0, principal * (1 + rc)
    for _ in range(80):
        if endbal(hi) <= balloon_target:
            break
        hi *= 1.3
    for _ in range(140):
        mid = 0.5 * (lo + hi)
        e = endbal(mid)
        if abs(e - balloon_target) <= 1.0:
            return mid
        if e > balloon_target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _compute_A(inputs: IPAInputs, f_trial: float):
    d = (
        inputs.override_ipa_net_d
        if inputs.override_ipa_net_d is not None
        else inputs.asset_net
    )
    e = d * (1 + inputs.vat_rate)
    ins_y1 = inputs.insurance.y1_amount if inputs.insurance.cap_y1 else 0.0
    base_no_lr = (
        inputs.asset_net
        + ins_y1
        + inputs.tsf.telematics_install_Q
        + inputs.tsf.tse_rate * d
        + inputs.tsf.tapr_fixed
        + inputs.tsf.stamp_duty_fixed
        + inputs.tsf.online_reg_fixed
        + inputs.tsf.filing_minutes_fixed
        + inputs.tsf.cprf_rate_effective * e
        + (inputs.tsf.tee_rate * e if inputs.tsf.apply_tee else 0.0)
    )
    A = (base_no_lr + inputs.tsf.loan_reg_rate * f_trial) / (
        1.0 - inputs.tsf.loan_reg_rate
    )
    parts = {
        "asset_net": inputs.asset_net,
        "insurance_y1": ins_y1,
        "telematics_Q": inputs.tsf.telematics_install_Q,
        "tse": inputs.tsf.tse_rate * d,
        "tapr": inputs.tsf.tapr_fixed,
        "stamp": inputs.tsf.stamp_duty_fixed,
        "online": inputs.tsf.online_reg_fixed,
        "filing": inputs.tsf.filing_minutes_fixed,
        "cprf": inputs.tsf.cprf_rate_effective * e,
        "tee": (inputs.tsf.tee_rate * e if inputs.tsf.apply_tee else 0.0),
        "loan_reg": inputs.tsf.loan_reg_rate * (A + f_trial),
    }
    return A, parts


def _compute_B(inputs: IPAInputs, A: float):
    T = inputs.vendor_payment_date_T
    S = inputs.first_due_date_S
    W = max(0, days_between(T, S))
    Wp = max(0, W - 30)
    rf = inputs.funding_rate
    funding_interest_W = A * rf * (Wp / 365.0)
    irc_dd = inputs.tsf.irc_rate * funding_interest_W
    bank_O_dd = inputs.tsf.banking_fee_rate * (A + funding_interest_W)
    B = funding_interest_W + irc_dd + bank_O_dd
    return B, {
        "W_days": W,
        "W_prime_days": Wp,
        "funding_interest_W": funding_interest_W,
        "IRC_dd": irc_dd,
        "Bank_O_dd": bank_O_dd,
    }


def _vat_generated(df: pd.DataFrame) -> float:
    total = 0.0
    for c in [
        "VAT on Annuity",
        "VAT on TSF Monthly",
        "VAT on Insurance Cap",
        "VAT on TSF Upfront",
    ]:
        if c in df.columns:
            total += float(df[c].sum())
    return total


def build_schedule(inputs: IPAInputs):
    starts, dues = build_due_dates_from_S(inputs.first_due_date_S, inputs.tenure_months)
    balloon_target = inputs.asset_net * inputs.balloon_percent
    vat_asset = inputs.asset_net * inputs.vat_rate

    def residual(f_trial: float):
        A, A_parts = _compute_A(inputs, f_trial)
        b_base = (
            inputs.bank_base_b_override
            if inputs.bank_base_b_override is not None
            else A
        )
        B, B_parts = _compute_B(inputs, A)
        C = A + B
        pmt = _annuity_payment(inputs, C, starts, dues, balloon_target)

        rows = []
        ob = C
        rc = inputs.annual_rate if inputs.annual_rate != 0 else 1e-12
        rf = inputs.funding_rate
        generic = sum(x.amount_monthly for x in inputs.monthly_tsf)

        for i in range(inputs.tenure_months):
            m = i + 1
            d1, d2 = starts[i], dues[i]
            di = days_between(d1, d2)
            ri = rc * (di / 365.0)
            interest = round(ob * ri, inputs.round_decimals)

            ins_add = 0.0
            if (
                m == inputs.insurance.y2_cap_month
                and inputs.insurance.cap_y2
                and inputs.insurance.y2_amount > 0
            ):
                ins_add += inputs.insurance.y2_amount
                ob += ins_add
            if (
                m == inputs.insurance.y3_cap_month
                and inputs.insurance.cap_y3
                and inputs.insurance.y3_amount > 0
            ):
                ins_add += inputs.insurance.y3_amount
                ob += ins_add
            vat_ins = (
                round(ins_add * inputs.vat_rate, inputs.round_decimals)
                if (ins_add and inputs.vat_on_insurance)
                else 0.0
            )

            c_prime = (rf / rc) * interest if rc != 0 else 0.0
            irc_n = round(inputs.tsf.irc_rate * c_prime, inputs.round_decimals)
            bank_o = round(
                inputs.tsf.banking_fee_rate * (b_base / inputs.tenure_months + c_prime),
                inputs.round_decimals,
            )
            tele_r = inputs.tsf.telematics_monthly_R

            tsf_monthly_vatable = (tele_r if inputs.tsf.vat_telematics else 0.0) + (
                generic if inputs.vat_on_tsf else 0.0
            )
            vat_tsf_monthly = round(
                tsf_monthly_vatable * inputs.vat_rate, inputs.round_decimals
            )

            if i < inputs.grace_months:
                annuity = 0.0
                amort = 0.0
                ob += interest
            else:
                annuity = pmt
                amort = round(annuity - interest, inputs.round_decimals)
                ob -= amort

            if i == inputs.tenure_months - 1:
                diff = ob - balloon_target
                amort += diff
                annuity = interest + amort
                ob = balloon_target

            tsf_upfront_this = 0.0
            vat_tsf_upfront = 0.0
            if i == 0:
                oneoffs_total = (
                    A_parts["telematics_Q"]
                    + A_parts["tse"]
                    + A_parts["tapr"]
                    + A_parts["stamp"]
                    + A_parts["online"]
                    + A_parts["filing"]
                    + A_parts["cprf"]
                    + A_parts["tee"]
                    + A_parts["loan_reg"]
                )
                tsf_upfront_this = round(oneoffs_total, inputs.round_decimals)
                vatable_upfront = (
                    A_parts["telematics_Q"] if inputs.tsf.vat_telematics else 0.0
                )
                if inputs.tsf.vat_upfront_taxes:
                    vatable_upfront += oneoffs_total - A_parts["telematics_Q"]
                vat_tsf_upfront = round(
                    vatable_upfront * inputs.vat_rate, inputs.round_decimals
                )

            vat_annuity = round(annuity * inputs.vat_rate, inputs.round_decimals)

            rows.append(
                {
                    "Per#": m,
                    "Period Start": d1,
                    "Due Date": d2,
                    "Days": di,
                    "OB Start": ob + amort - interest,
                    "Interest": interest,
                    "Amortization": amort,
                    "Annuity (net)": round(annuity, inputs.round_decimals),
                    "IRC N' (Monthly)": irc_n,
                    "Bank Fee O' (Monthly)": bank_o,
                    "Telematics R (Monthly)": tele_r,
                    "Generic TSF (Monthly)": generic,
                    "TSF Upfront (Month 1)": tsf_upfront_this,
                    "VAT on TSF Upfront": vat_tsf_upfront,
                    "VAT on TSF Monthly": vat_tsf_monthly,
                    "VAT on Insurance Cap": vat_ins,
                    "VAT on Annuity": vat_annuity,
                    "OB End": ob,
                }
            )

        df = pd.DataFrame(rows)
        vat_gen = _vat_generated(df)
        resid = vat_gen - (vat_asset + f_trial)
        totals = {
            "A": A,
            "B": B,
            "C": A + B,
            "balloon_target": balloon_target,
            "vat_asset": vat_asset,
            "f_trial": f_trial,
            "vat_generated": vat_gen,
        }
        return resid, df, totals

    # Solve for f
    if inputs.solve_equilibrium:
        lo, hi = 0.0, max(1.0, vat_asset * 0.5)
        r_lo, _, _ = residual(lo)
        r_hi, _, _ = residual(hi)
        tries = 0
        while r_lo * r_hi > 0 and tries < 25:
            hi *= 1.5
            r_hi, _, _ = residual(hi)
            tries += 1
        f_star = hi
        if r_lo * r_hi <= 0:
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                r_mid, _, _ = residual(mid)
                if abs(r_mid) <= 1.0:
                    f_star = mid
                    break
                if r_lo * r_mid <= 0:
                    hi = mid
                    r_hi = r_mid
                else:
                    lo = mid
                    r_lo = r_mid
        resid, df, totals = residual(f_star)
        f_solved = round(f_star, inputs.round_decimals)
    else:
        resid, df, totals = residual(0.0)
        f_solved = 0.0
>>>>>>> 2fd963e (chore: Koyeb Procfile/runtime, env-driven CORS, frontend .envs, calc engine & tests)

    # Prepare public totals
    totals_public = {
        "A": round(totals["A"], inputs.round_decimals),
        "B": round(totals["B"], inputs.round_decimals),
        "C_principal": round(totals["C"], inputs.round_decimals),
        "BalloonTarget": round(totals["balloon_target"], inputs.round_decimals),
        "VAT_on_Asset": round(totals["vat_asset"], inputs.round_decimals),
        "f_solved": f_solved,
        "VAT_generated": round(totals["vat_generated"], inputs.round_decimals),
    }
    return df, totals_public
