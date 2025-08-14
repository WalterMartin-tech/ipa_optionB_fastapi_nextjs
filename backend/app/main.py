
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import io
from openpyxl import Workbook
from reportlab.pdfgen import canvas
import os
from app.engine import run_calc, Inputs
from .calculator import compute

app = FastAPI(title="IPA Calculator API")

# CORS for local dev
origins = [o.strip() for o in os.getenv("FRONTEND_ORIGINS","http://localhost:3000,http://127.0.0.1:3000").split(",") if o.strip()]
koyeb = os.getenv("KOYEB_APP_DOMAIN")
if koyeb:
    origins.append(f"https://{koyeb}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginIn(BaseModel):
    username: str
    password: str

@app.post("/auth/login/json")
def login_json(body: LoginIn):
    if body.username == "admin@example.com" and body.password == "admin":
        return {"access_token": "demo-token", "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# very light auth dependency that accepts the demo token
def require_auth(authorization: Optional[str] = Header(None, alias="Authorization")):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if token != "demo-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return True

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/calculate")
async def calculate(req: Request, _=Depends(require_auth)):
    body = await req.json()
    inp = Inputs(
        principal=float(body.get("principal", 1_000_000)),
        rate=float(body.get("rate", 0.12)),
        term_months=int(body.get("term_months", 24)),
        balloon=float(body.get("balloon", 0.0)),
        vat_rate=float(body.get("vat_rate", 0.18)),
        asset_vat=float(body.get("asset_vat", 0.0)),
        telematics_monthly=float(body.get("telematics_monthly", 10_000)),
        include_irc=bool(body.get("include_irc", True)),
        include_banking=bool(body.get("include_banking", True)),
    )
    return run_calc(inp)
@app.post("/export/xlsx")
async def export_xlsx(req: Request, _=Depends(require_auth)):
    data = await req.json()
    wb = Workbook()
    ws = wb.active
    ws.title = "Calculation"
    ws["A1"] = "Example Metric"
    ws["B1"] = "Another"
    ws["A2"] = 123.45
    ws["B2"] = 67.89
    ws["A4"] = "Payload Echo"
    ws["B4"] = str(data)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    headers = {"Content-Disposition": 'attachment; filename="calculation.xlsx"'}
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )

@app.post("/export/pdf")
async def export_pdf(req: Request, _=Depends(require_auth)):
    data = await req.json()
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.setFont("Helvetica", 12)
    c.drawString(72, 800, "IPA Calculator - Demo PDF")
    c.drawString(72, 780, "Example Metric: 123.45")
    c.drawString(72, 760, "Another: 67.89")
    c.drawString(72, 740, f"Payload: {str(data)[:80]}...")
    c.showPage()
    c.save()
    buf.seek(0)
    headers = {"Content-Disposition": 'attachment; filename="calculation.pdf"'}
    return StreamingResponse(buf, media_type="application/pdf", headers=headers)
