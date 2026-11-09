"""Saturday Off Schedule page for ERPNext v16 (/app/saturday-off-schedul).

No custom DocTypes. Employees come from the standard Employee DocType
(Employee Number = SR #). Schedules, swaps and settings are stored as JSON in
DefaultValue under the parent "__saturday_roster". One month record holds every
employee; the Company / Branch / Employee filters choose what the page shows.
"""

import csv
import io
import json
import re

import frappe
from frappe import _
from frappe.utils import add_days, add_to_date, cint, get_datetime, get_last_day, getdate, now_datetime, sbool, today

PARENT = "__saturday_roster"
HR_ROLES = {"HR Manager", "HR User", "System Manager"}
CODES = ("Y", "N", "VAC", "OT", "WFH", "PH", "SH")
LABELS = {"Y": "Yes", "N": "No", "VAC": "Vacation", "OT": "OT", "WFH": "WFH", "PH": "PH", "SH": "Yes*"}
NO_SWAP = {"VAC", "PH"}
WORKING = {"Y", "OT", "WFH", "SH"}
OPEN = ("Awaiting Partner", "Awaiting Approval")
DEFAULT_SETTINGS = {
	"subtitle": "Human Resources Department",
	"footer": "This document is for internal use only | HR & Administration Department",
	"cutoff_hours": 24,
	"headings": {},  # {company: {"title": ..., "subtitle": ..., "footer": ...}}
}


# ------------------------------------------------------------------ storage
def _load(key, default=None):
	raw = frappe.db.get_default(key, parent=PARENT)
	if isinstance(raw, list):
		raw = raw[0] if raw else None
	return json.loads(raw) if raw else default


def _save(key, value):
	frappe.db.set_default(key, json.dumps(value, separators=(",", ":")), parent=PARENT)


def _month(ym):
	return _load(f"month:{ym}")


def _save_month(ym, month):
	month["updatedAt"] = str(now_datetime())
	month["updatedBy"] = frappe.session.user
	_save(f"month:{ym}", month)
	index = set(_load("months_index", []))
	if ym not in index:
		index.add(ym)
		_save("months_index", sorted(index))


def _swaps(ym):
	return _load(f"swaps:{ym}", {})


def _settings():
	s = dict(DEFAULT_SETTINGS)
	s.update(_load("settings", {}) or {})
	s["headings"] = s.get("headings") or {}
	return s


# ------------------------------------------------------------------ helpers
def _is_hr():
	return bool(HR_ROLES & set(frappe.get_roles()))


def _require_access():
	if frappe.session.user == "Guest" or not ((HR_ROLES | {"Employee"}) & set(frappe.get_roles())):
		frappe.throw(_("You don't have access to the Saturday Off Schedule."), frappe.PermissionError)


def _require_hr():
	_require_access()
	if not _is_hr():
		frappe.throw(_("Only HR can do this."), frappe.PermissionError)


def _my_employee():
	return frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")


def _check_ym(ym):
	if not re.fullmatch(r"\d{4}-\d{2}", ym or ""):
		frappe.throw(_("Invalid month."))
	return ym


def _saturdays(ym):
	first = getdate(f"{ym}-01")
	last = getdate(get_last_day(first))
	day = getdate(add_days(first, (5 - first.weekday()) % 7))  # Saturday = 5
	out = []
	while day <= last:
		out.append(str(day))
		day = getdate(add_days(day, 7))
	return out


def _past(d):
	return d < today()


def _head(d):
	return getdate(d).strftime("%d-%b-%Y").upper()


def _filters(company=None, branch=None, employee=None):
	return frappe._dict(company=company or None, branch=branch or None, employee=employee or None)


def _active_employees(f, ignore_employee=False):
	q = {"status": "Active", "saudization": 0}
	if f.company:
		q["company"] = f.company
	if f.branch:
		q["branch"] = f.branch
	if f.employee and not ignore_employee:
		q["name"] = f.employee
	return frappe.get_all(
		"Employee",
		filters=q,
		fields=["name", "employee_name", "employee_number", "company", "branch"],
		order_by="employee_number asc, name asc",
	)


def _meta(month, ids):
	"""company/branch/name/sr for ids, from the month snapshot or the Employee record."""
	names = (month or {}).get("names", {})
	out = {i: dict(names[i]) for i in ids if i in names}
	need = [i for i in ids if i not in out or "company" not in out[i]]
	if need:
		for e in frappe.get_all(
			"Employee", filters={"name": ["in", need]}, fields=["name", "employee_name", "employee_number", "company", "branch"]
		):
			base = out.get(e.name, {})
			out[e.name] = {
				"sr": base.get("sr", e.employee_number or ""),
				"name": base.get("name", e.employee_name),
				"company": e.company,
				"branch": e.branch,
			}
	for i in ids:
		out.setdefault(i, {"sr": "", "name": _("Removed employee"), "company": None, "branch": None})
	return out


def _match(m, f):
	return (not f.company or m.get("company") == f.company) and (not f.branch or m.get("branch") == f.branch)


def _snapshot(month, emp):
	month.setdefault("names", {})[emp.name] = {
		"sr": emp.employee_number or "",
		"name": emp.employee_name,
		"company": emp.company,
		"branch": emp.branch,
	}
	if emp.name not in month.setdefault("roster", []):
		month["roster"].append(emp.name)


def _remember(month, emp_id):
	emp = frappe.db.get_value(
		"Employee", emp_id, ["name", "employee_name", "employee_number", "company", "branch"], as_dict=True
	)
	if emp:
		_snapshot(month, emp)


def _rows(ym, month, f):
	"""Rows for the sheet. Past months use their saved roster, so they stay as recorded."""
	locked = all(_past(d) for d in _saturdays(ym))
	if month and locked:
		ids = month.get("roster", [])
		meta = _meta(month, ids)
		rows = [
			{"id": i, "sr": meta[i]["sr"], "name": meta[i]["name"]}
			for i in ids
			if _match(meta[i], f) and (not f.employee or i == f.employee)
		]
		return rows, locked
	order = {e: n for n, e in enumerate((month or {}).get("roster", []))}
	emps = _active_employees(f)
	emps.sort(key=lambda e: order.get(e.name, 10**6))
	return [{"id": e.name, "sr": e.employee_number or "", "name": e.employee_name} for e in emps], locked


def _heading(settings, company):
	h = settings["headings"].get(company or "_all", {})
	default_title = (
		frappe.db.get_value("Company", company, "company_name") if company else _("All Companies")
	)
	return {
		"title": h.get("title") or default_title,
		"subtitle": h.get("subtitle") or settings.get("subtitle"),
		"footer": h.get("footer") or settings.get("footer"),
		"custom": bool(h.get("title")),
	}


def _name(emp_id, month=None):
	if month and emp_id in month.get("names", {}):
		return month["names"][emp_id]["name"]
	return frappe.db.get_value("Employee", emp_id, "employee_name") or emp_id


def _user_of(emp_id):
	return frappe.db.get_value("Employee", emp_id, "user_id")


def _notify(users, subject):
	users = [u for u in set(users) if u and u != frappe.session.user]
	if not users:
		return
	try:
		from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification

		enqueue_create_notification(
			users, {"type": "Alert", "subject": subject, "from_user": frappe.session.user, "link": "/app/saturday-off-schedul"}
		)
	except Exception:
		frappe.log_error(title="Saturday roster notification failed")


# ------------------------------------------------------------------ read
@frappe.whitelist()
def get_data(ym=None, company=None, branch=None, employee=None):
	_require_access()
	ym = _check_ym(ym or today()[:7])
	f = _filters(company, branch, employee)
	settings = _settings()
	month = _month(ym)
	rows, locked = _rows(ym, month, f)
	status = (month or {}).get("status", {})
	missing = [r["id"] for r in rows if not status.get(r["id"])] if month and not locked else []

	# People who can be picked in the swap dialog: same company/branch, ignoring the employee filter
	people = [
		{"id": e.name, "sr": e.employee_number or "", "name": e.employee_name}
		for e in _active_employees(f, ignore_employee=True)
	]

	# Swaps that involve someone in the current filter
	if f.company or f.branch or f.employee:
		scope = {e.name for e in _active_employees(f)} if (f.company or f.branch) else set()
		if f.employee:
			scope = {f.employee}
	else:
		scope = None
	swaps = []
	for key in _load("months_index", []):
		for s in _swaps(key).values():
			if scope is None or s["emp"] in scope or s["partner"] in scope:
				swaps.append(s)
	swaps.sort(key=lambda s: s["createdAt"], reverse=True)

	return {
		"api_version": 3,
		"filters": f,
		"ym": ym,
		"today": today(),
		"saturdays": _saturdays(ym),
		"heading": _heading(settings, f.company),
		"settings": {k: settings[k] for k in ("subtitle", "footer", "cutoff_hours")},
		"month": {"status": status} if month else None,
		"rows": rows,
		"missing": len(missing),
		"locked": locked,
		"months": _load("months_index", []),
		"swaps": swaps[:300],
		"people": people,
		"ctx": {"is_hr": _is_hr(), "employee": _my_employee(), "user": frappe.session.user},
	}


@frappe.whitelist()
def get_history(period="all", company=None, branch=None, employee=None):
	_require_access()
	f = _filters(company, branch, employee)
	index = _load("months_index", [])
	three_months_ago = str(add_to_date(getdate(today()), months=-3))
	stats, sats = {}, set()

	def in_period(d, ym):
		if period == "all":
			return True
		if period == "3m":
			return d >= three_months_ago
		if len(period) == 4:
			return d.startswith(period)
		return ym == period

	for ym in index:
		month = _month(ym) or {}
		ids = list(month.get("status", {}).keys())
		meta = _meta(month, ids)
		keep = {i for i in ids if _match(meta[i], f) and (not f.employee or i == f.employee)}
		month_days = set()
		for d in _saturdays(ym):
			if not _past(d) or not in_period(d, ym):
				continue
			for emp in keep:
				code = month["status"][emp].get(d)
				if not code:
					continue
				sats.add(d)
				month_days.add(d)
				row = stats.setdefault(
					emp, {"sr": meta[emp]["sr"], "name": meta[emp]["name"], "swaps": 0, **{c: 0 for c in CODES}}
				)
				row[code] += 1
		for s in _swaps(ym).values():
			if s["status"] == "Approved" and s["date"] in month_days:
				for emp in (s["emp"], s["partner"]):
					if emp in stats:
						stats[emp]["swaps"] += 1

	rows = sorted(stats.values(), key=lambda r: (int(r["sr"]) if str(r["sr"]).isdigit() else 10**9, r["name"]))
	past_months = [ym for ym in index if any(_past(d) for d in _saturdays(ym))]
	return {
		"rows": rows,
		"saturdays": len(sats),
		"months": sorted(past_months, reverse=True),
		"years": sorted({ym[:4] for ym in past_months}, reverse=True),
	}


# ------------------------------------------------------------------ Excel (export, template, import)
XL_STYLE = {  # code: (fill, font colour, bold) — same colours as the sheet
	"Y": ("F1F2F4", "6B7280", False),
	"N": ("DCEFD9", "1E6B27", True),
	"VAC": ("FFF2C2", "7A5800", True),
	"OT": ("ECE6F8", "4B2C91", True),
	"WFH": ("FFE7CC", "8A4B00", True),
	"PH": ("D4EEF6", "0B5D78", True),
	"SH": ("FCE1EC", "A3164F", True),
}
XL_LEGEND = [
	("Y", "YES", "Employee is working this Saturday"),
	("N", "NO", "Employee is off this Saturday"),
	("VAC", "Vacation", "Employee on approved annual leave"),
	("OT", "OT", "Overtime scheduled"),
	("WFH", "WFH", "Working from home"),
	("PH", "PH", "Public holiday – all staff off"),
	("SH", "YES*", "Off / working on shift arrangement"),
]
ID_HEADER = "Employee ID (do not change)"
IMPORT_VALUES = {v.lower(): k for k, v in LABELS.items()}
IMPORT_VALUES.update({"y": "Y", "n": "N", "vac": "VAC", "shift arrangement": "SH", "clear": "", "—": "", "-": ""})


def _write_sheet(ws, ym, f, rows, status, h, template=False):
	"""Draw the sheet. template=True adds dropdowns, live colours and the Employee ID column."""
	from openpyxl.formatting.rule import CellIsRule
	from openpyxl.styles import Alignment, Border, Font, PatternFill, Protection, Side
	from openpyxl.utils import get_column_letter
	from openpyxl.worksheet.datavalidation import DataValidation

	sats = _saturdays(ym)
	ncol = 2 + len(sats) + (1 if template else 0)
	side = Side(style="thin", color="B9C7DD")
	border = Border(left=side, right=side, top=side, bottom=side)
	center = Alignment(horizontal="center", vertical="center", wrap_text=True)
	fill = lambda c: PatternFill("solid", fgColor=c)  # noqa: E731
	font = lambda **k: Font(name="Calibri", **k)  # noqa: E731

	def band(r, text, bg, size, bold=True, italic=False):
		ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncol)
		c = ws.cell(r, 1, text)
		c.font, c.fill, c.alignment = font(bold=bold, italic=italic, size=size, color="FFFFFF"), fill(bg), center
		for col in range(2, ncol + 1):
			ws.cell(r, col).fill = fill(bg)
		ws.row_dimensions[r].height = size * 1.9

	month_title = getdate(f"{ym}-01").strftime("%B %Y").upper()
	band(1, h["title"], "0E2B5C", 16)
	band(2, f"Saturday Off Schedule — {month_title}", "173F7E", 13)
	r = 2
	sub = " — ".join(x for x in (h["subtitle"], f.branch) if x)
	if sub:
		r += 1
		band(r, sub, "0E2B5C", 10, bold=False, italic=True)
	if template:
		r += 1
		ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncol)
		c = ws.cell(
			r, 1,
			"Pick a value from the dropdown in each Saturday cell: Yes, No, Vacation, OT, WFH, PH, Yes*, or Clear. "
			"Empty cells are left unchanged. Past Saturdays are ignored. Don't change the headings or the Employee ID column.",
		)
		c.font, c.alignment, c.fill = font(italic=True, size=9, color="7A5800"), Alignment(wrap_text=True, vertical="center"), fill("FFF8E1")
		ws.row_dimensions[r].height = 30

	r += 1
	header_row = r
	headers = ["SR #", "Employee Name"] + [
		f"{_head(d)}\n(Sat){' – past' if template and _past(d) else ''}" for d in sats
	]
	if template:
		headers.append(ID_HEADER)
	for i, text in enumerate(headers, 1):
		c = ws.cell(r, i, text)
		c.font, c.alignment, c.border = font(bold=True, color="FFFFFF"), center, border
		c.fill = fill("9AA3B2" if template and text == ID_HEADER else "2E6DB4")
	ws.row_dimensions[r].height = 32

	work, off = [0] * len(sats), [0] * len(sats)
	first_data = r + 1
	for n, row in enumerate(rows):
		r += 1
		alt = "E4EEF8" if n % 2 else "FFFFFF"
		sr = row["sr"]
		c = ws.cell(r, 1, int(sr) if str(sr).isdigit() else sr)
		c.alignment, c.fill, c.border, c.font = center, fill(alt), border, font()
		c = ws.cell(r, 2, row["name"])
		c.alignment, c.fill, c.border, c.font = Alignment(vertical="center"), fill(alt), border, font()
		for i, d in enumerate(sats):
			code = status.get(row["id"], {}).get(d, "")
			if code:
				(work if code in WORKING else off)[i] += 1
			c = ws.cell(r, 3 + i, LABELS.get(code, "" if template else "—"))
			c.alignment, c.border = center, border
			if template:
				c.font = font()
				if not _past(d):
					c.protection = Protection(locked=False)  # only upcoming Saturday cells can be edited
				if _past(d):
					c.fill = fill("EEEEEE")
					c.font = font(color="9AA3B2")
			else:
				bg, fg, bold = XL_STYLE.get(code, ("FFFFFF", "9AA3B2", False))
				c.fill, c.font = fill(bg), font(color=fg, bold=bold)
		if template:
			c = ws.cell(r, ncol, row["id"])
			c.font, c.border, c.fill = font(size=9, color="6B7280"), border, fill("F4F5F6")
	last_data = r

	if template and rows:
		rng = f"C{first_data}:{get_column_letter(2 + len(sats))}{last_data}"
		for code, (bg, fg, bold) in XL_STYLE.items():
			ws.conditional_formatting.add(
				rng,
				CellIsRule(
					operator="equal",
					formula=[f'"{LABELS[code]}"'],
					fill=PatternFill("solid", start_color=bg, end_color=bg),
					font=Font(color=fg, bold=bold),
				),
			)
		dv = DataValidation(
			type="list",
			formula1='"Yes,No,Vacation,OT,WFH,PH,Yes*,Clear"',
			allow_blank=True,
			showErrorMessage=True,
			errorTitle="Invalid status",
			error="Choose Yes, No, Vacation, OT, WFH, PH, Yes* or Clear.",
		)
		ws.add_data_validation(dv)
		dv.add(rng)
	else:
		for label, counts in (("Working", work), ("Off", off)):
			r += 1
			ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
			c = ws.cell(r, 1, label)
			c.font, c.alignment = font(bold=True), Alignment(horizontal="right", vertical="center")
			for col in range(1, ncol + 1):
				ws.cell(r, col).fill, ws.cell(r, col).border = fill("E4EEF8"), border
			for i, n in enumerate(counts):
				c = ws.cell(r, 3 + i, n)
				c.font, c.alignment = font(bold=True), center

	r += 2
	ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
	c = ws.cell(r, 1, "Legend / Key")
	c.font, c.fill, c.alignment = font(bold=True, color="FFFFFF"), fill("0E2B5C"), center
	ws.cell(r, 2).fill = fill("0E2B5C")
	for code, key, desc in XL_LEGEND:
		r += 1
		bg, fg, _bold = XL_STYLE[code]
		c = ws.cell(r, 1, key)
		c.fill, c.font, c.alignment, c.border = fill(bg), font(color=fg, bold=True), center, border
		c = ws.cell(r, 2, desc)
		c.border, c.font = border, font()

	if h.get("footer") and not template:
		r += 2
		ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncol)
		c = ws.cell(r, 1, h["footer"])
		c.font, c.alignment, c.fill = font(italic=True, size=9, color="6B7280"), center, fill("E4EEF8")

	ws.column_dimensions["A"].width = 10
	ws.column_dimensions["B"].width = 36
	for i in range(len(sats)):
		ws.column_dimensions[get_column_letter(3 + i)].width = 16
	if template:
		ws.column_dimensions[get_column_letter(ncol)].width = 24
	if template:
		# Protect the headings, names and IDs (no password) so Find & Replace can't change them.
		# Column widths and row heights can still be adjusted.
		ws.protection.sheet = True
		ws.protection.formatColumns = False
		ws.protection.formatRows = False
		ws.protection.formatCells = False
		# Hidden sheet that tells the importer which column is which Saturday,
		# so the import works even if the heading text gets changed.
		meta = ws.parent.create_sheet("_meta")
		meta["A1"], meta["B1"] = "saturday_off_schedul", ym
		meta["A2"], meta["B2"] = "id_col", ncol
		meta["A3"], meta["B3"] = "header_row", header_row
		for i, d in enumerate(sats):
			meta.cell(4 + i, 1, 3 + i)
			meta.cell(4 + i, 2, d)
		meta.sheet_state = "veryHidden"
	ws.freeze_panes = ws.cell(header_row + 1, 3)
	ws.print_title_rows = f"{header_row}:{header_row}"
	ws.page_setup.orientation = "portrait"
	ws.page_setup.paperSize = ws.PAPERSIZE_A4
	ws.sheet_properties.pageSetUpPr.fitToPage = True
	ws.page_setup.fitToWidth = 1
	ws.page_setup.fitToHeight = 0
	ws.print_options.horizontalCentered = True


def _send_xlsx(wb, filename):
	out = io.BytesIO()
	wb.save(out)
	frappe.response["filename"] = filename
	frappe.response["filecontent"] = out.getvalue()
	frappe.response["type"] = "binary"


@frappe.whitelist()
def export_xlsx(ym, company=None, branch=None, employee=None):
	"""Download the month as a coloured .xlsx that looks like the printed sheet."""
	_require_access()
	from openpyxl import Workbook

	ym = _check_ym(ym)
	f = _filters(company, branch, employee)
	month = _month(ym)
	if not month:
		frappe.throw(_("There is no schedule for this month yet."))
	rows, _locked = _rows(ym, month, f)
	wb = Workbook()
	wb.active.title = getdate(f"{ym}-01").strftime("%b %Y")
	_write_sheet(wb.active, ym, f, rows, month.get("status", {}), _heading(_settings(), f.company))
	name = re.sub(r"[^\w-]+", "-", f.company or "All")
	_send_xlsx(wb, f"Saturday-Off-{name}-{ym}.xlsx")


@frappe.whitelist()
def download_template(ym, company=None, branch=None, employee=None):
	"""Excel template for import: current statuses, dropdowns, live colours and Employee IDs."""
	_require_hr()
	from openpyxl import Workbook

	ym = _check_ym(ym)
	f = _filters(company, branch, employee)
	month = _month(ym) or {}
	locked = all(_past(d) for d in _saturdays(ym))
	if locked:
		frappe.throw(_("All Saturdays in this month have passed, so it can't be imported."))
	rows, _locked = _rows(ym, month or None, f)
	if not rows:
		frappe.throw(_("No employees match these filters."))
	wb = Workbook()
	wb.active.title = getdate(f"{ym}-01").strftime("%b %Y")
	_write_sheet(wb.active, ym, f, rows, month.get("status", {}), _heading(_settings(), f.company), template=True)
	name = re.sub(r"[^\w-]+", "-", f.company or "All")
	_send_xlsx(wb, f"Saturday-Off-Template-{name}-{ym}.xlsx")


def _read_upload(file_url):
	from openpyxl import load_workbook

	name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not name:
		frappe.throw(_("Uploaded file not found. Upload it again."))
	file_doc = frappe.get_doc("File", name)
	if not (file_doc.file_name or file_url).lower().endswith(".xlsx"):
		frappe.throw(_("Upload an .xlsx file (the template downloaded from this page)."))
	content = file_doc.get_content()
	if isinstance(content, str):
		content = content.encode()
	try:
		wb = load_workbook(io.BytesIO(content), data_only=True)
	except Exception:
		frappe.throw(_("This file couldn't be read as an Excel workbook."))
	return file_doc, wb


def _header_date(value):
	from datetime import date, datetime

	if isinstance(value, datetime):
		return str(value.date())
	if isinstance(value, date):
		return str(value)
	m = re.match(r"\s*(\d{1,2}-[A-Za-z]{3}-\d{4})", str(value or ""))
	if not m:
		return None
	try:
		return str(datetime.strptime(m.group(1).title(), "%d-%b-%Y").date())
	except ValueError:
		return None


@frappe.whitelist()
def import_xlsx(file_url, company=None, dry_run=1):
	"""Check (dry_run=1) or apply (dry_run=0) an uploaded template.
	Nothing is saved if the file has errors. Empty cells and past Saturdays are left unchanged."""
	_require_hr()
	dry = sbool(dry_run)
	file_doc, wb = _read_upload(file_url)
	ws = next((w for w in wb.worksheets if w.title != "_meta"), wb.worksheets[0])

	header_row, date_cols, id_col = None, {}, None
	if "_meta" in wb.sheetnames and wb["_meta"]["A1"].value == "saturday_off_schedul":
		# Template from this page: column positions come from the hidden sheet
		meta = wb["_meta"]
		id_col = cint(meta["B2"].value) or None
		header_row = cint(meta["B3"].value) or None
		r = 4
		while meta.cell(r, 1).value:
			date_cols[cint(meta.cell(r, 1).value)] = str(meta.cell(r, 2).value)[:10]
			r += 1
	else:
		for r in range(1, min(ws.max_row, 40) + 1):
			if str(ws.cell(r, 1).value or "").strip().upper().startswith("SR"):
				header_row = r
				break
		if not header_row:
			frappe.throw(_("Couldn't find the 'SR #' heading row. Use the template downloaded from this page."))
		for c in range(1, ws.max_column + 1):
			v = ws.cell(header_row, c).value
			d = _header_date(v)
			if d:
				date_cols[c] = d
			elif str(v or "").strip().lower().startswith("employee id"):
				id_col = c
	if not date_cols:
		frappe.throw(_("No Saturday columns found in the heading row (expected dates like 07-NOV-2026). Download a fresh template."))
	months = {d[:7] for d in date_cols.values()}
	if len(months) != 1:
		frappe.throw(_("All Saturday columns must be in the same month."))
	ym = months.pop()
	not_sat = [d for d in date_cols.values() if d not in _saturdays(ym)]
	if not_sat:
		frappe.throw(_("These columns are not Saturdays: {0}").format(", ".join(not_sat)))

	month = _month(ym) or {"status": {}, "roster": [], "names": {}}
	status = month.setdefault("status", {})
	errors, changed, seen = [], [], set()
	skipped_past = unchanged = 0
	transitions = {}

	for r in range(header_row + 1, ws.max_row + 1):
		sr_val, name = ws.cell(r, 1).value, ws.cell(r, 2).value
		if (sr_val in (None, "")) and not name:
			continue
		if str(sr_val or "").strip().lower() in ("legend / key", "working", "off"):
			break
		sr = str(int(sr_val)) if isinstance(sr_val, float) and sr_val.is_integer() else str(sr_val or "").strip()
		label = f"{_('Row')} {r} ({sr} {name or ''})".strip()

		emp = None
		if id_col:
			eid = str(ws.cell(r, id_col).value or "").strip()
			if eid and frappe.db.exists("Employee", eid):
				emp = eid
		if not emp and sr:
			q = {"employee_number": sr}
			if company:
				q["company"] = company
			emp = frappe.db.get_value("Employee", q, "name")
		if not emp:
			errors.append(_("{0}: no employee found with this SR #.").format(label))
			continue
		if company and frappe.db.get_value("Employee", emp, "company") != company:
			errors.append(_("{0}: employee belongs to another company.").format(label))
			continue
		if emp in seen:
			errors.append(_("{0}: this employee appears more than once.").format(label))
			continue
		seen.add(emp)

		for c, d in date_cols.items():
			raw = ws.cell(r, c).value
			if raw is None or str(raw).strip() == "":
				continue
			key = str(raw).strip().lower()
			if key not in IMPORT_VALUES:
				errors.append(_("{0}, {1}: '{2}' isn't a valid status.").format(label, _head(d), raw))
				continue
			code = IMPORT_VALUES[key]
			old = status.get(emp, {}).get(d, "")
			if code == old:
				unchanged += 1
				continue
			if _past(d):
				skipped_past += 1
				continue
			changed.append((emp, d, code))
			move = f"{LABELS.get(old, '—')} → {LABELS.get(code, '—')}"
			transitions[move] = transitions.get(move, 0) + 1

	result = {
		"ym": ym,
		"changes": len(changed),
		"employees": len({e for e, _d, _c in changed}),
		"rows": len(seen),
		"unchanged": unchanged,
		"skipped_past": skipped_past,
		"errors": errors[:50],
		"error_count": len(errors),
		"changed_cells": [f"{e}|{d}" for e, d, _c in changed],
		"transitions": sorted(transitions.items(), key=lambda x: -x[1]),
		"cells": len(changed) + unchanged,
	}
	if dry:
		return result
	if errors:
		frappe.throw(_("Fix the errors in the file first. Nothing was imported."))

	for emp, d, code in changed:
		_remember(month, emp)
		status.setdefault(emp, {})[d] = code
	if changed:
		_save_month(ym, month)
	frappe.delete_doc("File", file_doc.name, ignore_permissions=True)
	return result


@frappe.whitelist()
def discard_upload(file_url):
	"""Remove an uploaded template that wasn't imported."""
	_require_hr()
	name = frappe.db.get_value("File", {"file_url": file_url, "owner": frappe.session.user}, "name")
	if name:
		frappe.delete_doc("File", name, ignore_permissions=True)
	return True


# ------------------------------------------------------------------ schedule (HR)
@frappe.whitelist()
def create_month(ym, company=None, branch=None):
	"""Create the month (or add employees missing from it), continuing each person's Yes/No pattern."""
	_require_hr()
	ym = _check_ym(ym)
	f = _filters(company, branch)
	sats = _saturdays(ym)
	upcoming = [d for d in sats if not _past(d)]
	if not upcoming:
		frappe.throw(_("All Saturdays in this month have passed."))

	month = _month(ym) or {"status": {}, "roster": [], "names": {}}
	emps = [e for e in _active_employees(f) if not month["status"].get(e.name)]
	if not emps:
		frappe.throw(_("Everyone in this filter already has Saturdays set for this month."))

	previous = [_month(m) or {} for m in sorted((m for m in _load("months_index", []) if m < ym), reverse=True)]
	for i, emp in enumerate(emps):
		last = None
		for prev in previous:
			days = prev.get("status", {}).get(emp.name, {})
			for d in sorted(days, reverse=True):
				if days[d] in ("Y", "N"):
					last = (d, days[d])
					break
			if last:
				break
		if last:
			weeks = (getdate(upcoming[0]) - getdate(last[0])).days // 7
			cur = last[1] if weeks % 2 == 0 else ("N" if last[1] == "Y" else "Y")
		else:
			cur = "N" if i % 2 == 0 else "Y"
		month["status"][emp.name] = {}
		for d in upcoming:  # passed Saturdays stay empty for late additions
			month["status"][emp.name][d] = cur
			cur = "N" if cur == "Y" else "Y"
		_snapshot(month, emp)
	_save_month(ym, month)
	return len(emps)


@frappe.whitelist()
def set_cell(ym, employee, date, code=""):
	_require_hr()
	ym = _check_ym(ym)
	month = _month(ym)
	if not month:
		frappe.throw(_("Create the schedule first."))
	if date not in _saturdays(ym):
		frappe.throw(_("{0} is not a Saturday in this month.").format(date))
	if _past(date):
		frappe.throw(_("{0} has already passed and is part of the log.").format(_head(date)))
	if code and code not in CODES:
		frappe.throw(_("Invalid status."))
	_remember(month, employee)
	month.setdefault("status", {}).setdefault(employee, {})[date] = code
	_save_month(ym, month)
	return True


@frappe.whitelist()
def bulk_set_cells(ym, employees, dates, code=""):
	"""Set many cells at once. code: a status code, "" to clear, or "FLIP" to switch Yes <-> No
	(other statuses are left as they are when flipping)."""
	_require_hr()
	ym = _check_ym(ym)
	month = _month(ym)
	if not month:
		frappe.throw(_("Create the schedule first."))
	employees = frappe.parse_json(employees) or []
	dates = frappe.parse_json(dates) or []
	if not employees or not dates:
		frappe.throw(_("Select at least one employee and one Saturday."))
	if code not in CODES and code not in ("", "FLIP"):
		frappe.throw(_("Invalid status."))
	sats = set(_saturdays(ym))
	for d in dates:
		if d not in sats:
			frappe.throw(_("{0} is not a Saturday in this month.").format(d))
		if _past(d):
			frappe.throw(_("{0} has already passed and is part of the log.").format(_head(d)))

	status = month.setdefault("status", {})
	changed = 0
	for emp in employees:
		if emp not in status:
			_remember(month, emp)
		days = status.setdefault(emp, {})
		for d in dates:
			old = days.get(d, "")
			if code == "FLIP":
				new = {"Y": "N", "N": "Y"}.get(old, old)
			else:
				new = code
			if new != old:
				days[d] = new
				changed += 1
	if changed:
		_save_month(ym, month)
	return changed


@frappe.whitelist()
def mark_public_holiday(ym, date, company=None, branch=None):
	_require_hr()
	ym = _check_ym(ym)
	month = _month(ym)
	if not month or date not in _saturdays(ym) or _past(date):
		frappe.throw(_("Choose an upcoming Saturday of a created schedule."))
	emps = _active_employees(_filters(company, branch))
	for e in emps:
		_snapshot(month, e)
		month.setdefault("status", {}).setdefault(e.name, {})[date] = "PH"
	_save_month(ym, month)
	return len(emps)


@frappe.whitelist()
def save_heading(company=None, title=None, subtitle=None, footer=None):
	"""Sheet heading for one company (or for 'All Companies' when company is empty)."""
	_require_hr()
	settings = _settings()
	settings["headings"][company or "_all"] = {
		"title": (title or "").strip(),
		"subtitle": (subtitle or "").strip(),
		"footer": (footer or "").strip(),
	}
	_save("settings", settings)
	return _heading(settings, company)


@frappe.whitelist()
def save_settings(subtitle=None, footer=None, cutoff_hours=24):
	_require_hr()
	settings = _settings()
	settings.update({"subtitle": subtitle or "", "footer": footer or "", "cutoff_hours": cint(cutoff_hours)})
	_save("settings", settings)
	return True


@frappe.whitelist()
def import_month_csv(ym, csv_text, company=None):
	"""CSV: SR #, Employee Name, then one column per Saturday (Yes, No, Vacation, OT, WFH, PH, Yes*).
	Employees are matched by Employee Number (within the company if one is selected).
	Only the imported employees are replaced; others in the month are kept."""
	_require_hr()
	ym = _check_ym(ym)
	sats = _saturdays(ym)
	to_code = {v.lower(): k for k, v in LABELS.items()}
	month = _month(ym) or {"status": {}, "roster": [], "names": {}}
	missing, count = [], 0
	reader = csv.reader(io.StringIO(csv_text.strip().lstrip("\ufeff")))
	next(reader, None)
	for line in reader:
		if len(line) < 2 or not line[0].strip():
			continue
		sr = line[0].strip()
		q = {"employee_number": sr}
		if company:
			q["company"] = company
		emp = frappe.db.get_value("Employee", q, ["name", "employee_name", "employee_number", "company", "branch"], as_dict=True)
		if not emp:
			missing.append(f"{sr} {line[1].strip()}")
			continue
		_snapshot(month, emp)
		month["status"][emp.name] = {}
		for i, cell in enumerate(line[2 : 2 + len(sats)]):
			code = to_code.get(cell.strip().lower())
			if cell.strip() and not code:
				frappe.throw(_("Unknown status '{0}' for SR {1}.").format(cell, sr))
			if code:
				month["status"][emp.name][sats[i]] = code
		count += 1
	if missing:
		frappe.throw(_("Set Employee Number on these employees first:<br>{0}").format("<br>".join(missing)))
	_save_month(ym, month)
	return count


# ------------------------------------------------------------------ swaps
def _get_swap(ym, swap_id):
	swaps = _swaps(_check_ym(ym))
	if swap_id not in swaps:
		frappe.throw(_("Swap request not found."))
	return swaps, swaps[swap_id]


def _apply(swap, reverse=False):
	month = _month(swap["ym"])
	pairs = [(swap["date"], swap["empStatus"], swap["partnerStatus"])]
	if swap.get("ret"):
		pairs.append((swap["ret"], swap["empRet"], swap["partnerRet"]))
	status = month.setdefault("status", {})
	for d, mine, theirs in pairs:
		if _past(d):
			frappe.throw(_("{0} has already passed, so the schedule can't change.").format(_head(d)))
		a = status.get(swap["emp"], {}).get(d)
		b = status.get(swap["partner"], {}).get(d)
		if (a, b) != ((theirs, mine) if reverse else (mine, theirs)):
			frappe.throw(_("The schedule for {0} changed after this request. Reject it and create a new one.").format(_head(d)))
		status[swap["emp"]][d], status[swap["partner"]][d] = b, a
	_save_month(swap["ym"], month)


@frappe.whitelist()
def create_swap(ym, date, employee, partner, reason, return_date=None):
	_require_access()
	ym = _check_ym(ym)
	month = _month(ym)
	if not month:
		frappe.throw(_("This month has no schedule yet."))
	hr = _is_hr()
	if not hr and employee != _my_employee():
		frappe.throw(_("You can only request a swap for your own Saturday."), frappe.PermissionError)
	if employee == partner:
		frappe.throw(_("Choose two different employees."))
	if not (reason or "").strip():
		frappe.throw(_("Add a reason for the swap."))
	return_date = return_date or None
	if return_date == date:
		frappe.throw(_("The return Saturday must be a different Saturday."))
	dates = [d for d in (date, return_date) if d]

	sats = _saturdays(ym)
	status = month.get("status", {})
	got = {}
	for d in dates:
		if d not in sats:
			frappe.throw(_("{0} is not a Saturday in this month.").format(d))
		if _past(d):
			frappe.throw(_("{0} has already passed.").format(_head(d)))
		a, b = status.get(employee, {}).get(d), status.get(partner, {}).get(d)
		if not a or not b:
			frappe.throw(_("Both employees need a status on {0}.").format(_head(d)))
		if a in NO_SWAP or b in NO_SWAP:
			frappe.throw(_("Vacation and public holiday Saturdays can't be swapped ({0}).").format(_head(d)))
		if a == b:
			frappe.throw(_("Both are '{0}' on {1}, so there is nothing to swap.").format(LABELS[a], _head(d)))
		got[d] = (a, b)

	if not hr:
		hours = cint(_settings().get("cutoff_hours"))
		if add_to_date(now_datetime(), hours=hours) > get_datetime(min(dates)):
			frappe.throw(_("Swap requests must be made at least {0} hours before the Saturday. Contact HR.").format(hours))

	swaps = _swaps(ym)
	for s in swaps.values():
		if s["status"] in OPEN and {s["emp"], s["partner"]} & {employee, partner} and {s["date"], s.get("ret")} & set(dates):
			frappe.throw(_("There's already an open swap request for one of these employees on that Saturday."))

	swap = {
		"id": frappe.generate_hash(length=10),
		"ym": ym,
		"date": date,
		"ret": return_date,
		"emp": employee,
		"partner": partner,
		"empName": _name(employee, month),
		"partnerName": _name(partner, month),
		"empStatus": got[date][0],
		"partnerStatus": got[date][1],
		"empRet": got[return_date][0] if return_date else None,
		"partnerRet": got[return_date][1] if return_date else None,
		"reason": reason.strip()[:300],
		"status": "Awaiting Partner",
		"createdAt": str(now_datetime()),
		"createdBy": frappe.session.user,
		"history": [{"at": str(now_datetime()), "by": frappe.session.user, "action": "Requested"}],
	}
	swaps[swap["id"]] = swap
	_save(f"swaps:{ym}", swaps)
	_notify([_user_of(partner)], _("{0} asked to swap Saturday {1} with you").format(swap["empName"], _head(date)))
	return swap["id"]


@frappe.whitelist()
def respond_swap(ym, swap_id, accept):
	_require_access()
	swaps, s = _get_swap(ym, swap_id)
	if s["status"] != "Awaiting Partner":
		frappe.throw(_("This request is no longer waiting for the partner."))
	if _my_employee() != s["partner"] and not _is_hr():
		frappe.throw(_("Only {0} can respond to this request.").format(s["partnerName"]), frappe.PermissionError)
	accepted = sbool(accept)
	s["status"] = "Awaiting Approval" if accepted else "Rejected"
	s["history"].append({"at": str(now_datetime()), "by": frappe.session.user, "action": "Accepted" if accepted else "Declined"})
	_save(f"swaps:{ym}", swaps)
	_notify(
		[s["createdBy"], _user_of(s["emp"])],
		_("{0} {1} your Saturday swap").format(s["partnerName"], _("accepted") if accepted else _("declined")),
	)
	return s["status"]


@frappe.whitelist()
def decide_swap(ym, swap_id, approve, remarks=None):
	_require_hr()
	swaps, s = _get_swap(ym, swap_id)
	if s["status"] != "Awaiting Approval":
		frappe.throw(_("This request isn't waiting for approval."))
	approved = sbool(approve)
	if approved:
		_apply(s)
	s["status"] = "Approved" if approved else "Rejected"
	s["remarks"] = (remarks or "")[:200]
	s["history"].append({"at": str(now_datetime()), "by": frappe.session.user, "action": s["status"]})
	_save(f"swaps:{ym}", swaps)
	_notify(
		[s["createdBy"], _user_of(s["emp"]), _user_of(s["partner"])],
		_("Saturday swap {0} ⇄ {1} was {2}").format(s["empName"], s["partnerName"], s["status"].lower()),
	)
	return s["status"]


@frappe.whitelist()
def cancel_swap(ym, swap_id):
	_require_access()
	swaps, s = _get_swap(ym, swap_id)
	hr = _is_hr()
	if s["status"] in OPEN:
		if not hr and frappe.session.user != s["createdBy"] and _my_employee() != s["emp"]:
			frappe.throw(_("Only the requester or HR can withdraw this request."), frappe.PermissionError)
	elif s["status"] == "Approved":
		if not hr:
			frappe.throw(_("Only HR can cancel an approved swap."), frappe.PermissionError)
		_apply(s, reverse=True)
	else:
		frappe.throw(_("This request is already closed."))
	s["status"] = "Cancelled"
	s["history"].append({"at": str(now_datetime()), "by": frappe.session.user, "action": "Cancelled"})
	_save(f"swaps:{ym}", swaps)
	return s["status"]