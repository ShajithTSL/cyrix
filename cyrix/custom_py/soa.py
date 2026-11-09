import re
import frappe
from frappe.utils import flt, getdate

# # Ordered so the output always reads SO, JO, BQ, MC
REF_FIELDS = [
	("supply_order_data", "SO"),
	("job_order_data", "JO"),
	("budgetary_quotation", "BQ"),
	("maintenance_contract", "MC"),
]

STATEMENT_TYPES = (
	"Without Credit Note",
	"With Credit Note",
	"All Transactions",
	"Only Outstanding Transactions",
)


# Column labels for ERPNext's range1..range5, exactly as the Accounts
# Receivable report names them (30/60/90/120 day ranges).
AGEING_LABELS = ("0-30", "31-60", "61-90", "91-120", "121-Above")


@frappe.whitelist()
def get_complete_customer_receivable(customer, from_date, to_date, company, statement_type, show_ageing=None):
	"""
	Entry point used by the print format. `statement_type` picks which of
	four views to render:

	- "Without Credit Note": a per-invoice snapshot of only outstanding
	  Sales Invoices, excluding Credit Notes entirely. This is the
	  classic accounts-receivable list - one row per unpaid invoice.
	- "With Credit Note": the same per-invoice snapshot, but Credit Notes
	  with their own unused/unapplied balance are included as rows too.
	- "All Transactions" (default, for backward compatibility with any
	  existing caller that doesn't pass statement_type): the full ledger
	  - every voucher type that hit the customer's receivable account,
	  in date order, with a running balance. See get_all_transactions_html
	  for the design notes on why this is GL Entry-driven. This includes
	  vouchers that have since fully settled (e.g. a paid-off invoice
	  still shows its debit and the offsetting payment's credit).
	- "Only Outstanding Transactions": every transaction type that still
	  has an open/unsettled amount against the customer right now -
	  outstanding invoices, open Credit Notes, AND Payment Entries that
	  still carry an unallocated (advance) amount. Unlike "All
	  Transactions", anything that has fully settled is left out
	  entirely rather than shown net-zero. See get_outstanding_transactions_html.

	Whichever view is picked, an ageing summary (by due date) is appended
	underneath it unless `show_ageing` is switched off. The ageing always
	comes straight from ERPNext's Accounts Receivable report for this
	customer (see get_ageing_html), so it is the same whichever view is
	picked and matches that report - it is NOT limited to the invoices,
	credit notes or payments the chosen view lists.

	`show_ageing` can be passed explicitly (1/0, True/False, "1"/"0"). When
	it isn't, it is read from frappe.form_dict - which is where the SOA
	dialog's checkbox arrives, since the print format already reads its
	other inputs from form_dict. If neither is present, ageing is shown,
	so existing callers behave exactly as before.
	"""

	if show_ageing is None:
		show_ageing = frappe.form_dict.get("show_ageing")
	show_ageing = as_flag(show_ageing, default=True)

	if statement_type == "Without Credit Note":
		html = get_outstanding_invoices_html(customer, from_date, to_date, company, include_credit_notes=False)
	elif statement_type == "With Credit Note":
		html = get_outstanding_invoices_html(customer, from_date, to_date, company, include_credit_notes=True)
	elif statement_type == "Only Outstanding Transactions":
		html = get_outstanding_transactions_html(customer, from_date, to_date, company)
	else:
		html = get_all_transactions_html(customer, from_date, to_date, company)

	if show_ageing:
		html += get_ageing_html(customer, to_date, company)

	return html


def get_all_transactions_html(customer, from_date, to_date, company):
	"""
	Builds an HTML Statement of Account for a customer covering ALL
	accounting transactions posted against them - Sales Invoices, Payment
	Entries, Journal Entries, Credit/Debit Notes, etc. - in chronological
	order with a running balance.

	Design note: like ERPNext's own General Ledger / Statement of Accounts
	reports, this is driven off `GL Entry` rather than off individual
	doctypes. GL Entry is the single source of truth for what actually hit
	the customer's receivable account, so nothing gets missed and nothing
	needs special-casing (e.g. the old "skip invoice if a credit note
	exists against it" hack is no longer needed - the credit note's own
	GL line nets it out automatically in the running balance).

	Per your note, this keeps Debit/Credit merged into the same two
	columns as before (Invoiced / Paid) rather than showing them
	separately, and keeps the WOD / PO reference columns from the
	original format.
	"""

	currency = frappe.get_cached_value("Company", company, "default_currency")

	opening_balance = get_opening_balance(customer, company, from_date)
	entries = get_gl_entries(customer, company, from_date, to_date)

	si_names = list({e.voucher_no for e in entries if e.voucher_type == "Sales Invoice"})
	wod_map, po_map = get_sales_invoice_refs(si_names)

	data = get_style()
	data += '<table class="table-receivable">'
	data += """
	<tr>
		<th style="width:9%">Invoice Date</th>
		<th style="width:9%">Due Date</th>

		<th style="width:13%">Voucher No</th>
		<th style="width:19%">Reference Transactions</th>
		<th style="width:21%">Ref (PO)</th>
		<th style="width:10%; text-align: right">Invoiced</th>
		<th style="width:9%; text-align: right">Paid</th>
		<th style="width:10%; text-align: right">Balance</th>
	</tr>
	"""

	running_balance = flt(opening_balance)

	data += f"""
	<tr>
		<td>{getdate(from_date).strftime('%d-%m-%Y')}</td>
		<td colspan="5" class="bold" style = "text-align: center;">Opening Balance</td>
		<td></td>
		<td class="text-right bold">{fmt(running_balance)}</td>
	</tr>
	"""

	for e in entries:
		running_balance += flt(e.debit) - flt(e.credit)

		label, link = get_voucher_link(e)

		if e.voucher_type == "Sales Invoice":
			wod = wod_map.get(e.voucher_no, "")
			po = po_map.get(e.voucher_no, "")
		else:
			# For payments / journal entries, show which invoice they were
			# applied against (if any) in place of the WOD/PO columns.
			wod = f'Against <span class="nw">{e.against_voucher}</span>' if e.against_voucher else ""
			po = ""

		invoiced = fmt(e.debit) if e.debit else ""
		paid = fmt(e.credit) if e.credit else ""

		due_date = getdate(e.due_date).strftime('%d-%m-%Y') if e.due_date else "-"
		data += f"""
		<tr>
			<td>{getdate(e.posting_date).strftime('%d-%m-%Y')}</td>
			<td class="text-center">{due_date}</td>
			<td class="text-center">
				<a href="{link}" class="invoice-link" target="_blank">{label}</a>
			</td>
			<td class="text-center">{wod}</td>
			<td class="text-center">{po}</td>
			<td class="text-right">{invoiced}</td>
			<td class="text-right">{paid}</td>
			<td class="text-right bold">{fmt(running_balance)}</td>
		</tr>
		"""

	data += f"""
	<tr class="total-row">
		<td colspan="7" class="text-right bold">
			Balance Due <span class="currency">({currency})</span>
		</td>
		<td class="text-right bold">{fmt(running_balance)}</td>
	</tr>
	"""

	data += '</table>'
	data += '<p></p>'

	return data


def fmt(value):
	# round first and add 0.0 so float noise never prints as "-0.000"
	return "{:,.3f}".format(round(flt(value), 3) + 0.0)


def as_flag(value, default=True):
	"""Turns a checkbox-style value into a bool. Request params arrive as
	strings ("0"/"1"), JS sends 0/1, Python callers may pass True/False."""
	if value is None:
		return default
	return str(value).strip().lower() not in ("0", "false", "no", "", "none")


def get_opening_balance(customer, company, from_date):
	"""Net balance of everything posted to the customer's receivable
	account before the statement's start date."""
	result = frappe.db.sql(
		"""
		SELECT SUM(debit) - SUM(credit) AS balance
		FROM `tabGL Entry`
		WHERE party_type = 'Customer'
		  AND party = %(customer)s
		  AND company = %(company)s
		  AND posting_date < %(from_date)s
		  AND is_cancelled = 0
		""",
		{"customer": customer, "company": company, "from_date": from_date},
		as_dict=1,
	)
	return flt(result[0].balance) if result and result[0].balance else 0


def get_gl_entries(customer, company, from_date, to_date):
	return frappe.db.sql(
		"""
		SELECT
			posting_date,
			due_date,
			voucher_type,
			voucher_no,
			against_voucher,
			remarks,
			debit,
			credit
		FROM `tabGL Entry`
		WHERE party_type = 'Customer'
		  AND party = %(customer)s
		  AND company = %(company)s
		  AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		  AND is_cancelled = 0
		ORDER BY posting_date ASC, creation ASC
		""",
		{
			"customer": customer,
			"company": company,
			"from_date": from_date,
			"to_date": to_date,
		},
		as_dict=1,
	)

def _short_ref(value, abbr):
	"""'SO-2025-00001' -> 'SO-00001' (abbreviation + last five digits)."""
	digits = re.sub(r"\D", "", str(value or ""))
	return f"{abbr}-{digits[-5:]}" if digits else ""


def get_sales_invoice_refs(si_names):
	"""Build SO / JO / BQ / MC references (comma separated) and PO No,
	keyed by invoice name so they can be looked up per GL row."""
	jo_map, po_map = {}, {}
	if not si_names:
		return jo_map, po_map

	rows = frappe.db.sql(
		"""
		SELECT parent,
			supply_order_data,
			job_order_data,
			budgetary_quotation,
			maintenance_contract,
			order_no
		FROM `tabSales Invoice Item`
		WHERE parent IN %(names)s
		""",
		{"names": si_names},
		as_dict=1,
	)

	# parent -> {abbr: set(refs)}, plus a fallback set for order_no
	grouped = {}
	for r in rows:
		bucket = grouped.setdefault(
			r.parent, {"refs": {abbr: set() for _, abbr in REF_FIELDS}, "order_no": set()}
		)
		found = False
		for field, abbr in REF_FIELDS:
			ref = _short_ref(r.get(field), abbr)
			if ref:
				bucket["refs"][abbr].add(ref)
				found = True
		if not found and r.order_no:
			bucket["order_no"].add(r.order_no)

	for name, bucket in grouped.items():
		vals = []
		for _, abbr in REF_FIELDS:
			vals.extend(sorted(bucket["refs"][abbr]))
		vals.extend(sorted(bucket["order_no"]))
		jo_map[name] = ", ".join(vals)

	for r in frappe.get_all(
		"Sales Invoice", filters={"name": ["in", si_names]}, fields=["name", "po_no"]
	):
		po_map[r.name] = r.po_no or ""

	return jo_map, po_map


def get_sales_invoice_pdf_link(invoice_name):
	"""The customer-facing PDF download link for a single Sales Invoice
	(or Credit Note - Credit Notes are just Sales Invoices with is_return
	set, so the same print format/link works for both)."""

	return invoice_name

def get_voucher_link(entry):
	"""Returns (display_label, url) for a GL Entry's originating voucher."""
	voucher_type = entry.voucher_type
	voucher_no = entry.voucher_no

	if voucher_type == "Sales Invoice":
		link = get_sales_invoice_pdf_link(voucher_no)
		is_return = frappe.get_cached_value("Sales Invoice", voucher_no, "is_return")
		label = f"{voucher_no}<br>(Credit Note)" if is_return else voucher_no
		return label, link

	# Payment Entry, Journal Entry, etc. - link to the document itself.
	# (They don't have a dedicated customer-facing PDF format like the
	# invoice does, so this links to the desk form.)
	route = voucher_type.lower().replace(" ", "-")
	link = f"/app/{route}/{voucher_no}"
	return voucher_no, link


def get_outstanding_invoices_html(customer, from_date, to_date, company, include_credit_notes):
	"""
	Per-invoice snapshot (no running balance, no payments/journal entries
	as their own rows) - one row per Sales Invoice that still carries a
	non-zero outstanding_amount, in the style of the very first version
	of this report.

	include_credit_notes=False -> "Without Credit Note": only regular
	invoices (is_return=0).
	include_credit_notes=True -> "With Credit Note": also includes Credit
	Notes (is_return=1) that still have their own unused/unapplied
	balance.
	"""

	currency = frappe.get_cached_value("Company", company, "default_currency")

	filters = {
		"company": company,
		"customer": customer,
		"docstatus": 1,
		"posting_date": ["between", (from_date, to_date)],
		"outstanding_amount": ["!=", 0],
	}
	if not include_credit_notes:
		filters["is_return"] = 0

	invoices = frappe.get_all(
		"Sales Invoice",
		filters=filters,
		fields=["name", "posting_date", "due_date", "grand_total", "outstanding_amount", "po_no", "is_return"],
		order_by="posting_date asc",
	)

	si_names = [i.name for i in invoices]
	wod_map, po_map = get_sales_invoice_refs(si_names)

	data = get_style()
	data += '<table class="table-receivable">'
	data += """
	<tr>
		<th style="width:9%">Invoice Date</th>
		<th style="width:9%">Due Date</th>

		<th style="width:13%">Voucher No</th>
		<th style="width:19%">Reference Transactions</th>
		<th style="width:21%">Ref (PO)</th>
		<th style="width:10%; text-align: right">Invoiced</th>
		<th style="width:9%; text-align: right">Paid</th>
		<th style="width:10%; text-align: right">Outstanding</th>
	</tr>
	"""

	total_outstanding = 0
	for inv in invoices:
		total_outstanding += flt(inv.outstanding_amount)

		date = getdate(inv.posting_date).strftime('%d-%m-%Y') if inv.posting_date else ""
		due = getdate(inv.due_date).strftime('%d-%m-%Y') if inv.due_date else ""
		label = f"{inv.name}<br>(Credit Note)" if inv.is_return else inv.name
		link = get_sales_invoice_pdf_link(inv.name)
		wod = wod_map.get(inv.name, "")
		po = po_map.get(inv.name, "")
		paid = flt(inv.grand_total) - flt(inv.outstanding_amount)

		data += f"""
		<tr>
			<td>{date}</td>
			<td>{due}</td>
			<td class="text-center">
				<a href="{link}" class="invoice-link" target="_blank">{label}</a>
			</td>
			<td class="text-center">{wod}</td>
			<td class="text-center">{po}</td>
			<td class="text-right">{fmt(inv.grand_total)}</td>
			<td class="text-right">{fmt(paid)}</td>
			<td class="text-right bold">{fmt(inv.outstanding_amount)}</td>
		</tr>
		"""

	data += f"""
	<tr class="total-row">
		<td colspan="7" class="text-right bold">
			Balance Due <span class="currency">({currency})</span>
		</td>
		<td class="text-right bold">{fmt(total_outstanding)}</td>
	</tr>
	"""

	data += '</table>'
	data += '<p></p>'

	return data


def get_outstanding_transactions_html(customer, from_date, to_date, company):
	"""
	Like "With Credit Note", but broadened beyond just Sales Invoices:
	lists every transaction type that still has an open/unsettled amount
	against this customer right now - outstanding Sales Invoices, open
	Credit Notes, AND Payment Entries that still carry an unallocated
	(advance) amount sitting on the customer's account.

	This differs from "All Transactions": that view is the full
	chronological history, so a paid-off invoice still shows up (its
	debit and the offsetting payment's credit just net to zero in the
	running balance). This view drops anything that has fully settled -
	only genuinely open items appear, each shown at its own outstanding
	amount rather than as a running balance (since skipping settled rows
	means there's no continuous balance to run).

	Limitation: Journal Entries against the customer are not included.
	Unlike Payment Entry (which has a standard `unallocated_amount`
	field), there's no generic field on Journal Entry that says whether
	a given JE line against a customer is still "open" - that depends on
	how you use JEs (write-offs, manual adjustments, advance reversals,
	etc.). If you do post JEs against customers and want them considered
	here, let me know how "still outstanding" should be determined for
	those and this can be extended.
	"""

	currency = frappe.get_cached_value("Company", company, "default_currency")

	invoices = frappe.get_all(
		"Sales Invoice",
		filters={
			"company": company,
			"customer": customer,
			"docstatus": 1,
			"posting_date": ["between", (from_date, to_date)],
			"outstanding_amount": ["!=", 0],
		},
		fields=["name", "posting_date", "due_date", "grand_total", "outstanding_amount", "po_no", "is_return"],
		order_by="posting_date asc",
	)

	payments = frappe.get_all(
		"Payment Entry",
		filters={
			"company": company,
			"party_type": "Customer",
			"party": customer,
			"docstatus": 1,
			"posting_date": ["between", (from_date, to_date)],
			"unallocated_amount": ["!=", 0],
		},
		fields=["name", "posting_date", "unallocated_amount"],
		order_by="posting_date asc",
	)

	si_names = [i.name for i in invoices]
	wod_map, po_map = get_sales_invoice_refs(si_names)

	rows = []
	for inv in invoices:
		rows.append({
			"sort_date": inv.posting_date,
			"date": getdate(inv.posting_date).strftime('%d-%m-%Y'),
			"due_date": getdate(inv.due_date).strftime('%d-%m-%Y'),
			"label": f"{inv.name}<br>(Credit Note)" if inv.is_return else inv.name,
			"link": get_sales_invoice_pdf_link(inv.name),
			"wod": wod_map.get(inv.name, ""),
			"po": po_map.get(inv.name, ""),
			"invoiced": fmt(inv.grand_total),
			"paid": fmt(flt(inv.grand_total) - flt(inv.outstanding_amount)),
			"outstanding": flt(inv.outstanding_amount),
		})

	for pe in payments:
		# An unallocated amount is money the customer has already paid
		# that hasn't been applied against any invoice yet - it reduces
		# what they owe, so it contributes negatively to the outstanding
		# total, the same way an unused credit note does.
		rows.append({
			"sort_date": pe.posting_date,
			"date": getdate(pe.posting_date).strftime('%d-%m-%Y'),
			"due_date": "-",
			"label": f"{pe.name}<br>(Unallocated Advance)",
			"link": f"/app/payment-entry/{pe.name}",
			"wod": "",
			"po": "",
			"invoiced": "",
			"paid": fmt(pe.unallocated_amount),
			"outstanding": -flt(pe.unallocated_amount),
		})

	rows.sort(key=lambda r: r["sort_date"])

	data = get_style()
	data += '<table class="table-receivable">'
	data += """
	<tr>
		<th style="width:9%">Invoice Date</th>
		<th style="width:9%">Due Date</th>

		<th style="width:13%">Voucher No</th>
		<th style="width:19%">Reference Transactions</th>
		<th style="width:21%">Ref (PO)</th>
		<th style="width:10%; text-align: right">Invoiced</th>
		<th style="width:9%; text-align: right">Paid</th>
		<th style="width:10%; text-align: right">Outstanding</th>
	</tr>
	"""

	total_outstanding = 0
	for r in rows:
		total_outstanding += r["outstanding"]

		data += f"""
		<tr>
			<td>{r['date']}</td>
			<td>{r['due_date']}</td>
			<td class="text-center">
				<a href="{r['link']}" class="invoice-link" target="_blank">{r['label']}</a>
			</td>
			<td class="text-center">{r['wod']}</td>
			<td class="text-center">{r['po']}</td>
			<td class="text-right">{r['invoiced']}</td>
			<td class="text-right">{r['paid']}</td>
			<td class="text-right bold">{fmt(r['outstanding'])}</td>
		</tr>
		"""

	data += f"""
	<tr class="total-row">
		<td colspan="7" class="text-right bold">
			Balance Due <span class="currency">({currency})</span>
		</td>
		<td class="text-right bold">{fmt(total_outstanding)}</td>
	</tr>
	"""

	data += '</table>'
	data += '<p></p>'

	return data


def get_ageing_html(customer, to_date, company):
	"""
	Ageing summary by DUE DATE as of the statement's To Date, taken
	straight from ERPNext's own Accounts Receivable Summary report.

	Why it isn't worked out here: an earlier version summed each Sales
	Invoice's outstanding_amount into buckets itself, and that could not
	match the Accounts Receivable report. That report is built from the
	Payment Ledger, also ages Journal Entries and unallocated payments (by
	posting date), nets credit notes its own way, and can age against
	today instead of the report date. Calling the report itself - with the
	same filters ERPNext's Process Statement of Accounts uses for its
	ageing - removes any chance of drift.

	Filters: report_date = To Date, ageing based on Due Date, ranges
	30/60/90/120, this customer only, and age_as_on = "Report Date" so
	ageing is measured at To Date rather than today.

	Reading the result: range1..range5 are the OVERDUE buckets (0-30 ...
	121-Above). Anything not yet due sits in no bucket, so "Not Due" is
	derived as outstanding - sum(buckets). "Total Outstanding" is the
	report's Outstanding Amount, which is net of credit notes and advances
	- the figure to compare with the Accounts Receivable report.

	Matches ERPNext 14 and 15, which both call the report this way. A
	customer with nothing outstanding gets no row back, shown as zeros.

	"Unallocated" is the report's own Advance Amount: payments received
	but not yet allocated to an invoice. ERPNext already nets it into the
	buckets (aged by posting date) and into Total Outstanding, so it is a
	memo column placed after the total and labelled as included - adding it
	to the other columns would double count and break the match.
	If the report can't be called (e.g. a different ERPNext version) this
	raises rather than quietly printing numbers that don't match.
	"""

	currency = frappe.get_cached_value("Company", company, "default_currency")
	report_date = getdate(to_date)

	try:
		from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import (
			execute as get_ar_summary,
		)

		result = get_ar_summary(frappe._dict({
			"company": company,
			"report_date": to_date,
			"age_as_on": "Report Date",
			"ageing_based_on": "Due Date",
			"range1": 30,
			"range2": 60,
			"range3": 90,
			"range4": 120,
			"party_type": "Customer",
			"party": [customer],
		}))
		rows = result[1]
	except Exception:
		frappe.log_error(title="Statement of Account: ageing from Accounts Receivable failed")
		frappe.throw(
			frappe._(
				"Could not read the ageing from the Accounts Receivable report. "
				"Untick 'Show Ageing Summary' to continue without it, and check the Error Log."
			)
		)

	row = rows[0] if rows else {}
	buckets = [flt(row.get(f"range{i}")) for i in range(1, len(AGEING_LABELS) + 1)]
	outstanding = flt(row.get("outstanding"))
	not_due = outstanding - sum(buckets)

	# Unallocated payments / advances on account, as the Accounts Receivable
	# Summary reports them (positive there; shown as a credit, i.e. negative).
	# Already netted into the buckets and Total Outstanding above, so this
	# column is for information and is NOT added again.
	unallocated = -abs(flt(row.get("advance")))

	headers = "".join(
		f'<th style="text-align: right">{label}</th>' for label in ("Not Due",) + AGEING_LABELS
	)
	cells = "".join(f'<td class="text-right">{fmt(v)}</td>' for v in [not_due] + buckets)

	return f"""
	<div class="ageing-title">
		Ageing Summary
		<span class="currency">(by due date, as of {report_date.strftime('%d-%m-%Y')}, {currency})</span>
	</div>
	<table class="table-receivable ageing-table">
		<tr>
			{headers}
			<th style="text-align: right">Total Outstanding</th>
			<th style="text-align: right">Unallocated*</th>
		</tr>
		<tr>
			{cells}
			<td class="text-right bold">{fmt(outstanding)}</td>
			<td class="text-right">{fmt(unallocated)}</td>
		</tr>
	</table>
	<div class="ageing-note">* Unallocated payments / advances on account. Already included in the figures above.</div>
	<p></p>
	"""


def get_style():
	return """
	<style>
	.table-receivable {
		width: 100%;
		border-collapse: collapse;
		font-family: 'Segoe UI', Tahoma, sans-serif;
		color: #2c3e50;
	}

	.table-receivable th {
		background-color: #1a4d8c;
		color: #ffffff;
		font-size: 10px !important;
		font-weight: 600;
		padding: 7px 8px;
		text-align: center;
		border-bottom: 2px solid #163d6b;
		letter-spacing: 0.3px;
	}

	/* Row density: the vertical padding and line-height below are what set
	   how many rows fit on a page. Smaller = more rows per page. */
	.table-receivable td {
		font-size: 9px !important;
		padding: 3px 6px;
		line-height: 1.25;
		border-bottom: 1px solid #e6e9ef;
	}

	/* never split one row across two pages */
	.table-receivable tr {
		page-break-inside: avoid;
	}

	.table-receivable tr:nth-child(even) {
		background-color: #fbfcfe;
	}

	.table-receivable tr:hover {
		background-color: #f1f6ff;
	}

	.text-center { text-align: center; }
	/* amounts must never wrap, whatever the page width */
	.text-right { text-align: right; white-space: nowrap; }
	.bold { font-weight: 600; }
	.nw { white-space: nowrap; }

	/* first two columns are the dates: keep each on one line */
	.table-receivable td:nth-child(1),
	.table-receivable td:nth-child(2) {
		white-space: nowrap;
	}

	/* a voucher number is a single token - don't break it at its hyphens */
	.invoice-link {
		text-decoration: none;
		color: #1a4d8c;
		font-weight: 600;
		white-space: nowrap;
	}

	.invoice-link:hover {
		text-decoration: underline;
	}

	.total-row td {
		border-top: 2px solid #1a4d8c;
		background-color: #f4f7fb;
		font-size: 12px !important;
		padding: 7px 6px;
	}

	.currency {
		color: #7f8c8d;
		font-weight: 500;
	}

	.ageing-title {
		font-family: 'Segoe UI', Tahoma, sans-serif;
		font-size: 11px;
		font-weight: 600;
		color: #1a4d8c;
		margin: 14px 0 6px 0;
	}

	.ageing-note {
		font-size: 9px;
		color: #7f8c8d;
		margin-top: 3px;
	}

	.ageing-table td {
		font-size: 10px !important;
		padding: 8px 8px;
	}

	</style>
	"""


import frappe
from frappe.utils.pdf import get_pdf
from frappe.utils.jinja import get_jenv
from frappe.utils.file_manager import save_file
from frappe.utils import nowdate


def render_soa_html(customer, from_date, to_date, company, statement_type, show_ageing=None):

	print_format_name = "Customer Receivables"

	doc = frappe.get_doc("Customer", customer)

	print_format = frappe.get_doc(
		"Print Format",
		print_format_name
	)

	jenv = get_jenv()
	template = jenv.from_string(print_format.html)

	body = template.render({
		"doc": doc,
		"customer": customer,
		"from_date": from_date,
		"to_date": to_date,
		"company": company,
		"print_format": print_format_name,
		"no_letterhead": 0,
		"statement_type": statement_type,
		"show_ageing": show_ageing,
	})

	# print_format.html is only the body markup - any styling defined in
	# the Print Format's own "CSS" tab (print_format.css) lives separately
	# and is normally stitched in by Frappe's standard print/preview
	# pipeline. Since we render manually with a raw Jinja template instead
	# of going through that pipeline, we have to bring it in ourselves or
	# it silently gets dropped (this is what was causing the boxed
	# Address / For Payment / Bank Details sections to lose their
	# borders in both the PDF and the edit preview).
	if print_format.css:
		body = f"<style>{print_format.css}</style>\n{body}"

	return body

@frappe.whitelist()
def get_soa_html_for_edit(customer, from_date, to_date, company, statement_type="All Transactions", show_ageing=None):
	"""Returns the rendered statement as an HTML string for the front end
	to drop into an editable container before the team turns it into a
	PDF. No PDF is generated here - this is the "preview to edit" step."""

	frappe.has_permission("Customer", "read", customer, throw=True)
	return render_soa_html(customer, from_date, to_date, company, statement_type, show_ageing)


@frappe.whitelist()
def save_edited_soa_pdf(customer, html, from_date=None, to_date=None, orientation="Portrait"):
	"""Takes whatever HTML the team ended up with after editing (fixed
	wording, adjusted rows, added remarks - anything) and turns exactly
	that into a PDF, attached to the Customer record so there is a
	record of what was actually generated and sent out.

	`orientation` is "Portrait" or "Landscape" and is handed to
	wkhtmltopdf as the page orientation. Anything else falls back to
	Portrait.

	`html` is trusted only insofar as the calling user already has write
	access to this Customer - see the permission check below. It is
	still just converted to PDF by wkhtmltopdf, so malformed markup left
	over from in-browser editing (an unclosed tag, a stray span) will at
	worst render oddly, not break anything server-side.
	"""

	frappe.has_permission("Customer", "write", customer, throw=True)

	orientation = "Landscape" if str(orientation).strip().lower() == "landscape" else "Portrait"
	pdf = get_pdf(html, {"orientation": orientation})

	date_bit = f"_{from_date}_to_{to_date}" if from_date and to_date else f"_{nowdate()}"
	filename = f"{customer}_SOA{date_bit}.pdf"

	file_doc = save_file(filename, pdf, "Customer", customer, is_private=1)

	return {
		"file_url": file_doc.file_url,
		"file_name": file_doc.file_name,
	}