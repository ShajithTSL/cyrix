# Put this file at: apps/YOUR_APP/YOUR_APP/customer_hub_api.py
"""Customer Hub API.

Tabs shown for a customer:
  Quotation           -> quotation_to = "Customer" and party_name = customer (Lead quotations excluded);
                         status shown = workflow_state (falls back to status if no workflow)
  Work Order Data     -> custom DocType, linked by its Customer field   (see CUSTOM_DOCTYPES)
  Supply Order Data   -> custom DocType, linked by its Customer field   (see CUSTOM_DOCTYPES)
  Delivery Note       -> customer
  Sales Invoice       -> customer
  Payment Entry       -> party_type = Customer, party = customer

Who sees which customers:
  Users with a role in UNRESTRICTED_ROLES (and Administrator) see every customer.
  Everyone else sees only customers whose Sales Team contains their Sales Person
  (User -> Employee.user_id -> Sales Person.employee, including Sales Persons below
  theirs in the tree), plus customers where they are the Account Manager.
"""

import frappe
from frappe import _
from frappe.utils import add_days, add_months, cint, escape_html, flt, get_first_day, get_url, getdate, nowdate, strip_html

# ======================= Settings (edit to match your site) =======================

UNRESTRICTED_ROLES = {"System Manager", "Sales Manager", "Accounts Manager"}

# Your custom DocTypes. The customer / date / amount / status fields are detected
# automatically from the DocType. If detection picks the wrong field, set it here:
#   "customer_field": "customer", "date_field": "order_date",
#   "amount_field": "total_amount", "status_field": "status",
#   "info_fields": ["item_name", "qty"]
CUSTOM_DOCTYPES = [
	{"doctype": "Job Order Data", "label": "Job Orders", "short": "Job Order", "icon": "tool"},
	{"doctype": "Supply Order Data", "label": "Supply Orders", "short": "Supply Order", "icon": "truck"},
	{"doctype": "Maintenance Contract", "label": "Maintenance Contracts", "short": "Maintenance Contract", "icon": "truck"},
]

# Statuses that count as "finished" when counting open custom documents
DONE_STATUSES = {"Completed", "Closed", "Cancelled", "Delivered", "Supplied", "Done", "Finished", "Rejected"}

# ==================================================================================

LIMIT = 500
DOCSTATUS = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
COMMON = ["name", "docstatus", "creation", "owner"]
DATE_CANDIDATES = ("posting_date", "transaction_date", "order_date", "date", "work_order_date",
                   "supply_date", "document_date", "schedule_date")
AMOUNT_CANDIDATES = ("grand_total", "rounded_total", "total_amount", "net_total", "total", "amount")
SKIP_TYPES = {"Section Break", "Column Break", "Tab Break", "HTML", "Button", "Image", "Fold",
              "Heading", "Table", "Table MultiSelect", "Attach", "Attach Image", "Signature",
              "Text Editor", "Long Text", "Code", "Markdown Editor", "HTML Editor", "Geolocation", "Password"}

_fullnames = {}


def _fullname(user):
	if user not in _fullnames:
		_fullnames[user] = frappe.utils.get_fullname(user) or user
	return _fullnames[user]


# ------------------------------ ageing ------------------------------

BUCKETS = ("not_due", "d1_30", "d31_60", "d61_90", "d90_plus")


def _bucket(days):
	if days <= 0:
		return "not_due"
	if days <= 30:
		return "d1_30"
	if days <= 60:
		return "d31_60"
	if days <= 90:
		return "d61_90"
	return "d90_plus"


def _ageing(invoices, today=None):
	"""invoices: rows with outstanding_amount and due_date (or posting_date).
	Age = days past the due date, like ERPNext's Accounts Receivable report (ageing by due date)."""
	today = today or getdate(nowdate())
	out = {b: 0.0 for b in BUCKETS}
	out.update(total=0.0, max_days=None, invoices=0)
	for r in invoices:
		amt = flt(r.outstanding_amount)
		if not amt:
			continue
		days = (today - getdate(r.due_date or r.posting_date)).days
		out[_bucket(days)] += amt
		out["total"] += amt
		out["invoices"] += 1
		if amt > 0 and days > 0:
			out["max_days"] = max(out["max_days"] or 0, days)
	return out


def _unpaid_invoices(customers=None):
	filters = {"docstatus": 1, "outstanding_amount": ["!=", 0]}
	if customers is not None:
		filters["customer"] = ["in", list(customers) or [""]]
	return frappe.get_all(
		"Sales Invoice", filters=filters,
		fields=["customer", "outstanding_amount", "due_date", "posting_date"], limit_page_length=0,
	)


# ------------------------------ access control ------------------------------

def _restriction(user=None):
	"""None = user may see all customers. Otherwise {'user', 'sales_persons'}."""
	user = user or frappe.session.user
	if user == "Administrator" or UNRESTRICTED_ROLES & set(frappe.get_roles(user)):
		return None
	sales_persons = set()
	employees = frappe.get_all("Employee", filters={"user_id": user}, pluck="name")
	if employees:
		for sp in frappe.get_all("Sales Person", filters={"employee": ["in", employees]}, fields=["name", "lft", "rgt"]):
			sales_persons.update(
				frappe.get_all("Sales Person", filters={"lft": [">=", sp.lft], "rgt": ["<=", sp.rgt]}, pluck="name")
			)
	return {"user": user, "sales_persons": sorted(sales_persons)}


def _allowed_customers(r):
	names = set()
	if r["sales_persons"]:
		names.update(frappe.get_all(
			"Sales Team",
			filters={"parenttype": "Customer", "sales_person": ["in", r["sales_persons"]]},
			pluck="parent",
		))
	if frappe.get_meta("Customer").has_field("account_manager"):
		names.update(frappe.get_all("Customer", filters={"account_manager": r["user"]}, pluck="name"))
	return names


def _check_access(customer):
	frappe.has_permission("Customer", "read", customer, throw=True)
	r = _restriction()
	if r is not None and customer not in _allowed_customers(r):
		frappe.throw(_("Customer {0} is not assigned to your Sales Person.").format(customer), frappe.PermissionError)


_UNSET = object()

# Branch: the field named BRANCH_FIELD is looked for first on Customer, then on Sales Invoice
# (where it is usually an Accounting Dimension). If neither has it, the Branch filter is hidden.
BRANCH_FIELD = "branch"


def _branch_mode():
	if frappe.get_meta("Customer").has_field(BRANCH_FIELD):
		return "customer"
	if frappe.get_meta("Sales Invoice").has_field(BRANCH_FIELD):
		return "invoice"
	return None


def _customer_rows(txt, start, page_len, names=_UNSET):
	"""Customer rows, limited to `names` (a set) or, by default, to what the user may see."""
	if names is _UNSET:
		r = _restriction()
		names = None if r is None else _allowed_customers(r)
	filters = [["disabled", "=", 0]]
	if names is not None:
		if not names:
			return []
		filters.append(["name", "in", list(names)])
	or_filters = [["name", "like", f"%{txt}%"], ["customer_name", "like", f"%{txt}%"]] if txt else None
	return frappe.get_list(
		"Customer",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "customer_name", "customer_group", "territory"],
		order_by="customer_name asc",
		limit_start=start,
		limit_page_length=page_len,
	)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def customer_query(doctype, txt, searchfield, start, page_len, filters):
	"""Search for the customer picker: only customers the user may see."""
	rows = _customer_rows(txt, cint(start), cint(page_len) or 20)
	return [[r.name, r.customer_name] for r in rows]


def _sales_person_tree(sp):
	lft, rgt = frappe.db.get_value("Sales Person", sp, ["lft", "rgt"]) or (None, None)
	if lft is None:
		return [sp]
	return frappe.get_all("Sales Person", filters={"lft": [">=", lft], "rgt": ["<=", rgt]}, pluck="name")


def _age_match(a, age):
	if age == "outstanding":
		return a["total"] > 0
	if age == "overdue":
		return a["max_days"] is not None
	if age == "not_due":
		return a["total"] > 0 and a["max_days"] is None
	return a["max_days"] is not None and _bucket(a["max_days"]) == age


def _filter_options(r, mode):
	if r is None:
		sales_persons = frappe.get_all("Sales Person", filters={"enabled": 1}, pluck="name", order_by="name asc")
	else:
		sales_persons = r["sales_persons"]
	branches = []
	if mode:
		if frappe.db.exists("DocType", "Branch"):
			branches = frappe.get_all("Branch", pluck="name", order_by="name asc")
		elif mode == "customer":
			branches = sorted(x for x in frappe.get_all("Customer", distinct=True, pluck=BRANCH_FIELD) if x)
	return {"sales_persons": sales_persons, "branches": branches, "branch_mode": mode}


@frappe.whitelist()
def get_customers(txt=None, start=0, page_len=50, top=0, rank_by="sales", from_date=None, to_date=None,
                  sales_person=None, branch=None, age=None):
	"""Customer list for the landing view.

	Always limited to the user's Sales Person (unless unrestricted role). Optional filters:
	sales_person (includes Sales Persons under it), branch, age (outstanding / overdue / not_due /
	d1_30 / d31_60 / d61_90 / d90_plus, matched on the customer's oldest overdue invoice).
	top > 0 returns the top N ranked by `rank_by` ("sales" in the period, or "outstanding").
	"""
	start, page_len, top = cint(start), min(cint(page_len) or 50, 200), min(cint(top), 500)
	r = _restriction()
	mode = _branch_mode() if branch else None

	# ---- narrow down the set of customers ----
	scope = None if r is None else set(_allowed_customers(r))

	def narrow(names):
		nonlocal scope
		names = set(names)
		scope = names if scope is None else scope & names

	if sales_person:
		narrow(frappe.get_all(
			"Sales Team",
			filters={"parenttype": "Customer", "sales_person": ["in", _sales_person_tree(sales_person)]},
			pluck="parent",
		))
	if branch and mode == "customer":
		narrow(frappe.get_all("Customer", filters={BRANCH_FIELD: branch}, pluck="name"))
	elif branch and mode == "invoice":
		narrow(frappe.get_all("Sales Invoice", filters={BRANCH_FIELD: branch, "docstatus": 1},
		                      distinct=True, pluck="customer"))

	# ---- ageing (respects branch when branch lives on the invoice) ----
	can_si = _can_read("Sales Invoice")
	by_cust = {}
	if can_si:
		inv_filters = {"docstatus": 1, "outstanding_amount": ["!=", 0]}
		if scope is not None:
			inv_filters["customer"] = ["in", list(scope) or [""]]
		if branch and mode == "invoice":
			inv_filters[BRANCH_FIELD] = branch
		for inv in frappe.get_all("Sales Invoice", filters=inv_filters,
		                          fields=["customer", "outstanding_amount", "due_date", "posting_date"],
		                          limit_page_length=0):
			by_cust.setdefault(inv.customer, []).append(inv)
	ages = {c: _ageing(v) for c, v in by_cust.items()}

	if age:
		narrow(c for c, a in ages.items() if _age_match(a, age))

	summary = None
	if can_si:
		in_scope = by_cust if scope is None else {c: v for c, v in by_cust.items() if c in scope}
		summary = _ageing([i for v in in_scope.values() for i in v])
		summary["customers"] = len([c for c in in_scope if ages[c]["total"] > 0])

	# ---- rows ----
	params = {"txt": f"%{txt}%" if txt else None, "scope": tuple(scope or [""]),
	          "from": from_date, "to": to_date, "branch": branch}
	period = ""
	if from_date:
		period += " and si.posting_date >= %(from)s"
	if to_date:
		period += " and si.posting_date <= %(to)s"
	if branch and mode == "invoice":
		period += f" and si.`{BRANCH_FIELD}` = %(branch)s"

	if scope is not None and not scope:
		rows, has_more = [], False
	elif top:
		conds = " and c.disabled = 0"
		if scope is not None:
			conds += " and c.name in %(scope)s"
		if txt:
			conds += " and (c.name like %(txt)s or c.customer_name like %(txt)s)"
		if rank_by == "outstanding":
			ranked = sorted((c for c in ages if ages[c]["total"] > 0 and (scope is None or c in scope)),
			                key=lambda c: ages[c]["total"], reverse=True)
			if txt:
				ok = set(x.name for x in _customer_rows(txt, 0, 0, set(ranked)))
				ranked = [c for c in ranked if c in ok]
			ranked = ranked[:top]
		else:
			ranked = [x[0] for x in frappe.db.sql(
				f"""select si.customer from `tabSales Invoice` si join `tabCustomer` c on c.name = si.customer
				where si.docstatus = 1 {conds} {period} group by si.customer
				having sum(si.base_grand_total) > 0 order by sum(si.base_grand_total) desc limit {top}""", params)]
		rows = frappe.get_list(
			"Customer", filters=[["name", "in", ranked]],
			fields=["name", "customer_name", "customer_group", "territory"], limit_page_length=0,
		) if ranked else []
		order = {n: i for i, n in enumerate(ranked)}
		rows.sort(key=lambda x: order.get(x.name, 1e9))
		has_more = False
	else:
		rows = _customer_rows(txt, start, page_len + 1, scope)
		has_more = len(rows) > page_len
		rows = rows[:page_len]

	names = [x.name for x in rows]
	sales, last_inv, team = {}, {}, {}
	if names:
		params["n"] = tuple(names)
		for c, amt in frappe.db.sql(
			f"""select si.customer, sum(si.base_grand_total) from `tabSales Invoice` si
			where si.docstatus = 1 and si.customer in %(n)s {period} group by si.customer""", params):
			sales[c] = flt(amt)
		for c, d in frappe.db.sql(
			"""select customer, max(posting_date) from `tabSales Invoice`
			where docstatus = 1 and customer in %(n)s group by customer""", params):
			last_inv[c] = str(d) if d else None
		for c, sp in frappe.db.sql(
			"""select parent, sales_person from `tabSales Team`
			where parenttype = 'Customer' and parent in %(n)s order by idx""", params):
			team.setdefault(c, []).append(sp)

	empty = _ageing([])
	return {
		"ageing": summary,
		"filters": _filter_options(r, mode or _branch_mode()) if start == 0 else None,
		"rows": [
			{**x, "sales": sales.get(x.name, 0), "outstanding": ages.get(x.name, empty)["total"],
			 "age_days": ages.get(x.name, empty)["max_days"], "last_invoice": last_inv.get(x.name),
			 "sales_persons": team.get(x.name, [])}
			for x in rows
		],
		"has_more": has_more,
		"restricted": r is not None,
		"sales_persons": r["sales_persons"] if r else [],
		"currency": frappe.defaults.get_global_default("default_currency"),
	}


# ------------------------------ helpers ------------------------------

def _dates(field, from_date, to_date, is_datetime=False):
	f = []
	if from_date:
		f.append([field, ">=", from_date])
	if to_date:
		f.append([field, "<=", f"{to_date} 23:59:59" if is_datetime else to_date])
	return f


def _can_read(doctype):
	return frappe.db.exists("DocType", doctype) and frappe.has_permission(doctype, "read")


def _list(doctype, filters, fields, order_by, limit=LIMIT):
	if not _can_read(doctype):
		return []
	return frappe.get_list(doctype, filters=filters, fields=fields, order_by=order_by, limit_page_length=limit)


def _norm(rows, doctype, info=None, progress=None, status=None):
	return [
		{
			"doctype": doctype,
			"name": r.name,
			"date": str(r.get("date") or "")[:10],
			"status": (status(r) if status else None) or r.get("status") or DOCSTATUS.get(r.docstatus, ""),
			"amount": r.get("amount"),
			"currency": r.get("currency"),
			"info": info(r) if info else "",
			"progress": round(flt(progress(r)), 1) if progress else None,
			"creation": str(r.creation),
			"owner": _fullname(r.owner),
		}
		for r in rows
	]


def _detect(doctype, cfg):
	"""Work out which fields of a custom DocType hold customer, date, amount, status."""
	meta = frappe.get_meta(doctype)
	has = meta.has_field
	fields = [d for d in meta.fields if d.fieldtype not in SKIP_TYPES]

	cust = cfg.get("customer_field")
	if not cust:
		cust = next((d.fieldname for d in fields if d.fieldtype == "Link" and d.options == "Customer"), None)
	if not cust:
		cust = next((n for n in ("customer", "customer_name", "party", "party_name") if has(n)), None)
	cust_df = meta.get_field(cust) if cust else None

	date = cfg.get("date_field") or next((n for n in DATE_CANDIDATES if has(n)), None) \
		or next((d.fieldname for d in fields if d.fieldtype in ("Date", "Datetime")), None) or "creation"
	date_is_dt = date == "creation" or (meta.get_field(date) and meta.get_field(date).fieldtype == "Datetime")

	amount = cfg.get("amount_field") or next((n for n in AMOUNT_CANDIDATES if has(n)), None) \
		or next((d.fieldname for d in fields if d.fieldtype == "Currency"), None)
	status = cfg.get("status_field") or ("status" if has("status") else ("workflow_state" if has("workflow_state") else None))

	used = {cust, date, amount, status, "currency", "naming_series", "amended_from", "company"}
	info = cfg.get("info_fields") or [d.fieldname for d in fields if d.in_list_view and d.fieldname not in used][:3]
	if not info and meta.title_field and meta.title_field not in used:
		info = [meta.title_field]

	return {
		"meta": meta, "customer": cust,
		"customer_is_link": bool(cust_df and cust_df.fieldtype == "Link"),
		"date": date, "date_is_dt": date_is_dt, "amount": amount, "status": status,
		"currency": has("currency"), "info": info,
	}


def _fmt(meta, field, value):
	if value in (None, ""):
		return ""
	df = meta.get_field(field)
	if df and df.fieldtype in ("Date", "Datetime", "Currency", "Float", "Int", "Percent"):
		return strip_html(str(frappe.format(value, df)))
	return str(value)


def _custom_docs(cfg, customer, customer_name, from_date, to_date):
	"""Returns (rows, setup_note)."""
	dt = cfg["doctype"]
	if not frappe.db.exists("DocType", dt):
		return None, _("DocType '{0}' was not found. Set the correct name in customer_hub/api.py.").format(dt)
	if not frappe.has_permission(dt, "read"):
		return [], None
	m = _detect(dt, cfg)
	if not m["customer"]:
		return None, _("'{0}' has no Customer field. Set customer_field in customer_hub/api.py.").format(dt)

	cust_filter = [m["customer"], "=", customer] if m["customer_is_link"] else [m["customer"], "in", [customer, customer_name]]
	fields = COMMON + [f"{m['date']} as date"] + m["info"]
	if m["status"]:
		fields.append(f"{m['status']} as status")
	if m["amount"]:
		fields.append(f"{m['amount']} as amount")
	if m["currency"]:
		fields.append("currency")

	rows = frappe.get_list(
		dt,
		filters=[cust_filter, ["docstatus", "<", 2]] + _dates(m["date"], from_date, to_date, m["date_is_dt"]),
		fields=list(dict.fromkeys(fields)),
		order_by=f"{m['date']} desc",
		limit_page_length=LIMIT,
	)
	meta = m["meta"]
	return _norm(rows, dt, info=lambda r: " · ".join(
		v for v in (_fmt(meta, f, r.get(f)) for f in m["info"]) if v)), None


# ------------------------------ main endpoint ------------------------------

@frappe.whitelist()
def get_customer_hub(customer, from_date=None, to_date=None):
	_check_access(customer)
	cust = frappe.get_doc("Customer", customer)
	company_currency = frappe.defaults.get_global_default("default_currency")

	docs, tabs, notes = {}, [], []

	def add(dt, label, short, icon, rows, creatable=False):
		docs[dt] = rows
		tabs.append({"dt": dt, "label": _(label), "short": _(short), "icon": icon, "creatable": creatable})

	qtn_wf = frappe.get_meta("Quotation").has_field("workflow_state")
	qtn = _list(
		"Quotation",
		[["quotation_to", "=", "Customer"], ["party_name", "=", customer], ["docstatus", "<", 2]]
		+ _dates("transaction_date", from_date, to_date),
		COMMON + ["transaction_date as date", "valid_till", "status", "grand_total as amount",
		          "base_grand_total", "currency", "order_type"] + (["workflow_state"] if qtn_wf else []),
		"transaction_date desc",
	)
	add("Quotation", "Quotations", "Quotation", "file", _norm(qtn, "Quotation",
		info=lambda r: " · ".join(x for x in [r.order_type,
			_("Valid till {0}").format(frappe.format(r.valid_till, "Date")) if r.valid_till else ""] if x),
		status=lambda r: r.get("workflow_state")), True)

	# requests (CRM deals) for this existing customer
	if frappe.db.exists("DocType", "CRM Deal") and frappe.has_permission("CRM Deal", "read"):
		dmeta = frappe.get_meta("CRM Deal")
		or_f = [["organization", "=", cust.customer_name]]
		if dmeta.has_field("custom_customer"):
			or_f.append(["custom_customer", "=", customer])
		vf = next((f for f in ("deal_value", "annual_revenue") if dmeta.has_field(f)), None)
		dfields = ["name", "status", "creation", "owner", "modified", "docstatus"] + \
			[f for f in ("custom_request_type", "custom_unit_model", "currency") if dmeta.has_field(f)] + ([f"{vf} as amount"] if vf else [])
		drows = frappe.get_list("CRM Deal", or_filters=or_f, fields=dfields, order_by="creation desc", limit_page_length=200)
		for d in drows:
			d.date = d.creation
		add("CRM Deal", "Requests (Deals)", "Deal", "target", _norm(drows, "CRM Deal",
			info=lambda r: " · ".join(x for x in [r.get("custom_request_type"), r.get("custom_unit_model")] if x)), True)

	for cfg in CUSTOM_DOCTYPES:
		rows, note = _custom_docs(cfg, customer, cust.customer_name, from_date, to_date)
		if note:
			notes.append(note)
		if rows is not None:
			add(cfg["doctype"], cfg.get("label", cfg["doctype"]), cfg.get("short", cfg["doctype"]),
			    cfg.get("icon", "file"), rows, cfg.get("creatable", False))

	dn = _list(
		"Delivery Note",
		[["customer", "=", customer], ["docstatus", "<", 2]] + _dates("posting_date", from_date, to_date),
		COMMON + ["posting_date as date", "status", "grand_total as amount", "currency", "per_billed", "lr_no"],
		"posting_date desc",
	)
	add("Delivery Note", "Delivery Notes", "DN", "send", _norm(dn, "Delivery Note",
		info=lambda r: _("LR {0}").format(r.lr_no) if r.lr_no else "", progress=lambda r: r.per_billed), True)

	si = _list(
		"Sales Invoice",
		[["customer", "=", customer], ["docstatus", "<", 2]] + _dates("posting_date", from_date, to_date),
		COMMON + ["posting_date as date", "due_date", "status", "grand_total as amount",
		          "base_grand_total", "currency", "outstanding_amount", "is_return"],
		"posting_date desc",
	)
	add("Sales Invoice", "Sales Invoices", "Sales Invoice", "invoice", _norm(si, "Sales Invoice",
		info=lambda r: " · ".join(x for x in [
			_("Return") if r.is_return else "",
			_("Due {0}").format(frappe.format(r.due_date, "Date")) if r.due_date else "",
			_("{0} days overdue").format((getdate(nowdate()) - getdate(r.due_date)).days)
			if r.docstatus == 1 and flt(r.outstanding_amount) > 0 and r.due_date and getdate(r.due_date) < getdate(nowdate()) else "",
		] if x)), True)

	pe = _list(
		"Payment Entry",
		[["party_type", "=", "Customer"], ["party", "=", customer], ["docstatus", "<", 2]]
		+ _dates("posting_date", from_date, to_date),
		COMMON + ["posting_date as date", "payment_type", "mode_of_payment", "reference_no",
		          "paid_amount as amount", "paid_from_account_currency as currency"],
		"posting_date desc",
	)
	add("Payment Entry", "Payments", "Payment", "wallet", _norm(pe, "Payment Entry",
		info=lambda r: " · ".join(x for x in [r.payment_type, r.mode_of_payment, r.reference_no] if x)))

	return {
		"customer": _customer_info(cust),
		"currency": company_currency or cust.default_currency,
		"tabs": tabs,
		"setup_notes": notes,
		"kpis": _kpis(customer, qtn, si, pe, docs),
		"monthly": {
			"invoiced": _monthly("Sales Invoice", {"customer": customer}, "posting_date"),
			"received": _monthly("Payment Entry", {"party_type": "Customer", "party": customer,
			                                       "payment_type": "Receive"}, "posting_date", "base_paid_amount"),
			"quoted": _monthly("Quotation", {"quotation_to": "Customer", "party_name": customer}, "transaction_date"),
		},
		"docs": docs,
		"activity": _activity(customer, docs),
		"followups": _followups(reference=("Customer", customer)),
	}


def _customer_info(cust):
	address = ""
	if cust.get("customer_primary_address"):
		address = strip_html((cust.get("primary_address") or "").replace("<br>", ", ")).strip(", ")
	credit = cust.get("credit_limits") or []
	return {
		"name": cust.name,
		"customer_name": cust.customer_name,
		"customer_type": cust.customer_type,
		"customer_group": cust.customer_group,
		"territory": cust.territory,
		"tax_id": cust.get("tax_id"),
		"email_id": cust.get("email_id"),
		"mobile_no": cust.get("mobile_no"),
		"contact": cust.get("customer_primary_contact"),
		"address": address,
		"account_manager": _fullname(cust.account_manager) if cust.get("account_manager") else "",
		"sales_persons": [r.sales_person for r in (cust.get("sales_team") or [])],
		"credit_limit": flt(credit[0].credit_limit) if credit else 0,
		"since": str(cust.creation)[:10],
		"disabled": cust.disabled,
	}


def _kpis(customer, qtn, si, pe, docs):
	sub = lambda rows: [r for r in rows if r.docstatus == 1]
	open_q = [r for r in sub(qtn) if r.status in ("Open", "Replied", "Partially Ordered")]
	ordered_q = [r for r in sub(qtn) if r.status in ("Ordered", "Partially Ordered")]

	ageing = _ageing(frappe.get_list(
		"Sales Invoice",
		filters={"customer": customer, "docstatus": 1, "outstanding_amount": ["!=", 0]},
		fields=["outstanding_amount", "due_date", "posting_date"],
		limit_page_length=0,
	)) if _can_read("Sales Invoice") else _ageing([])
	outstanding = ageing["total"]
	overdue = sum(ageing[b] for b in BUCKETS if b != "not_due")

	custom = {}
	for cfg in CUSTOM_DOCTYPES:
		rows = docs.get(cfg["doctype"])
		if rows is None:
			continue
		custom[cfg["doctype"]] = {
			"count": len(rows),
			"open": len([r for r in rows if r["status"] not in DONE_STATUSES and r["status"] != "Cancelled"]),
			"amount": sum(flt(r["amount"]) for r in rows if r["status"] != "Draft"),
		}

	last_invoice = max((r.date for r in sub(si)), default=None)
	return {
		"total_sales": sum(flt(r.base_grand_total) for r in sub(si)),
		"invoice_count": len(sub(si)),
		"outstanding": outstanding,
		"overdue": overdue,
		"ageing": ageing,
		"open_quotations": len(open_q),
		"open_quotation_value": sum(flt(r.base_grand_total) for r in open_q),
		"received": sum(flt(r.amount) for r in sub(pe) if r.payment_type == "Receive"),
		"payment_count": len([r for r in sub(pe) if r.payment_type == "Receive"]),
		"custom": custom,
		"conversion_rate": round(len(ordered_q) / len(sub(qtn)) * 100, 1) if sub(qtn) else None,
		"last_invoice_date": str(last_invoice) if last_invoice else None,
	}


def _monthly(doctype, filters, date_field, value_field="base_grand_total"):
	start = get_first_day(add_months(nowdate(), -11))
	buckets = {add_months(start, i).strftime("%Y-%m"): {"value": 0, "count": 0} for i in range(12)}
	if _can_read(doctype):
		for r in frappe.get_list(
			doctype,
			filters={**filters, "docstatus": 1, date_field: [">=", start]},
			fields=[f"{date_field} as d", f"{value_field} as v"],
			limit_page_length=0,
		):
			b = buckets.get(getdate(r.d).strftime("%Y-%m"))
			if b:
				b["value"] += flt(r.v)
				b["count"] += 1
	return [{"month": k, **v} for k, v in buckets.items()]


def _activity(customer, docs):
	events, names = [], [customer]
	for rows in docs.values():
		for d in rows:
			names.append(d["name"])
			events.append({"kind": "doc", "ts": d["creation"], **d})

	for c in frappe.get_all(
		"Comment",
		filters={"comment_type": "Comment", "reference_name": ["in", names]},
		fields=["reference_doctype", "reference_name", "content", "owner", "creation"],
		order_by="creation desc",
		limit_page_length=300,
	):
		events.append({
			"kind": "comment", "ts": str(c.creation), "doctype": c.reference_doctype,
			"name": c.reference_name, "owner": _fullname(c.owner),
			"content": strip_html(c.content or "")[:2000],
		})

	if _can_read("Communication"):
		for m in frappe.get_list(
			"Communication",
			filters={"communication_type": "Communication", "reference_name": ["in", names]},
			fields=["reference_doctype", "reference_name", "subject", "sender", "recipients",
			        "content", "sent_or_received", "creation"],
			order_by="creation desc",
			limit_page_length=200,
		):
			events.append({
				"kind": "email", "ts": str(m.creation), "doctype": m.reference_doctype,
				"name": m.reference_name, "owner": m.sender, "subject": m.subject,
				"recipients": m.recipients, "direction": m.sent_or_received,
				"content": strip_html(m.content or "")[:400],
			})

	events.sort(key=lambda e: e["ts"], reverse=True)
	return events[:400]


CALL_PREFIX = "Call: "  # comments starting with this are shown as logged calls


@frappe.whitelist()
def add_comment(customer, content, kind="note", mentions=None):
	"""kind = "note" (plain comment) or "call" (comment shown as a logged call)."""
	_check_access(customer)
	content = (content or "").strip()
	if not content:
		frappe.throw(_("Comment is empty"))
	if kind == "call":
		content = CALL_PREFIX + content
	html = _mention_html(content, mentions)
	return frappe.get_doc("Customer", customer).add_comment("Comment", text=html).name


def _mention_html(text, mentions=None):
	"""Plain text -> HTML; "@Full Name" of each picked user becomes a Frappe mention (notifies them)."""
	html = escape_html(text or "").replace("\n", "<br>")
	for uid in dict.fromkeys(frappe.parse_json(mentions) or []):
		if not uid or not frappe.db.exists("User", uid):
			continue
		full = frappe.utils.get_fullname(uid) or uid
		span = (f'<span class="mention" data-id="{escape_html(uid)}" data-value="{escape_html(full)}" '
		        f'data-denotation-char="@">@{escape_html(full)}</span>')
		html = html.replace("@" + escape_html(full), span)
	return f"<p>{html}</p>"


@frappe.whitelist()
def mention_users():
	"""People who can be @mentioned (enabled desk users)."""
	return [{"name": u.name, "full_name": u.full_name or u.name} for u in frappe.get_all(
		"User", filters={"enabled": 1, "user_type": "System User", "name": ["!=", "Guest"]},
		fields=["name", "full_name"], order_by="full_name asc")]


# =============================== Sales home (CRM) ===============================
# Follow-ups are standard ERPNext ToDo records (they also appear in the To Do list).
# If the Frappe CRM app is installed, its Tasks, Leads and Deals are shown as well.

CRM_ROUTE = "/crm"  # where the Frappe CRM UI lives
QUIET_DAYS = 90     # "gone quiet": no invoice for this many days ...
QUIET_LOOKBACK = 540  # ... but invoiced within this many days


STD_FIELDS = {"name", "modified", "creation", "owner"}


def _crm(doctype):
	return frappe.db.exists("DocType", doctype)


def _assigned_or_owned(owner_field, user):
	return [[owner_field, "=", user], ["_assign", "like", f'%"{user}"%']]


def _ref_labels(pairs):
	"""{(doctype, name): label} for ToDo references (customer names, lead names, ...)."""
	out, by_dt = {}, {}
	for dt, name in pairs:
		if dt and name:
			by_dt.setdefault(dt, set()).add(name)
	title_fields = {"Customer": "customer_name", "CRM Lead": "lead_name", "CRM Deal": "organization",
	                "Quotation": "customer_name"}
	for dt, names in by_dt.items():
		f = title_fields.get(dt)
		if f and frappe.db.exists("DocType", dt) and frappe.get_meta(dt).has_field(f):
			for r in frappe.get_all(dt, filters={"name": ["in", list(names)]}, fields=["name", f"{f} as label"]):
				out[(dt, r.name)] = r.label or r.name
	return out


def _followups(user=None, reference=None, team=False, scope=None):
	"""Open follow-ups: ToDo (+ CRM Task when not filtered by reference)."""
	user = user or frappe.session.user
	filters = {"status": "Open"}
	if reference:
		filters.update(reference_type=reference[0], reference_name=reference[1])
	elif not team:
		filters["allocated_to"] = user
	else:
		filters["reference_type"] = ["in", ["Customer", "Quotation", "CRM Lead", "CRM Deal"]]
	rows = frappe.get_all("ToDo", filters=filters,
	                      fields=["name", "description", "date", "reference_type", "reference_name",
	                              "allocated_to", "priority"],
	                      order_by="date asc, creation asc", limit_page_length=150)
	if team and scope is not None:
		rows = [r for r in rows if r.reference_type != "Customer" or r.reference_name in scope]
	out = [{
		"kind": "todo", "name": r.name, "title": strip_html(r.description or "")[:200],
		"date": str(r.date) if r.date else None, "ref_doctype": r.reference_type,
		"ref_name": r.reference_name, "owner": _fullname(r.allocated_to) if r.allocated_to else "",
		"priority": r.priority,
	} for r in rows]

	if not reference and _crm("CRM Task") and not frappe.get_meta("CRM Task").istable:
		tf = {"status": ["not in", ["Done", "Canceled"]]}
		if not team:
			tf["assigned_to"] = user
		tmeta = frappe.get_meta("CRM Task")
		if not tmeta.has_field("assigned_to"):
			tf.pop("assigned_to", None)
		tfields = [f for f in ["name", "title", "description", "due_date", "status", "priority", "assigned_to",
		                       "reference_doctype", "reference_docname"] if f == "name" or tmeta.has_field(f)]
		for r in frappe.get_all("CRM Task", filters=tf, fields=tfields,
		                        order_by="due_date asc" if tmeta.has_field("due_date") else "modified desc",
		                        limit_page_length=100):
			out.append({
				"kind": "crm_task", "name": r.name,
				"title": r.get("title") or strip_html(r.get("description") or "")[:140] or r.name,
				"date": str(r.due_date)[:10] if r.get("due_date") else None,
				"ref_doctype": r.get("reference_doctype"), "ref_name": r.get("reference_docname"),
				"owner": _fullname(r.assigned_to) if r.get("assigned_to") else "", "priority": r.get("priority"),
			})

	labels = _ref_labels((f["ref_doctype"], f["ref_name"]) for f in out)
	for f in out:
		f["ref_label"] = labels.get((f["ref_doctype"], f["ref_name"]), f["ref_name"] or "")
	out.sort(key=lambda f: f["date"] or "9999")
	return out


def _deal_pipeline(user, team):
	if not _crm("CRM Deal"):
		return None
	meta = frappe.get_meta("CRM Deal")
	value_field = next((f for f in ("deal_value", "annual_revenue") if meta.has_field(f)), None)
	close_field = next((f for f in ("expected_closure_date", "close_date") if meta.has_field(f)), None)

	statuses, closed = [], set()
	if _crm("CRM Deal Status"):
		sm = frappe.get_meta("CRM Deal Status")
		fields = ["name"] + [f for f in ("color", "position", "type") if sm.has_field(f)]
		order = "position asc" if sm.has_field("position") else "name asc"
		for s in frappe.get_all("CRM Deal Status", fields=fields, order_by=order):
			if (s.get("type") in ("Won", "Lost")) or (not s.get("type") and s.name in ("Won", "Lost")):
				closed.add(s.name)
				continue
			statuses.append({"status": s.name, "color": s.get("color") or "gray"})

	fields = ["name", "organization", "status", "deal_owner", "modified", "currency"]
	fields += [f"{value_field} as value"] if value_field else []
	fields += [f"{close_field} as close_date"] if close_field else []
	filters = [["status", "not in", list(closed) or [""]]]
	deals = frappe.get_list("CRM Deal", filters=filters,
	                        or_filters=None if team else _assigned_or_owned("deal_owner", user),
	                        fields=[f for f in fields if f.split(" ")[0] in STD_FIELDS or meta.has_field(f.split(" ")[0])],
	                        order_by="modified desc", limit_page_length=300)
	cols = {s["status"]: {**s, "deals": [], "count": 0, "value": 0} for s in statuses}
	for d in deals:
		col = cols.setdefault(d.status, {"status": d.status, "color": "gray", "deals": [], "count": 0, "value": 0})
		col["count"] += 1
		col["value"] += flt(d.get("value"))
		if len(col["deals"]) < 6:
			col["deals"].append({
				"name": d.name, "organization": d.organization or d.name, "value": flt(d.get("value")),
				"currency": d.get("currency"), "close_date": str(d.get("close_date") or "")[:10] or None,
				"owner": _fullname(d.deal_owner) if d.deal_owner else "",
			})
	return {"columns": list(cols.values()), "count": len(deals), "value": sum(flt(d.get("value")) for d in deals),
	        "url": CRM_ROUTE}


def _new_leads(user, team):
	if not _crm("CRM Lead"):
		return None
	meta = frappe.get_meta("CRM Lead")
	filters = [["converted", "=", 0]] if meta.has_field("converted") else []
	fields = ["name", "lead_name", "organization", "status", "mobile_no", "email", "modified", "lead_owner"]
	rows = frappe.get_list("CRM Lead", filters=filters,
	                       or_filters=None if team else _assigned_or_owned("lead_owner", user),
	                       fields=[f for f in fields if f in STD_FIELDS or meta.has_field(f)],
	                       order_by="modified desc", limit_page_length=8)
	return [{"name": r.name, "lead_name": r.get("lead_name") or r.name, "organization": r.get("organization"),
	         "status": r.get("status"), "mobile_no": r.get("mobile_no"), "email": r.get("email"),
	         "modified": str(r.modified), "owner": _fullname(r.lead_owner) if r.get("lead_owner") else ""}
	        for r in rows]


@frappe.whitelist()
def get_home(team=0, part="all"):
	"""part = "crm": follow-ups, visits, pipeline, leads (Sales CRM page, fast: no invoice scan)
	part = "customers": outstanding / ageing, overdue payments, expiring quotations, gone quiet (Customer Hub)
	part = "all": both."""
	crm_part = part in ("all", "crm")
	cust_part = part in ("all", "customers")
	user = frappe.session.user
	today = getdate(nowdate())
	r = _restriction()
	team = bool(cint(team)) and r is None
	scope = None if r is None else _allowed_customers(r)
	in_scope = (lambda c: True) if scope is None else (lambda c: c in scope)

	# ---- ageing for customers in scope ----
	by_cust = {}
	if cust_part and _can_read("Sales Invoice"):
		inv_filters = {"docstatus": 1, "outstanding_amount": ["!=", 0]}
		if scope is not None:
			inv_filters["customer"] = ["in", list(scope) or [""]]
		for inv in frappe.get_all("Sales Invoice", filters=inv_filters,
		                          fields=["customer", "outstanding_amount", "due_date", "posting_date"],
		                          limit_page_length=0):
			by_cust.setdefault(inv.customer, []).append(inv)
	ages = {c: _ageing(v) for c, v in by_cust.items()}
	total_age = _ageing([i for v in by_cust.values() for i in v])
	overdue_total = total_age["total"] - total_age["not_due"]

	overdue = sorted(
		({"customer": c, "amount": a["total"] - a["not_due"], "days": a["max_days"]}
		 for c, a in ages.items() if a["max_days"] and a["max_days"] > 30 and a["total"] - a["not_due"] > 0),
		key=lambda x: x["amount"], reverse=True)[:6]

	# ---- quotations expiring within a week (or expired in the last week) ----
	q_filters = [["quotation_to", "=", "Customer"], ["docstatus", "=", 1],
	             ["status", "in", ["Open", "Replied", "Partially Ordered"]]]
	if scope is not None:
		q_filters.append(["party_name", "in", list(scope) or [""]])
	open_quotes = frappe.get_list("Quotation", filters=q_filters,
	                              fields=["name", "party_name", "customer_name", "grand_total", "base_grand_total",
	                                      "currency", "valid_till", "transaction_date"],
	                              order_by="valid_till asc", limit_page_length=0) if cust_part and _can_read("Quotation") else []
	lo, hi = add_days(today, -7), add_days(today, 7)
	expiring = [{"name": q.name, "customer": q.party_name, "customer_name": q.customer_name,
	             "amount": flt(q.grand_total), "currency": q.currency, "valid_till": str(q.valid_till)}
	            for q in open_quotes if q.valid_till and lo <= getdate(q.valid_till) <= hi][:6]

	# ---- gone quiet: good customers with no invoice for QUIET_DAYS ----
	quiet = []
	if cust_part and _can_read("Sales Invoice"):
		params = {"cut": add_days(today, -QUIET_DAYS), "from": add_days(today, -QUIET_LOOKBACK)}
		cond = ""
		if scope is not None:
			if not scope:
				cond = " and 1=0"
			else:
				cond = " and customer in %(scope)s"
				params["scope"] = tuple(scope)
		for c, last, total in frappe.db.sql(f"""
			select customer, max(posting_date), sum(base_grand_total) from `tabSales Invoice`
			where docstatus = 1 and is_return = 0 and posting_date >= %(from)s {cond}
			group by customer having max(posting_date) < %(cut)s
			order by sum(base_grand_total) desc limit 6""", params):
			quiet.append({"customer": c, "last_invoice": str(last), "days": (today - getdate(last)).days,
			              "sales": flt(total)})

	# customer names for everything above
	ids = {x["customer"] for x in overdue + expiring + quiet}
	info = {c.name: c for c in frappe.get_all(
		"Customer", filters={"name": ["in", list(ids) or [""]]}, fields=["name", "customer_name", "mobile_no"])}
	for x in overdue + expiring + quiet:
		c = info.get(x["customer"]) or {}
		x["customer_name"] = x.get("customer_name") or c.get("customer_name") or x["customer"]
		x["mobile_no"] = c.get("mobile_no")

	followups = _followups(user=user, team=team, scope=scope) if crm_part else []
	visits = _upcoming_visits(user, team) if crm_part else None
	pipeline = _deal_pipeline(user, team) if crm_part else None
	leads = _new_leads(user, team) if crm_part else None

	customer_count = len(scope) if scope is not None else frappe.db.count("Customer", {"disabled": 0})
	return {
		"user": {"first_name": (frappe.db.get_value("User", user, "first_name") or user.split("@")[0]),
		         "can_team": r is None, "team": team,
		         "sales_persons": r["sales_persons"] if r else []},
		"currency": frappe.defaults.get_global_default("default_currency"),
		"today": str(today),
		"kpis": {
			"customers": customer_count,
			"outstanding": total_age["total"], "overdue": overdue_total,
			"open_quotes": len(open_quotes),
			"open_quote_value": sum(flt(q.base_grand_total) for q in open_quotes),
			"deals": pipeline["count"] if pipeline else None,
			"deal_value": pipeline["value"] if pipeline else None,
		},
		"followups": followups,
		"visits": visits,
		"attention": {"overdue": overdue, "expiring": expiring, "quiet": quiet},
		"pipeline": pipeline,
		"leads": leads,
		"crm_route": CRM_ROUTE if _crm("CRM Deal") else None,
	}


@frappe.whitelist()
def add_followup(reference_doctype, reference_name, date, description):
	"""Create a follow-up (ToDo) for the current user on a customer, quotation, lead or deal."""
	if reference_doctype == "Customer":
		_check_access(reference_name)
	else:
		frappe.has_permission(reference_doctype, "read", reference_name, throw=True)
	description = (description or "").strip()
	if not description:
		frappe.throw(_("Write what to follow up"))
	todo = frappe.get_doc({
		"doctype": "ToDo",
		"description": escape_html(description),
		"date": date or add_days(nowdate(), 1),
		"allocated_to": frappe.session.user,
		"assigned_by": frappe.session.user,
		"reference_type": reference_doctype,
		"reference_name": reference_name,
		"priority": "Medium",
	}).insert()
	return todo.name


@frappe.whitelist()
def complete_followup(kind, name):
	if kind == "crm_task":
		doc = frappe.get_doc("CRM Task", name)
		doc.status = "Done"
	else:
		doc = frappe.get_doc("ToDo", name)
		doc.status = "Closed"
	doc.save()  # normal permission checks apply
	return doc.name



def _upcoming_visits(user, team, days=7):
	"""Planned visits for the next `days` days: Visit Plan lines + calendar visits (Events with a Visit Type)."""
	plans = _plan_lines_upcoming(user, team, days)
	events = _event_visits_upcoming(user, team, days)
	if plans is None and events is None:
		return None
	out = (plans or []) + (events or [])
	out.sort(key=lambda v: v["starts_on"])
	return out


def _plan_lines_upcoming(user, team, days):
	if not frappe.db.exists("DocType", "Visit Plan"):
		return None
	from frappe.utils import add_days as _add
	today = getdate(nowdate())
	pf = {"plan_date": ["between", [_add(today, -7), _add(today, days)]], "status": ["in", ["Draft", "Planned", "In Progress"]]}
	if not team:
		pf["sales_user"] = user
	plans = {p.name: p for p in frappe.get_all("Visit Plan", filters=pf, fields=["name", "plan_date", "sales_user"],
	                                           limit_page_length=200)}
	if not plans:
		return []
	rows = frappe.get_all("Visit Plan Item", filters={"parent": ["in", list(plans)], "parenttype": "Visit Plan",
	                                                  "status": "Planned"},
	                      fields=["name", "parent", "visit_time", "party_type", "party", "party_name", "visit_type",
	                              "location", "purpose"], limit_page_length=500)
	out = []
	for r in rows:
		p = plans[r.parent]
		t = r.visit_time
		hhmm = f"{int(t.total_seconds()) // 3600:02d}:{(int(t.total_seconds()) % 3600) // 60:02d}" if hasattr(t, "total_seconds") else (str(t)[:5] if t else "09:00")
		out.append({"name": r.name, "plan": r.parent, "subject": r.purpose or r.visit_type, "starts_on": f"{p.plan_date} {hhmm}:00",
		            "type": r.visit_type, "location": r.location, "by": _fullname(p.sales_user),
		            "ref_doctype": r.party_type, "ref_name": r.party, "ref_label": r.party_name or r.party,
		            "late": getdate(p.plan_date) < today})
	return out


def _event_visits_upcoming(user, team, days):
	if not (frappe.db.exists("DocType", "Event") and frappe.get_meta("Event").has_field("custom_visit_type")):
		return None
	from frappe.utils import add_to_date, get_datetime, now_datetime
	start = get_datetime(nowdate())
	end = add_to_date(start, days=days + 1)
	filters = [["custom_visit_type", "is", "set"], ["status", "=", "Open"],
	           ["starts_on", ">=", add_to_date(start, days=-7)], ["starts_on", "<", end]]
	or_filters = None if team else [["custom_visit_assigned_to", "=", user], ["owner", "=", user]]
	rows = frappe.get_all("Event", filters=filters, or_filters=or_filters,
	                      fields=["name", "subject", "starts_on", "ends_on", "custom_visit_type", "custom_visit_location",
	                              "custom_visit_assigned_to", "owner"],
	                      order_by="starts_on asc", limit_page_length=50)
	if not rows:
		return []
	links = {}
	for p in frappe.get_all("Event Participants", filters={"parent": ["in", [r.name for r in rows]], "parenttype": "Event"},
	                        fields=["parent", "reference_doctype", "reference_docname"]):
		links.setdefault(p.parent, (p.reference_doctype, p.reference_docname))
	labels = _ref_labels(links.values())
	now = now_datetime()
	out = []
	for r in rows:
		ref = links.get(r.name, (None, None))
		late = get_datetime(r.starts_on) < now and get_datetime(r.starts_on).date() < now.date()
		out.append({"name": r.name, "subject": r.subject, "starts_on": str(r.starts_on), "type": r.custom_visit_type,
		            "location": r.custom_visit_location, "by": _fullname(r.custom_visit_assigned_to or r.owner),
		            "ref_doctype": ref[0], "ref_name": ref[1], "ref_label": labels.get(ref, ref[1] or ""),
		            "late": late})
	return out