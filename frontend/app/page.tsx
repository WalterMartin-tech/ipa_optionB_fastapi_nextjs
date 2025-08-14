<<<<<<< HEAD

"use client";
import React, { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type CalcPayload = {
  asset_net: number;
  vat_rate: number;
  tenure_months: number;
  annual_rate: number;
  funding_rate: number;
  grace_months: number;
  balloon_percent: number;
  vendor_payment_date_T: string;
  first_due_date_S: string;
  monthly_tsf: { name: string; amount_monthly: number; vatable: boolean }[];
  tsf: any;
  insurance: any;
  vat_on_tsf: boolean;
  vat_on_insurance: boolean;
  round_decimals: number;
  solve_equilibrium: boolean;
};

export default function Page() {
  const [loading, setLoading] = useState(false);
  const [totals, setTotals] = useState<any>(null);
  const [rows, setRows] = useState<any[]>([]);

  const [form, setForm] = useState<CalcPayload>({
    asset_net: 10000000,
    vat_rate: 0.18,
    tenure_months: 36,
    annual_rate: 0.20,
    funding_rate: 0.12,
    grace_months: 0,
    balloon_percent: 0.0,
    vendor_payment_date_T: "2025-09-15",
    first_due_date_S: "2025-10-01",
    monthly_tsf: [],
    tsf: {
      tse_rate: 0.001, tapr_fixed: 25000, stamp_duty_fixed: 30000, online_reg_fixed: 6650,
      filing_minutes_fixed: 5000, cprf_rate_effective: 0.0003, tee_rate: 0.05, apply_tee: true,
      loan_reg_rate: 0.01, telematics_install_Q: 58500, telematics_monthly_R: 10000,
      irc_rate: 0.18, banking_fee_rate: 0.026, vat_telematics: true, vat_upfront_taxes: false
    },
    insurance: {
      y1_amount: 0, y2_amount: 0, y3_amount: 0, cap_y1: true, cap_y2: true, cap_y3: true, vatable: true,
      y2_cap_month: 12, y3_cap_month: 24
    },
    vat_on_tsf: true,
    vat_on_insurance: true,
    round_decimals: 0,
    solve_equilibrium: true,
  });

  const number = (v: number) => new Intl.NumberFormat().format(v ?? 0);

  async function calc() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setTotals(data.totals);
      setRows(data.schedule);
    } catch (e: any) {
      alert("Calc failed: " + e.message);
    } finally {
      setLoading(false);
    }
  }

  async function download(path: string, filename: string) {
    try {
      const res = await fetch(`${API}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = filename; a.click();
      window.URL.revokeObjectURL(url);
    } catch (e: any) {
      alert("Download failed: " + e.message);
    }
  }

  return (
    <div style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700 }}>IPA – FastAPI + Next.js</h1>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginTop: 16 }}>
        <label>Asset (net) <input type="number" value={form.asset_net} onChange={e=>setForm({...form, asset_net: parseFloat(e.target.value)})}/></label>
        <label>VAT Rate <input type="number" step="0.01" value={form.vat_rate} onChange={e=>setForm({...form, vat_rate: parseFloat(e.target.value)})}/></label>
        <label>Tenure (months) <input type="number" value={form.tenure_months} onChange={e=>setForm({...form, tenure_months: parseInt(e.target.value)})}/></label>
        <label>rc <input type="number" step="0.01" value={form.annual_rate} onChange={e=>setForm({...form, annual_rate: parseFloat(e.target.value)})}/></label>
        <label>rf <input type="number" step="0.01" value={form.funding_rate} onChange={e=>setForm({...form, funding_rate: parseFloat(e.target.value)})}/></label>
        <label>Balloon % <input type="number" step="0.01" value={form.balloon_percent} onChange={e=>setForm({...form, balloon_percent: parseFloat(e.target.value)})}/></label>
        <label>T (vendor payment) <input type="date" value={form.vendor_payment_date_T} onChange={e=>setForm({...form, vendor_payment_date_T: e.target.value})}/></label>
        <label>S (first due date) <input type="date" value={form.first_due_date_S} onChange={e=>setForm({...form, first_due_date_S: e.target.value})}/></label>
        <label>Rounding
          <select value={form.round_decimals} onChange={e=>setForm({...form, round_decimals: parseInt(e.target.value)})}>
            <option value={0}>0</option>
            <option value={1}>1</option>
            <option value={2}>2</option>
          </select>
        </label>
      </div>

      <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
        <button onClick={calc} disabled={loading} style={{ padding: "8px 12px" }}>
          {loading ? "Calculating..." : "Calculate"}
        </button>
        <button onClick={()=>download("/export/xlsx","schedule.xlsx")} style={{ padding: "8px 12px" }}>Export XLSX</button>
        <button onClick={()=>download("/export/pdf","schedule.pdf")} style={{ padding: "8px 12px" }}>Export PDF</button>
      </div>

      {totals && (
        <div style={{ marginTop: 24 }}>
          <h2 style={{ fontSize: 18 }}>Totals</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
            {Object.entries(totals).map(([k,v]) => (
              <div key={k} style={{ background:"#1111", padding: 8, borderRadius: 8 }}>
                <div style={{ fontSize: 12, color:"#444" }}>{k}</div>
                <div style={{ fontWeight: 600 }}>{typeof v === "number" ? number(v) : String(v)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {rows?.length>0 && (
        <div style={{ marginTop: 24 }}>
          <h2 style={{ fontSize: 18 }}>Schedule (first 12)</h2>
          <div style={{ maxHeight: 400, overflow: "auto", border: "1px solid #ddd" }}>
            <table cellPadding={6} style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
              <thead>
                <tr>
                  {Object.keys(rows[0]).map((h) => <th key={h} style={{ position:"sticky", top:0, background:"#fafafa", borderBottom:"1px solid #ccc" }}>{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, 12).map((r, i) => (
                  <tr key={i}>
                    {Object.values(r).map((v, j) => <td key={j} style={{ borderBottom:"1px solid #eee" }}>{typeof v === "number" ? number(v) : String(v)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
||||||| (empty tree)
=======
'use client'
import React, { useState } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type CalcPayload = {
  asset_net: number
  vat_rate: number
  tenure_months: number
  annual_rate: number
  funding_rate: number
  grace_months: number
  balloon_percent: number
  vendor_payment_date_T: string
  first_due_date_S: string
  monthly_tsf: { name: string; amount_monthly: number; vatable: boolean }[]
  tsf: any
  insurance: any
  vat_on_tsf: boolean
  vat_on_insurance: boolean
  round_decimals: number
  solve_equilibrium: boolean
}

export default function Page() {
  const [loading, setLoading] = useState(false)
  const [totals, setTotals] = useState<any>(null)
  const [rows, setRows] = useState<any[]>([])

  const [form, setForm] = useState<CalcPayload>({
    asset_net: 10000000,
    vat_rate: 0.18,
    tenure_months: 36,
    annual_rate: 0.2,
    funding_rate: 0.12,
    grace_months: 0,
    balloon_percent: 0.0,
    vendor_payment_date_T: '2025-09-15',
    first_due_date_S: '2025-10-01',
    monthly_tsf: [],
    tsf: {
      tse_rate: 0.001,
      tapr_fixed: 25000,
      stamp_duty_fixed: 30000,
      online_reg_fixed: 6650,
      filing_minutes_fixed: 5000,
      cprf_rate_effective: 0.0003,
      tee_rate: 0.05,
      apply_tee: true,
      loan_reg_rate: 0.01,
      telematics_install_Q: 58500,
      telematics_monthly_R: 10000,
      irc_rate: 0.18,
      banking_fee_rate: 0.026,
      vat_telematics: true,
      vat_upfront_taxes: false,
    },
    insurance: {
      y1_amount: 0,
      y2_amount: 0,
      y3_amount: 0,
      cap_y1: true,
      cap_y2: true,
      cap_y3: true,
      vatable: true,
      y2_cap_month: 12,
      y3_cap_month: 24,
    },
    vat_on_tsf: true,
    vat_on_insurance: true,
    round_decimals: 0,
    solve_equilibrium: true,
  })

  const number = (v: number) => new Intl.NumberFormat().format(v ?? 0)

  async function calc() {
    setLoading(true)
    try {
      const res = await fetch(`${API}/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setTotals(data.totals)
      setRows(data.schedule)
    } catch (e: any) {
      alert('Calc failed: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  async function download(path: string, filename: string) {
    try {
      const res = await fetch(`${API}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (e: any) {
      alert('Download failed: ' + e.message)
    }
  }

  return (
    <div style={{ padding: 24, fontFamily: 'ui-sans-serif, system-ui' }}>
      <h1 style={{ fontSize: 22, fontWeight: 700 }}>IPA – FastAPI + Next.js</h1>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 16,
          marginTop: 16,
        }}
      >
        <label>
          Asset (net){' '}
          <input
            type="number"
            value={form.asset_net}
            onChange={(e) =>
              setForm({ ...form, asset_net: parseFloat(e.target.value) })
            }
          />
        </label>
        <label>
          VAT Rate{' '}
          <input
            type="number"
            step="0.01"
            value={form.vat_rate}
            onChange={(e) =>
              setForm({ ...form, vat_rate: parseFloat(e.target.value) })
            }
          />
        </label>
        <label>
          Tenure (months){' '}
          <input
            type="number"
            value={form.tenure_months}
            onChange={(e) =>
              setForm({ ...form, tenure_months: parseInt(e.target.value) })
            }
          />
        </label>
        <label>
          rc{' '}
          <input
            type="number"
            step="0.01"
            value={form.annual_rate}
            onChange={(e) =>
              setForm({ ...form, annual_rate: parseFloat(e.target.value) })
            }
          />
        </label>
        <label>
          rf{' '}
          <input
            type="number"
            step="0.01"
            value={form.funding_rate}
            onChange={(e) =>
              setForm({ ...form, funding_rate: parseFloat(e.target.value) })
            }
          />
        </label>
        <label>
          Balloon %{' '}
          <input
            type="number"
            step="0.01"
            value={form.balloon_percent}
            onChange={(e) =>
              setForm({ ...form, balloon_percent: parseFloat(e.target.value) })
            }
          />
        </label>
        <label>
          T (vendor payment){' '}
          <input
            type="date"
            value={form.vendor_payment_date_T}
            onChange={(e) =>
              setForm({ ...form, vendor_payment_date_T: e.target.value })
            }
          />
        </label>
        <label>
          S (first due date){' '}
          <input
            type="date"
            value={form.first_due_date_S}
            onChange={(e) =>
              setForm({ ...form, first_due_date_S: e.target.value })
            }
          />
        </label>
        <label>
          Rounding
          <select
            value={form.round_decimals}
            onChange={(e) =>
              setForm({ ...form, round_decimals: parseInt(e.target.value) })
            }
          >
            <option value={0}>0</option>
            <option value={1}>1</option>
            <option value={2}>2</option>
          </select>
        </label>
      </div>

      <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
        <button
          onClick={calc}
          disabled={loading}
          style={{ padding: '8px 12px' }}
        >
          {loading ? 'Calculating...' : 'Calculate'}
        </button>
        <button
          onClick={() => download('/export/xlsx', 'schedule.xlsx')}
          style={{ padding: '8px 12px' }}
        >
          Export XLSX
        </button>
        <button
          onClick={() => download('/export/pdf', 'schedule.pdf')}
          style={{ padding: '8px 12px' }}
        >
          Export PDF
        </button>
      </div>

      {totals && (
        <div style={{ marginTop: 24 }}>
          <h2 style={{ fontSize: 18 }}>Totals</h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: 8,
            }}
          >
            {Object.entries(totals).map(([k, v]) => (
              <div
                key={k}
                style={{ background: '#1111', padding: 8, borderRadius: 8 }}
              >
                <div style={{ fontSize: 12, color: '#444' }}>{k}</div>
                <div style={{ fontWeight: 600 }}>
                  {typeof v === 'number' ? number(v) : String(v)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {rows?.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h2 style={{ fontSize: 18 }}>Schedule (first 12)</h2>
          <div
            style={{
              maxHeight: 400,
              overflow: 'auto',
              border: '1px solid #ddd',
            }}
          >
            <table
              cellPadding={6}
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: 12,
              }}
            >
              <thead>
                <tr>
                  {Object.keys(rows[0]).map((h) => (
                    <th
                      key={h}
                      style={{
                        position: 'sticky',
                        top: 0,
                        background: '#fafafa',
                        borderBottom: '1px solid #ccc',
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, 12).map((r, i) => (
                  <tr key={i}>
                    {Object.values(r).map((v, j) => (
                      <td key={j} style={{ borderBottom: '1px solid #eee' }}>
                        {typeof v === 'number' ? number(v) : String(v)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
>>>>>>> 2fd963e (chore: Koyeb Procfile/runtime, env-driven CORS, frontend .envs, calc engine & tests)
}
