# Copyright (c) 2026, TSL
# Cash Flow Drill — shows the exact cash movements behind a Cash Flow (Direct) cell.
#
# Reproduces the cash-flow figure precisely: the contra entries on vouchers that
# TOUCHED CASH, valued as (credit - debit) x sign. The Total row equals the clicked
# cash-flow cell exactly — which the standard General Ledger cannot do, because GL
# has no "cash-touching vouchers" filter and nets debit-credit instead.

import json

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = frappe._dict(filters or {})

    raw = filters.get("acct_list")
    if isinstance(raw, (list, tuple)):
        accounts = list(raw)
    else:
        try:
            accounts = json.loads(raw or "[]")
        except Exception:
            accounts = [a.strip() for a in (raw or "").split(",") if a.strip()]

    if not accounts:
        return get_columns(), [{
            "voucher_type": _("Open this from a Cash Flow figure — no account context received."),
        }]

    sign = flt(filters.get("sign") or 1) or 1

    raw_cc = filters.get("cost_centers")
    if isinstance(raw_cc, (list, tuple)):
        cost_centers = list(raw_cc)
    else:
        try:
            cost_centers = json.loads(raw_cc) if raw_cc else []
        except Exception:
            cost_centers = [c.strip() for c in (raw_cc or "").split(",") if c.strip()]

    if filters.get("company"):
        companies = [filters.company]
    else:
        companies = list(set(frappe.get_all(
            "Account", filters={"name": ["in", accounts]}, pluck="company")))

    cash_accounts = frappe.get_all(
        "Account",
        filters={"company": ["in", companies], "account_type": ["in", ["Cash", "Bank"]]},
        pluck="name")
    if not cash_accounts:
        frappe.throw(_("No cash/bank accounts for the drill scope."))

    cond_company = " AND gle.company = %(company)s" if filters.get("company") else ""
    cond_cc = " AND gle.cost_center IN %(cost_centers)s" if cost_centers else ""
    rows = frappe.db.sql(
        f"""
        SELECT gle.posting_date, gle.company, gle.account,
               gle.voucher_type, gle.voucher_no, gle.party,
               gle.debit, gle.credit, (gle.credit - gle.debit) AS cash_impact
        FROM `tabGL Entry` gle
        INNER JOIN (
            SELECT DISTINCT voucher_type, voucher_no
            FROM `tabGL Entry`
            WHERE is_cancelled = 0 AND account IN %(cash)s
              AND company IN %(companies)s
              AND posting_date BETWEEN %(from_date)s AND %(to_date)s
        ) cv ON cv.voucher_type = gle.voucher_type AND cv.voucher_no = gle.voucher_no
        WHERE gle.account IN %(accounts)s AND gle.is_cancelled = 0
          AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
          {cond_company}
          {cond_cc}
        ORDER BY gle.posting_date, gle.voucher_no
        """,
        {"accounts": tuple(accounts), "cash": tuple(cash_accounts),
         "companies": tuple(companies), "company": filters.get("company"),
         "cost_centers": tuple(cost_centers) if cost_centers else ("",),
         "from_date": filters.from_date, "to_date": filters.to_date},
        as_dict=True,
    )

    data, total = [], 0.0
    for r in rows:
        impact = flt(r.cash_impact) * sign
        total += impact
        data.append({
            "posting_date": r.posting_date,
            "voucher_type": r.voucher_type,
            "voucher_no": r.voucher_no,
            "party": r.party,
            "account": r.account,
            "debit": flt(r.debit),
            "credit": flt(r.credit),
            "cash_impact": impact,
        })

    data.append({
        "voucher_type": _("TOTAL  (= Cash Flow figure)"),
        "cash_impact": flt(total, 2),
        "debit": sum(d["debit"] for d in data),
        "credit": sum(d["credit"] for d in data),
    })

    return get_columns(), data


def get_columns():
    return [
        {"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 140},
        {"label": _("Voucher No"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link",
         "options": "voucher_type", "width": 170},
        {"label": _("Party"), "fieldname": "party", "fieldtype": "Data", "width": 160},
        {"label": _("Account"), "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 240},
        {"label": _("Debit"), "fieldname": "debit", "fieldtype": "Float", "width": 120},
        {"label": _("Credit"), "fieldname": "credit", "fieldtype": "Float", "width": 120},
        {"label": _("Cash Impact"), "fieldname": "cash_impact", "fieldtype": "Float", "width": 130},
    ]