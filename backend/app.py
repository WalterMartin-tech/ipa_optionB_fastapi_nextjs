print("Booting IPA API via app.py (no exporters)")

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

try:
    from models import LeaseInput
except Exception:
    class LeaseInput(BaseModel):
        amount: float = 0.0
        currency: str = "USD"
        class Config: extra = "allow"

def _load_build_schedule():
    try:
        from ipa_engine.engine import build_schedule as _bs
        return _bs
    except Exception:
        def _bs(payload): return {"schedule": [], "note": "placeholder (no engine found)"}
        return _bs

try:
    from utils_export import export_schedule_xlsx, export_schedule_pdf
except Exception:
    def export_schedule_xlsx(schedule, currency="USD"): return b""
    def export_schedule_pdf(schedule, currency="USD"):  return b""



from backend.debug_errors import setup as setup_debug
setup_debug(app)

from backend.debug_errors import setup as setup_debug
setup_debug(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://*.vercel.app","https://double-alexia-waltwart-saas-543e51cf.koyeb.app"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/", include_in_schema=False)
def root(): return RedirectResponse("/docs")

@app.post("/calculate")
def calculate(payload: LeaseInput):
    return _load_build_schedule()(payload)

@app.post("/export/xlsx")
def export_xlsx(payload: LeaseInput):
    res = _load_build_schedule()(payload)
    data = export_schedule_xlsx(res.get("schedule", []), currency=getattr(payload,"currency","USD"))
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="schedule.xlsx"'}
    )

@app.post("/export/pdf")
def export_pdf(payload: LeaseInput):
    res = _load_build_schedule()(payload)
    data = export_schedule_pdf(res.get("schedule", []), currency=getattr(payload,"currency","USD"))
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="schedule.pdf"'}
    )


@app.get('/__probe')
def __probe():
    return {
        "debug_errors": os.getenv("DEBUG_ERRORS","0"),
        "has_handler": True
    }
