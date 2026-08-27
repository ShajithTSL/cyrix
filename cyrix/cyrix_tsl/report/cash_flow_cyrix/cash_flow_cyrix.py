# Copyright (c) 2026, TSL
# Cash Flow Statement — DIRECT METHOD, Company x Year grid + Consolidated, multi-currency.
#
# Columns: for each company -> one column per period (year/quarter/month), then a
# Consolidated block (sum across companies). Every figure is converted to the report
# Currency using the exchange rate on each transaction's posting date.
#
# Reconciliation: verified per company in LOCAL currency (always ties). The effect of
# converting to the report currency appears as an explicit "FX Translation on Cash"
# line, so Opening + Net Movement + FX Translation = Closing exactly.

from datetime import date, datetime, timedelta
import bisect
import calendar

import frappe
from frappe import _
from frappe.utils import flt, getdate, cint

SECTIONS = ("op_inflow", "nonop_inflow", "op_outflow", "investing", "fx")
CONSOL = "__consol__"


def execute(filters=None):
    filters = frappe._dict(filters or {})
    frappe.local.report_filters = filters
    validate_filters(filters)

    # ---- scope: companies + blocks ----
    base = [filters.company] if filters.get("company") else []
    extra = filters.get("consolidate_with_companies") or []
    if isinstance(extra, str):
        extra = [extra]
    companies = list(dict.fromkeys(base + extra))
    if not companies:
        frappe.throw(_("Select a Company (or companies to consolidate)."))
    show_consol = len(companies) > 1
    blocks = companies + ([CONSOL] if show_consol else [])

    comp_ccy = {c: frappe.get_cached_value("Company", c, "default_currency") for c in companies}
    comp_abbr = {c: frappe.get_cached_value("Company", c, "abbr") for c in companies}

    cost_centers = filters.get("cost_centers") or []
    if isinstance(cost_centers, str):
        cost_centers = [cc.strip() for cc in cost_centers.split(",") if cc.strip()]
    report_currency = filters.get("currency") or comp_ccy[companies[0]]
    rate_of = build_rate_lookup(set(comp_ccy.values()), report_currency)

    cash_accounts = get_cash_accounts(companies)
    if not cash_accounts:
        frappe.throw(_("No Cash / Bank accounts found."))

    periodicity = filters.get("periodicity") or "Yearly"
    fiscal_years = filters.get("fiscal_years") or []
    if isinstance(fiscal_years, str):
        fiscal_years = [fiscal_years]

    if fiscal_years:
        periods = build_periods_from_fiscal_years(
            fiscal_years, filters.get("from_date"), filters.get("to_date"))
        if not periods:
            # Clipping (or stray From/To defaults) removed every year — retry unclipped
            # so ticking years always shows those years.
            periods = build_periods_from_fiscal_years(fiscal_years, None, None)
    else:
        periods = build_periods(filters.from_date, filters.to_date, periodicity)
    if not periods:
        got = ", ".join(fiscal_years) if fiscal_years else "(none)"
        frappe.throw(_(
            "No periods to show. Selected fiscal years: {0}. "
            "Confirm these Fiscal Year records exist, or clear the From/To dates."
        ).format(got))

    pks = [p["key"] for p in periods]
    period_of = make_period_locator(periods)
    from_eff = min(p["from_date"] for p in periods)
    to_eff = max(p["to_date"] for p in periods)
    show_growth = bool(filters.get("show_growth")) and len(periods) >= 2

    # ---- pull + convert + bucket ----
    # master[section][label] = {"periods": {(block,pk): amt}, "children": {acct: {(block,pk): amt}}}
    master = {k: {} for k in SECTIONS}
    label_order = {k: [] for k in SECTIONS}
    # local (unconverted) net per company for the integrity check
    local_net = {c: 0.0 for c in companies}

    rows = get_contra_movements(companies, cash_accounts, from_eff, to_eff, cost_centers)
    for r in rows:
        pk = period_of(r.posting_date)
        if pk is None:
            continue
        local = flt(r.cash_flow)
        conv = local * rate_of(comp_ccy[r.company], r.posting_date)
        local_net[r.company] += local

        section, label = classify_direct(r.name, r.account_type, r.root_type,
                                         r.parent_account, local)
        if label not in master[section]:
            master[section][label] = {"periods": {}, "children": {}}
            label_order[section].append(label)
        m = master[section][label]
        _add(m["periods"], (r.company, pk), conv)
        display = strip_company_abbr(r.name, comp_abbr.get(r.company) or "") if show_consol else r.name
        child = m["children"].setdefault(display, {"vals": {}, "accounts": set()})
        _add(child["vals"], (r.company, pk), conv)
        child["accounts"].add(r.name)
        if show_consol:
            _add(m["periods"], (CONSOL, pk), conv)
            _add(child["vals"], (CONSOL, pk), conv)

    # ---- per (block,period) section totals ----
    def sec_total(section, block, pk):
        return sum(master[section][l]["periods"].get((block, pk), 0.0) for l in master[section])

    op_in = _grid(blocks, pks, lambda b, k: sec_total("op_inflow", b, k))
    nonop = _grid(blocks, pks, lambda b, k: sec_total("nonop_inflow", b, k))
    out_sgn = _grid(blocks, pks, lambda b, k: sec_total("op_outflow", b, k))
    inv = _grid(blocks, pks, lambda b, k: sec_total("investing", b, k))
    fx = _grid(blocks, pks, lambda b, k: sec_total("fx", b, k))

    total_in = _grid(blocks, pks, lambda b, k: op_in[(b, k)] + nonop[(b, k)])
    total_out = _grid(blocks, pks, lambda b, k: -out_sgn[(b, k)])
    op_cf = _grid(blocks, pks, lambda b, k: total_in[(b, k)] - total_out[(b, k)])
    net = _grid(blocks, pks, lambda b, k: op_cf[(b, k)] + inv[(b, k)] + fx[(b, k)])

    # ---- converted opening / closing / fx-translation plug ----
    opening, closing_actual, fx_trans = {}, {}, {}
    for p in periods:
        for c in companies:
            o_loc = get_cash_balance(c, p["from_date"], inclusive=False, cost_centers=cost_centers)
            cl_loc = get_cash_balance(c, p["to_date"], inclusive=True, cost_centers=cost_centers)
            o = o_loc * rate_of(comp_ccy[c], p["from_date"])
            cl = cl_loc * rate_of(comp_ccy[c], p["to_date"])
            opening[(c, p["key"])] = o
            closing_actual[(c, p["key"])] = cl
        if show_consol:
            opening[(CONSOL, p["key"])] = sum(opening[(c, p["key"])] for c in companies)
            closing_actual[(CONSOL, p["key"])] = sum(closing_actual[(c, p["key"])] for c in companies)
    for b in blocks:
        for k in pks:
            fx_trans[(b, k)] = closing_actual[(b, k)] - (opening[(b, k)] + net[(b, k)])

    # ---- LOCAL-currency integrity check (the real guard) ----
    recon = {}
    for c in companies:
        o = get_cash_balance(c, from_eff, inclusive=False, cost_centers=cost_centers)
        cl = get_cash_balance(c, to_eff, inclusive=True, cost_centers=cost_centers)
        recon[c] = flt(local_net[c] - (cl - o), 2)

    # ------------------------------ rows ------------------------------
    data = []
    hdr = _("Report Currency: {0}").format(report_currency)
    if show_consol:
        hdr += "   |   " + _("Consolidating: {0}").format(", ".join(companies))
    if cost_centers:
        hdr += "   |   " + _("Cost Centers: {0}").format(", ".join(cost_centers))
    data.append({"account": hdr})

    add_section(data, master, label_order, "op_inflow", _("Operating Cash Inflow"), +1, blocks, pks, filters, show_growth)
    add_total_row(data, _("Total Operating Cash Inflow"), op_in, blocks, pks, filters, show_growth)

    add_section(data, master, label_order, "nonop_inflow", _("Non-Operating Cash Inflow"), +1, blocks, pks, filters, show_growth)
    add_total_row(data, _("Total Non-Operating Cash Inflow"), nonop, blocks, pks, filters, show_growth)

    add_section(data, master, label_order, "op_outflow", _("Operating Cash Outflow"), -1, blocks, pks, filters, show_growth)
    add_total_row(data, _("Total Operating Cash Outflow"), total_out, blocks, pks, filters, show_growth)

    add_total_row(data, _("Operating Cash Flow  (Inflow \u2212 Outflow)"), op_cf, blocks, pks, filters, show_growth)

    add_section(data, master, label_order, "investing", _("Investing Activities"), +1, blocks, pks, filters, show_growth)
    add_total_row(data, _("Total Investing Activities Cash Flow"), inv, blocks, pks, filters, show_growth)

    add_section(data, master, label_order, "fx", _("Foreign Currency Gains / Losses"), +1, blocks, pks, filters, show_growth)
    add_total_row(data, _("Total Foreign Currency Gains / Losses"), fx, blocks, pks, filters, show_growth)

    add_total_row(data, _("NET CASH MOVEMENT"), net, blocks, pks, filters, show_growth)

    add_title(data, _("Summary"))
    add_total_row(data, _("Opening Balance"), opening, blocks, pks, filters, show_growth, indent=1)
    add_total_row(data, _("Net Cash Movement"), net, blocks, pks, filters, show_growth, indent=1)
    add_total_row(data, _("FX Translation on Cash"), fx_trans, blocks, pks, filters, show_growth, indent=1)
    add_total_row(data, _("Closing Cash Balance"), closing_actual, blocks, pks, filters, show_growth, indent=1)

    bad = [c for c in companies if recon[c]]
    status = _("\u2713 Reconciled (all companies, local currency)") if not bad \
        else _("\u26a0 Local mismatch in: {0}").format(", ".join(bad))
    data.append({"account": status, "indent": 1})

    columns = get_columns(blocks, periods, filters, show_growth)
    return columns, data


# ============================================================ helpers: scope/currency

def build_rate_lookup(from_currencies, to_currency):
    """rate(from_currency, on_date) -> report-currency multiplier, using the latest
    Currency Exchange on/before the date; reverse pair inverted; live fallback; else 1.0."""
    cache = {}
    for fc in from_currencies:
        if not fc or fc == to_currency:
            continue
        direct = frappe.get_all("Currency Exchange",
                                filters={"from_currency": fc, "to_currency": to_currency},
                                fields=["date", "exchange_rate"], order_by="date asc")
        if direct:
            cache[fc] = ([getdate(r["date"]) for r in direct],
                         [flt(r["exchange_rate"]) for r in direct], False)
            continue
        rev = frappe.get_all("Currency Exchange",
                             filters={"from_currency": to_currency, "to_currency": fc},
                             fields=["date", "exchange_rate"], order_by="date asc")
        if rev:
            cache[fc] = ([getdate(r["date"]) for r in rev],
                         [flt(r["exchange_rate"]) for r in rev], True)

    def rate(fc, on_date):
        if not fc or fc == to_currency:
            return 1.0
        entry = cache.get(fc)
        if not entry:
            try:
                from erpnext.setup.utils import get_exchange_rate
                return flt(get_exchange_rate(fc, to_currency, on_date)) or 1.0
            except Exception:
                return 1.0
        dates, rates, inverted = entry
        d = getdate(on_date)
        idx = bisect.bisect_right(dates, d) - 1
        r = rates[idx] if idx >= 0 else rates[0]
        if not r:
            return 1.0
        return (1.0 / r) if inverted else r

    return rate


def build_periods_from_fiscal_years(fy_names, from_date, to_date):
    """One period per selected ERPNext Fiscal Year, using its real start/end dates.
    If both From and To are set, each fiscal year is clipped to that window; a year
    that doesn't overlap is dropped. Columns are labelled by the fiscal year-end
    (e.g. 'Jul 26') and ordered oldest -> newest."""
    fd = getdate(from_date) if from_date else None
    td = getdate(to_date) if to_date else None
    periods = []
    for name in fy_names:
        fy = frappe.db.get_value("Fiscal Year", name,
                                 ["year_start_date", "year_end_date"], as_dict=True)
        if not fy:
            continue
        start, end = getdate(fy.year_start_date), getdate(fy.year_end_date)
        cstart = max(start, fd) if fd else start
        cend = min(end, td) if td else end
        if cstart > cend:
            continue
        periods.append({
            "key": "fy_" + "".join(ch if ch.isalnum() else "_" for ch in str(name)),
            "label": end.strftime("%b %y"),      # fiscal year-end, matches 'Jul 26'
            "from_date": cstart.isoformat(),
            "to_date": cend.isoformat(),
            "_sort": end,
        })
    periods.sort(key=lambda p: p["_sort"])
    return periods


def build_periods(from_date, to_date, periodicity):
    def d(x):
        return x if isinstance(x, date) else datetime.strptime(str(x)[:10], "%Y-%m-%d").date()
    start, end = d(from_date), d(to_date)
    periods, cur = [], start
    while cur <= end:
        if periodicity == "Monthly":
            last = date(cur.year, cur.month, calendar.monthrange(cur.year, cur.month)[1])
            label = cur.strftime("%b %Y")
        elif periodicity == "Quarterly":
            q = (cur.month - 1) // 3
            lm = q * 3 + 3
            last = date(cur.year, lm, calendar.monthrange(cur.year, lm)[1])
            label = "Q{} {}".format(q + 1, cur.year)
        else:
            last = date(cur.year, 12, 31)
            label = str(cur.year)
        p_end = min(last, end)
        periods.append({"key": "p_" + cur.isoformat().replace("-", "_"), "label": label,
                        "from_date": cur.isoformat(), "to_date": p_end.isoformat()})
        cur = last + timedelta(days=1)
    return periods


def make_period_locator(periods):
    bounds = [(getdate(p["from_date"]), getdate(p["to_date"]), p["key"]) for p in periods]

    def locate(posting_date):
        d = getdate(posting_date)
        for f, t, k in bounds:
            if f <= d <= t:
                return k
        return None
    return locate


def _add(dct, key, val):
    dct[key] = dct.get(key, 0.0) + val


def strip_company_abbr(name, abbr):
    """Collapse the same logical account across companies by removing the trailing
    ' - <company abbr>'. Uses the company's real abbreviation (which may be 'TSL',
    'TSL-UAE', or 'TSL - KSA'), so it works regardless of abbr punctuation:
    '1020201 - Accounts Receivable - TSL - KSA' -> '1020201 - Accounts Receivable'."""
    if abbr:
        suffix = " - " + abbr
        if name.endswith(suffix):
            return name[: -len(suffix)].strip()
    return name.strip()


def _grid(blocks, pks, fn):
    return {(b, k): fn(b, k) for b in blocks for k in pks}


# ============================================================ classification

def classify_direct(name, account_type, root_type, parent, cash_flow):
    lower = name.lower()
    par = (parent or "").lower()

    if "currency gain" in lower or "currency loss" in lower or "exchange gain" in lower or "exchange loss" in lower:
        return "fx", _("Realised / Unrealised Currency Gains / Losses")
    if account_type in ("Fixed Asset", "Capital Work in Progress", "Accumulated Depreciation"):
        return "investing", _("Fixed Assets")
    if "guarantee" in lower or "bid bond" in lower:
        return "investing", _("Bank Guarantees / Bid Bonds")
    if "end of service" in lower or "gratuity" in lower or "eos" in lower:
        return "investing", _("End of Service Benefit Provision")
    if "due to/from rp" in lower or "related part" in lower or "due related" in lower:
        return ("nonop_inflow", _("Due Related Parties")) if cash_flow >= 0 \
            else ("op_outflow", _("Due Parties (Related)"))
    if root_type == "Income":
        if "revenue from service" in lower or "service revenue" in lower:
            return "op_inflow", _("Revenue from Service")
        if "direct sale" in lower:
            return "op_inflow", _("Revenue from Direct Sales")
        if "automation" in lower:
            return "op_inflow", _("Revenue from Automation")
        if "tender" in lower:
            return "op_inflow", _("Revenue from SE Tender")
        if "interest" in lower:
            return "nonop_inflow", _("Interest Income")
        return "nonop_inflow", _("Other Revenue")
    if account_type == "Receivable":
        return "op_inflow", _("Collections from Trade Receivables")
    if "advance to suppl" in lower or "advance to vendor" in lower:
        return "op_outflow", _("Advance to Suppliers")
    if "advance from customer" in lower:
        return ("op_inflow", _("Advances Received from Customers")) if cash_flow >= 0 \
            else ("op_outflow", _("Advances Refunded to Customers"))
    if "staff loan" in lower or "staff advance" in lower or ("advance" in lower and "staff" in lower):
        return "op_outflow", _("Staff Loans / Advances")
    if "received but not billed" in lower:
        return "op_outflow", _("Stock Received but not Billed")
    if "doubtful" in lower:
        return "op_outflow", _("Loss on Doubtful Debts")
    if account_type == "Payable" or "creditor" in lower or "accounts payable" in lower:
        return "op_outflow", _("Payments to Suppliers / Payables")
    if account_type == "Tax" or "vat" in lower or "zakat" in lower:
        return "op_outflow", _("Tax / VAT / Zakat Payments")
    if root_type == "Expense":
        if "indirect" in par:
            return "op_outflow", _("Indirect Expenses")
        if "direct" in par or "cost of" in lower:
            return "op_outflow", _("Direct Expenses")
        return "op_outflow", _("Indirect Expenses")
    return ("op_inflow", _("Other Cash Inflows")) if cash_flow >= 0 \
        else ("op_outflow", _("Other Cash Outflows"))


# ============================================================ data pulls

def get_cash_accounts(companies):
    return frappe.get_all("Account",
                          filters={"company": ["in", companies], "account_type": ["in", ["Cash", "Bank"]]},
                          pluck="name")


def get_contra_movements(companies, cash_accounts, from_date, to_date, cost_centers=None):
    cc_cond = " AND gle.cost_center IN %(cost_centers)s" if cost_centers else ""
    return frappe.db.sql(
        f"""
        SELECT acc.name AS name, gle.company AS company, gle.posting_date AS posting_date,
               acc.account_type AS account_type, acc.root_type AS root_type,
               acc.parent_account AS parent_account,
               SUM(gle.credit - gle.debit) AS cash_flow
        FROM `tabGL Entry` gle
        INNER JOIN `tabAccount` acc ON acc.name = gle.account
        INNER JOIN (
            SELECT DISTINCT voucher_type, voucher_no
            FROM `tabGL Entry`
            WHERE company IN %(companies)s AND is_cancelled = 0
              AND account IN %(cash)s
              AND posting_date BETWEEN %(from_date)s AND %(to_date)s
        ) cv ON cv.voucher_type = gle.voucher_type AND cv.voucher_no = gle.voucher_no
        WHERE gle.company IN %(companies)s AND gle.is_cancelled = 0
          AND gle.account NOT IN %(cash)s
          AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
          {cc_cond}
        GROUP BY acc.name, gle.company, gle.posting_date,
                 acc.account_type, acc.root_type, acc.parent_account
        HAVING SUM(gle.credit - gle.debit) != 0
        """,
        {"companies": tuple(companies), "cash": tuple(cash_accounts),
         "from_date": from_date, "to_date": to_date,
         "cost_centers": tuple(cost_centers) if cost_centers else ("",)},
        as_dict=True,
    )


def get_cash_balance(company, on_date, inclusive=True, cost_centers=None):
    op = "<=" if inclusive else "<"
    cc_cond = " AND gle.cost_center IN %(cost_centers)s" if cost_centers else ""
    value = frappe.db.sql(
        f"""
        SELECT SUM(gle.debit - gle.credit)
        FROM `tabGL Entry` gle
        WHERE gle.company = %(company)s AND gle.is_cancelled = 0
          AND gle.posting_date {op} %(on_date)s
          AND gle.account IN (SELECT name FROM `tabAccount`
                              WHERE company = %(company)s AND account_type IN ('Cash','Bank'))
          {cc_cond}
        """,
        {"company": company, "on_date": on_date,
         "cost_centers": tuple(cost_centers) if cost_centers else ("",)},
    )[0][0]
    return flt(value)


# ============================================================ rendering

def _block_label(block):
    return _("Consolidated") if block == CONSOL else block


def get_columns(blocks, periods, filters, show_growth):
    prec = 0 if filters.get("remove_decimal") else 2
    pmap = {p["key"]: p for p in periods}
    cols = [{"fieldname": "account", "label": _("Particulars"), "fieldtype": "Data", "width": 380}]
    for bi, b in enumerate(blocks):
        for p in periods:
            cols.append({
                "fieldname": "c{}_{}".format(bi, p["key"]),
                "label": "{} {}".format(_block_label(b), p["label"]),
                "fieldtype": "Float", "precision": prec, "width": 130,
                # metadata so a clicked cell drills into GL matching this exact figure:
                "gl_company": "" if b == CONSOL else b,
                "gl_from_date": p["from_date"],
                "gl_to_date": p["to_date"],
            })
        if show_growth:
            cols.append({"fieldname": "c{}_growth".format(bi),
                         "label": "{} {}".format(_block_label(b), _("Growth %")),
                         "fieldtype": "Float", "precision": 1, "width": 100})
    return cols


def validate_filters(filters):
    if not filters.get("company") and not filters.get("consolidate_with_companies"):
        frappe.throw(_("Select a Company."))
    if not filters.get("fiscal_years") and not (filters.get("from_date") and filters.get("to_date")):
        frappe.throw(_("Select 'Compare With Years', or set both From Date and To Date."))


def growth_pct(vals_by_pk, pks):
    if len(pks) < 2:
        return ""
    prev, last = vals_by_pk.get(pks[-2], 0.0), vals_by_pk.get(pks[-1], 0.0)
    if not prev:
        return ""
    return flt((last - prev) / abs(prev) * 100.0, 1)


def _grid_cells(row, grid, blocks, pks, filters, show_growth, sign=1):
    prec = 0 if filters.get("remove_decimal") else 2
    for bi, b in enumerate(blocks):
        series = {}
        for k in pks:
            v = sign * grid.get((b, k), 0.0)
            row["c{}_{}".format(bi, k)] = flt(v, prec)
            series[k] = v
        if show_growth:
            row["c{}_growth".format(bi)] = growth_pct(series, pks)
    return row


def add_title(data, title):
    data.append({"account": title, "indent": 0})


def add_total_row(data, label, grid, blocks, pks, filters, show_growth, indent=0):
    row = {"account": label, "indent": indent}
    data.append(_grid_cells(row, grid, blocks, pks, filters, show_growth))


def add_section(data, master, label_order, section_key, title, sign, blocks, pks, filters, show_growth):
    add_title(data, title)
    for label in label_order[section_key]:
        m = master[section_key][label]
        all_accounts = sorted({a for ch in m["children"].values() for a in ch["accounts"]})
        prow = {"account": label, "indent": 1, "gl_accounts": all_accounts, "_sign": sign}
        data.append(_grid_cells(prow, m["periods"], blocks, pks, filters, show_growth, sign=sign))
        for cleaned in sorted(m["children"], key=lambda c: -abs(sum(m["children"][c]["vals"].values()))):
            ch = m["children"][cleaned]
            crow = {"account": cleaned, "indent": 2, "gl_accounts": sorted(ch["accounts"]), "_sign": sign}
            data.append(_grid_cells(crow, ch["vals"], blocks, pks, filters, show_growth, sign=sign))