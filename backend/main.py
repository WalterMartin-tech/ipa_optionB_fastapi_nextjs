from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# --- import your app logic ---
from models import LeaseInput
# lazy import inside endpoint to avoid boot-time failure
from exporters.xlsx_exporter import export_schedule_xlsx
from exporters.pdf_exporter import export_schedule_pdf

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
    from services import build_schedule
    return build_schedule(payload)

@app.post("/export/xlsx")
def export_xlsx(payload: LeaseInput):
    from services import build_schedule
    res = build_schedule(payload)
    data = export_schedule_xlsx(res.schedule, currency=payload.currency)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="schedule.xlsx"'}
    )

@app.post("/export/pdf")
def export_pdf(payload: LeaseInput):
    from services import build_schedule
    res = build_schedule(payload)
    data = export_schedule_pdf(res.schedule, currency=payload.currency)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="schedule.pdf"'}
    )
