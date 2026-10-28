import frappe
from frappe import _
from frappe.query_builder.functions import Count, Sum
from frappe.utils import add_days, add_months, cint, fmt_money, formatdate, getdate, nowdate
from frappe.utils.nestedset import get_descendants_of
from frappe.utils.pdf import get_pdf

# ---------------------------------------------------------------------------
# Your Job Order / Supply Order doctypes.
# customer_field and date_field are optional: if they are wrong or empty,
# the code detects them from the doctype (first Link field to Customer, and
# the first of transaction_date / posting_date / order_date / date, else creation).
# Child tables inside Customer are supported too (counted per parent customer).
# ---------------------------------------------------------------------------
JOB_ORDER = {"doctype": "Job Order Data", "customer_field": "customer", "date_field": "received_date"}
SUPPLY_ORDER = {"doctype": "Supply Order Data", "customer_field": "customer", "date_field": "posting_date"}

#
# Sales Person field on Sales Invoice, Job Order and Supply Order.
# If the name differs, the first Link field to "Sales Person" is used instead.
SALES_PERSON_FIELD = "sales_person"
 
DATE_CANDIDATES = ("transaction_date", "posting_date", "order_date", "date", "received_date")
 
 
def get_quarter_range(year, quarter):
	start = getdate(f"{year}-{(quarter - 1) * 3 + 1:02d}-01")
	end = getdate(add_days(add_months(start, 3), -1))
	return start, end
 
 
def parse_args(year, quarter, limit):
	today = getdate(nowdate())
	year = cint(year) or today.year
	quarter = cint(quarter) or (today.month - 1) // 3 + 1
	limit = min(cint(limit) or 5, 50)
	return year, quarter, limit
 
 
@frappe.whitelist()
def get_top_customers(year=None, quarter=None, company=None, limit=5, sales_person=None):
	frappe.has_permission("Sales Invoice", "read", throw=True)
 
	year, quarter, limit = parse_args(year, quarter, limit)
	sales_persons = get_sales_persons(sales_person)
	from_date, to_date = get_quarter_range(year, quarter)
	currency = get_currency(company)
	result = {
		"rows": [],
		"currency": currency,
		"from_date": from_date,
		"to_date": to_date,
		"year": year,
		"quarter": quarter,
		"limit": limit,
		"sales_person": sales_person or "",
		"warnings": [],
	}
 
	# 1. Rank customers by invoiced amount (company currency, net of returns)
	si = frappe.qb.DocType("Sales Invoice")
	query = (
		frappe.qb.from_(si)
		.select(si.customer, Sum(si.base_grand_total).as_("total_invoice"))
		.where(si.docstatus == 1)
		.where(si.posting_date.between(from_date, to_date))
		.groupby(si.customer)
		.orderby(Sum(si.base_grand_total), order=frappe.qb.desc)
		.limit(limit)
	)
	if company:
		query = query.where(si.company == company)
	if sales_persons:
		si_sp = get_sales_person_field(frappe.get_meta("Sales Invoice"))
		if si_sp:
			query = query.where(si[si_sp].isin(sales_persons))
		else:
			result["warnings"].append(_("Sales Invoice has no field linked to Sales Person."))
			return result
	rows = query.run(as_dict=True)
 
	customers = [r.customer for r in rows]
	if not customers:
		return result
 
	names = {
		c.name: c.customer_name
		for c in frappe.get_all("Customer", filters={"name": ["in", customers]}, fields=["name", "customer_name"])
	}
 
	# 2. Job Order / Supply Order counts
	jo_counts = get_counts(JOB_ORDER, customers, from_date, to_date, result["warnings"], sales_persons)
	so_counts = get_counts(SUPPLY_ORDER, customers, from_date, to_date, result["warnings"], sales_persons)
 
	for r in rows:
		result["rows"].append(
			{
				"customer": r.customer,
				"customer_name": names.get(r.customer) or r.customer,
				"jo_received": jo_counts.get(r.customer, 0),
				"so_received": so_counts.get(r.customer, 0),
				"total_invoice": r.total_invoice or 0,
			}
		)
 
	return result
 
 
def resolve_config(cfg, warnings):
	"""Work out the real customer and date fields of the doctype."""
	doctype = cfg["doctype"]
	if not frappe.db.exists("DocType", doctype):
		warnings.append(_("DocType {0} was not found. Fix the name in top_customers.py.").format(doctype))
		return None
 
	meta = frappe.get_meta(doctype)
 
	if meta.istable:
		# child table inside Customer: the customer is the parent row
		cust_field, parent_filter = "parent", True
	else:
		parent_filter = False
		cust_field = cfg.get("customer_field")
		if not cust_field or not meta.has_field(cust_field):
			links = [df.fieldname for df in meta.fields if df.fieldtype == "Link" and df.options == "Customer"]
			if not links:
				warnings.append(_("{0} has no field linked to Customer.").format(doctype))
				return None
			cust_field = links[0]
 
	date_field = cfg.get("date_field")
	if not date_field or not meta.has_field(date_field):
		date_field = next((f for f in DATE_CANDIDATES if meta.has_field(f)), "creation")
 
	sp_field = None if meta.istable else get_sales_person_field(meta)
 
	return {
		"doctype": doctype,
		"cust": cust_field,
		"date": date_field,
		"parent_filter": parent_filter,
		"sp": sp_field,
	}
 
 
def get_sales_person_field(meta):
	"""The Sales Person docfield on a doctype: SALES_PERSON_FIELD, else the first Link to Sales Person."""
	df = meta.get_field(SALES_PERSON_FIELD)
	if df and df.fieldtype == "Link":
		return SALES_PERSON_FIELD
	return next(
		(d.fieldname for d in meta.fields if d.fieldtype == "Link" and d.options == "Sales Person"),
		None,
	)
 
 
def get_sales_persons(sales_person):
	"""The selected salesperson plus everyone under them in the Sales Person tree."""
	if not sales_person:
		return []
	return [sales_person, *get_descendants_of("Sales Person", sales_person)]
 
 
def get_counts(cfg, customers, from_date, to_date, warnings, sales_persons=None):
	conf = resolve_config(cfg, warnings)
	if not conf:
		return {}
 
	dt = frappe.qb.DocType(conf["doctype"])
	cust = dt[conf["cust"]]
 
	# creation is a datetime, so include the whole last day
	upper = f"{to_date} 23:59:59" if conf["date"] == "creation" else to_date
 
	query = (
		frappe.qb.from_(dt)
		.select(cust.as_("customer"), Count(dt.name).as_("cnt"))
		.where(cust.isin(customers))
		.where(dt[conf["date"]].between(from_date, upper))
		.where(dt.docstatus < 2)  # exclude cancelled
		.groupby(cust)
	)
	if conf["parent_filter"]:
		query = query.where(dt.parenttype == "Customer")
	if sales_persons:
		if not conf["sp"]:
			warnings.append(_("{0} has no field linked to Sales Person.").format(conf["doctype"]))
			return {}
		query = query.where(dt[conf["sp"]].isin(sales_persons))
 
	return {r.customer: r.cnt for r in query.run(as_dict=True)}
 
 
def get_currency(company=None):
	company = company or frappe.defaults.get_user_default("Company")
	if company:
		return frappe.get_cached_value("Company", company, "default_currency")
	return frappe.db.get_default("currency") or "SAR"
 
 
# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
PDF_TEMPLATE = """
<style>
	body { font-family: Arial, Helvetica, sans-serif; }
	h2 { color: #0b4f9c; font-size: 22px; margin: 0 0 4px; }
	.sub { color: #777; font-size: 11px; margin-bottom: 14px; }
	table { width: 100%; border-collapse: collapse; border: 2px solid #555; }
	th { background: #0b4f9c; color: #fff; font-size: 13px; padding: 12px 8px; text-align: center; }
	td { background: #f7f8fa; font-size: 12px; padding: 12px 8px; color: #333; }
	td.name { font-weight: bold; }
	td.c { text-align: center; }
	td.amt { text-align: center; font-weight: bold; }
</style>
<h2>Top {{ limit }} Customers of Q{{ quarter }} {{ year }}</h2>
<div class="sub">{{ from_date }} to {{ to_date }}{% if company %} | {{ company }}{% endif %}{% if sales_person %} | Sales Person: {{ sales_person }}{% endif %}</div>
<table>
	<thead>
		<tr><th>Customer Name</th><th>JO Received</th><th>SO Received</th><th>Total Invoice</th></tr>
	</thead>
	<tbody>
	{% for r in rows %}
		<tr>
			<td class="name">{{ r.customer_name }}</td>
			<td class="c">{{ r.jo_received }}</td>
			<td class="c">{{ r.so_received }}</td>
			<td class="amt">{{ r.total_fmt }}</td>
		</tr>
	{% else %}
		<tr><td colspan="4" class="c">No submitted Sales Invoices in this quarter.</td></tr>
	{% endfor %}
	</tbody>
</table>
"""
 
 
@frappe.whitelist()
def download_pdf(year=None, quarter=None, company=None, limit=5, sales_person=None):
	data = get_top_customers(year, quarter, company, limit, sales_person)
	for r in data["rows"]:
		r["total_fmt"] = fmt_money(r["total_invoice"], precision=0, currency=data["currency"])
 
	html = frappe.render_template(
		PDF_TEMPLATE,
		{
			**data,
			"company": company,
			"from_date": formatdate(data["from_date"]),
			"to_date": formatdate(data["to_date"]),
		},
	)
 
	frappe.local.response.filename = f"Top_{data['limit']}_Customers_Q{data['quarter']}_{data['year']}.pdf"
	frappe.local.response.filecontent = get_pdf(html)
	frappe.local.response.type = "pdf"
 
 
# ---------------------------------------------------------------------------
# Invoice split (popup when clicking Total Invoice)
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_invoice_breakdown(customer, year=None, quarter=None, company=None, sales_person=None):
	frappe.has_permission("Sales Invoice", "read", throw=True)
 
	year, quarter, _limit = parse_args(year, quarter, 5)
	from_date, to_date = get_quarter_range(year, quarter)
 
	filters = {
		"customer": customer,
		"docstatus": 1,
		"posting_date": ["between", [from_date, to_date]],
	}
	if company:
		filters["company"] = company
 
	sales_persons = get_sales_persons(sales_person)
	if sales_persons:
		sp_field = get_sales_person_field(frappe.get_meta("Sales Invoice"))
		if sp_field:
			filters[sp_field] = ["in", sales_persons]
 
	invoices = frappe.get_list(
		"Sales Invoice",
		filters=filters,
		fields=["name", "posting_date", "base_grand_total", "status", "is_return"],
		order_by="posting_date asc, name asc",
	)
 
	# split by month of the quarter (all three months shown, even if empty)
	months = []
	start = from_date
	for i in range(3):
		m = getdate(add_months(start, i))
		amount = sum(
			inv.base_grand_total or 0
			for inv in invoices
			if getdate(inv.posting_date).month == m.month and getdate(inv.posting_date).year == m.year
		)
		count = sum(
			1 for inv in invoices if getdate(inv.posting_date).month == m.month and getdate(inv.posting_date).year == m.year
		)
		months.append({"month": m.strftime("%B"), "amount": amount, "count": count})
 
	return {
		"customer": customer,
		"customer_name": frappe.db.get_value("Customer", customer, "customer_name") or customer,
		"invoices": invoices,
		"months": months,
		"total": sum(inv.base_grand_total or 0 for inv in invoices),
		"currency": get_currency(company),
		"from_date": from_date,
		"to_date": to_date,
	}