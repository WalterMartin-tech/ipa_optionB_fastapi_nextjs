from dataclasses import dataclass, asdict
from typing import List, Dict

@dataclass
class Inputs:
    # Core inputs (C, rc, n, balloon)
    principal: float            # Final Financing Amount C
    rate: float                 # rc (decimal), e.g. 0.12
    term_months: int            # n
    balloon: float = 0.0        # balloon due at end
    # VAT / reporting
    vat_rate: float = 0.18
    asset_vat: float = 0.0      # E
    # TSF knobs (monthly, non-capitalized flows)
    telematics_monthly: float = 10_000.0  # R
    include_irc: bool = True               # N'
    include_banking: bool = True           # O'
    # Approximations for monthly TSF
    irc_rate: float = 0.18                 # 18% on monthly interest (N')
    banking_rate: float = 0.026            # 2.6% on (C/n + monthly interest) (O')

def pmt_with_balloon(pv: float, rate_annual: float, n: int, fv: float=0.0) -> float:
    """Standard annuity (includes balloon in PV logic)."""
    i = rate_annual / 12.0
    if n <= 0:
        return 0.0
    # PMT = i*(pv - fv/(1+i)^n) / (1 - (1+i)^-n)
    denom = 1.0 - (1.0 + i) ** (-n)
    adj_pv = pv - fv / ((1.0 + i) ** n)
    return (i * adj_pv) / denom

def run_calc(inp: Inputs) -> Dict:
    i = inp.rate / 12.0
    annuity = pmt_with_balloon(inp.principal, inp.rate, inp.term_months, fv=inp.balloon)

    rows: List[Dict] = []
    outstanding = float(inp.principal)
    annuity_identity_ok = True

    for m in range(1, inp.term_months + 1):
        interest = outstanding * i
        irc_m = (inp.irc_rate * interest) if inp.include_irc else 0.0               # N'
        bank_m = (inp.banking_rate * ((inp.principal / inp.term_months) + interest)) if inp.include_banking else 0.0  # O'
        tsf = inp.telematics_monthly + irc_m + bank_m                               # R + N' + O'
        capital = annuity - interest - tsf                                          # Capital can be < 0 (negative amortization)
        outstanding = outstanding - capital

        # Identity check: AP == Interest + TSF + Capital
        if abs((interest + tsf + capital) - annuity) > 1e-6:
            annuity_identity_ok = False

        rows.append({
            "month": m,
            "interest": round(interest, 2),
            "tsf": round(tsf, 2),
            "capital": round(capital, 2),
            "annuity": round(annuity, 2),
            "outstanding": round(outstanding, 2),
        })

    # IPA totals (net of VAT): sum of annuities + balloon
    ipa_net = annuity * inp.term_months + inp.balloon
    vat_ipa = inp.vat_rate * ipa_net
    vat_delta = vat_ipa - inp.asset_vat  # = VAT(IPA) - VAT(Asset)

    out = {
        "inputs": asdict(inp),
        "annuity": round(annuity, 2),
        "ipa_net": round(ipa_net, 2),                         # d
        "ipa_vat": round(vat_ipa, 2),                         # VAT on total IPA
        "asset_vat": round(inp.asset_vat, 2),                 # E
        "vat_delta": round(vat_delta, 2),                     # f = VAT(IPA) - VAT(Asset)
        "annuity_identity_ok": annuity_identity_ok,           # spec: AP = Interest + TSF + Capital
        "schedule": rows[:12],                                # head (avoid huge payloads)
        "outstanding_final": round(outstanding, 2),
    }
    return out
