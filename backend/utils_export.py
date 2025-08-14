<<<<<<< HEAD

import io
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
import xlsxwriter

def schedule_to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Schedule")
        ws = writer.sheets["Schedule"]
        wb = writer.book
        num = wb.add_format({"num_format": "#,##0"})
        for i, col in enumerate(df.columns):
            ws.set_column(i, i, 16, num if pd.api.types.is_numeric_dtype(df[col]) else None)
    return buf.getvalue()

def schedule_to_pdf_bytes(df: pd.DataFrame, title: str = "IPA Schedule") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    width, height = landscape(A4)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(20*mm, height-15*mm, title)

    # basic table header + first ~25 rows to keep simple
    cols = list(df.columns)
    x0, y = 15*mm, height-30*mm
    col_w = (width - 30*mm) / len(cols)
    c.setFont("Helvetica-Bold", 8)
    for i, col in enumerate(cols):
        c.drawString(x0 + i*col_w, y, str(col)[:18])
    y -= 6*mm

    c.setFont("Helvetica", 8)
    rows = df.head(25).values.tolist()
    for r in rows:
        for i, val in enumerate(r):
            c.drawString(x0 + i*col_w, y, f"{val}")
        y -= 5*mm
        if y < 15*mm:
            c.showPage()
            y = height-20*mm

    c.showPage(); c.save()
||||||| (empty tree)
=======
import io

import pandas as pd
import xlsxwriter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def schedule_to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Schedule")
        ws = writer.sheets["Schedule"]
        wb = writer.book
        num = wb.add_format({"num_format": "#,##0"})
        for i, col in enumerate(df.columns):
            ws.set_column(
                i, i, 16, num if pd.api.types.is_numeric_dtype(df[col]) else None
            )
    return buf.getvalue()


def schedule_to_pdf_bytes(df: pd.DataFrame, title: str = "IPA Schedule") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    width, height = landscape(A4)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, height - 15 * mm, title)

    # basic table header + first ~25 rows to keep simple
    cols = list(df.columns)
    x0, y = 15 * mm, height - 30 * mm
    col_w = (width - 30 * mm) / len(cols)
    c.setFont("Helvetica-Bold", 8)
    for i, col in enumerate(cols):
        c.drawString(x0 + i * col_w, y, str(col)[:18])
    y -= 6 * mm

    c.setFont("Helvetica", 8)
    rows = df.head(25).values.tolist()
    for r in rows:
        for i, val in enumerate(r):
            c.drawString(x0 + i * col_w, y, f"{val}")
        y -= 5 * mm
        if y < 15 * mm:
            c.showPage()
            y = height - 20 * mm

    c.showPage()
    c.save()
>>>>>>> 2fd963e (chore: Koyeb Procfile/runtime, env-driven CORS, frontend .envs, calc engine & tests)
    return buf.getvalue()
