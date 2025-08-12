from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# --- LeaseInput model (use your real one if present) ---
try:
    from models import LeaseInput  # your own schema
except Exception:
    class LeaseInput(BaseModel):   # permissive fallback so app boots
        amount: float = 0.0
        currency: str = "USD"
        class Config:
            extra = "allow"

def _load_build_schedule():
    """Import build_schedule from your engine if available; else placeholder."""
    try:
        from ipa_engine.engine import build_schedule as _bs
        return _bs
    except Exception:
        def _bs(payload):
            return {"schedule": [], "note": "placeholder (no engine found)"}
        return _bs

# --- Exporters: use utils_export if you have it; else minimal fallbacks ---
try:
    from utils_export import export_schedule_xlsx, export_schedule_pdf  # your helpers
except Exception:
    def export_schedule_xlsx(schedule, currency="USD"):
        import io, pandas as pd
        buf = io.BytesIO()
        df = pd.DataFrame(schedule)
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df.to_excel(w, index=False, sheet_name="Schedule")
        return buf.getvalue()
    def export_schedule_pdf(schedule, currency="USD"):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        import io
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.drawString(72, 800, f"Lease schedule ({currency})")
        y = 780
        for row in schedule[:50]:
            c.drawString(72, y, str(row))
            y -= 14
            if y < 72:
                c.showPage(); y = 800
        c.save()
        return buf.getvalue()

app = FastAPI(title="IPA API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://double-alexia-waltwart-saas-543e51cf.koyeb.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")

@app.post("/calculate")
def calculate(payload: LeaseInput):
    build_schedule = _load_build_schedule()
    return build_schedule(payload)

@app.post("/export/xlsx")
def export_xlsx(payload: LeaseInput):
    build_schedule = _load_build_schedule()
    res = build_schedule(payload)
    data = export_schedule_xlsx(res.get("schedule", []), currency=getattr(payload, "currency", "USD"))
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="schedule.xlsx"'}
    )

@app.post("/export/pdf")
def export_pdf(payload: LeaseInput):
    build_schedule = _load_build_schedule()
    res = build_schedule(payload)
    data = export_schedule_pdf(res.get("schedule", []), currency=getattr(payload, "currency", "USD"))
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="schedule.pdf"'}
    )
