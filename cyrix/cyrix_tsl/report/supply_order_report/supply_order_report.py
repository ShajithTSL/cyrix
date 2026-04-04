import frappe
from frappe import _
from erpnext.setup.utils import get_exchange_rate


def execute(filters=None):
	if not validate_filters(filters):
		frappe.throw(_("Invalid filters provided. Please select From Date, To Date, and Branch."))

	columns = get_columns()
	data = get_data(filters)
	return columns, data


def validate_filters(filters):
	"""Ensure mandatory filters are provided."""
	return bool(filters and filters.get("from_date") and filters.get("to_date") and filters.get("branch"))


def get_columns():
	"""Define report columns."""
	return [
		{"label": _("Supply Order"), "fieldname": "job_order", "fieldtype": "Link", "options": "Supply Order Data", "width": 140},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 150},
		{"label": _("Sales Person"), "fieldname": "sales_person", "fieldtype": "Link", "options": "Sales Person", "width": 130},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 280},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 100},
		{"label": _("MFG"), "fieldname": "mfg", "fieldtype": "Data", "width": 100},
		{"label": _("Model No"), "fieldname": "model_no", "fieldtype": "Data", "width": 140},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 180},
		{"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Float", "width": 100},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 100},
		{"label": _("Customer Reference"), "fieldname": "customer_reference", "fieldtype": "Data", "width": 200},
		{"label": _("Quoted Date"), "fieldname": "quoted_date", "fieldtype": "Date", "width": 150},
		{"label": _("Approval Date"), "fieldname": "approval_date", "fieldtype": "Date", "width": 150},
		{"label": _("Payment Reference"), "fieldname": "payment_entry_reference", "fieldtype": "Data", "width": 170},
		{"label": _("Payment Date"), "fieldname": "payment_date", "fieldtype": "Date", "width": 150},
		{"label": _("Delivery Note"), "fieldname": "delivery_note", "fieldtype": "Link", "options": "Delivery Note", "width": 160},
		{"label": _("Delivery Date"), "fieldname": "delivery_date", "fieldtype": "Date", "width": 150},
		{"label": _("Invoice No"), "fieldname": "invoice_no", "fieldtype": "Link", "options": "Sales Invoice", "width": 160},
		{"label": _("Invoice Date"), "fieldname": "invoice_date", "fieldtype": "Date", "width": 150},
		{"label": _("Quoted Amount"), "fieldname": "quoted_amount", "fieldtype": "Currency", "options":"currency", "width": 150},
		{"label": _("VAT Amount"), "fieldname": "vat_amount", "fieldtype": "Currency", "options":"currency", "width": 150},
		{"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "options":"currency", "width": 150},
		{"label": _("Quotation"), "fieldname": "quotation", "fieldtype": "Link", "options": "Quotation", "width": 100},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 150},
	]


def get_data(filters):
	"""Get supply order and material-wise report data."""
	rows = []
	supply_orders = get_supply_orders(filters)

	for order in supply_orders:
		materials = get_supply_order_materials(order.name)

		for material in materials:
			quote = get_quotation_details(order.name, material.model_no)

			rows.append({
				"job_order": order.name,
				"posting_date": order.posting_date,
				"sales_person": order.sales_person,
				"company": order.company,
				"branch": order.branch,
				"mfg": material.mfg,
				"model_no": frappe.db.get_value("Item Model", material.model_no, "model"),
				"item_name": material.item_name,
				"quantity": material.quantity,
				"customer": order.customer,
				"customer_reference": order.customer_reference_number,
				"quoted_date": quote.get("quoted_date"),
				"approval_date": quote.get("approval_date"),
				"quotation": quote.get("quote_name"),
				"quoted_amount": quote.get("amount", 0),
				"delivery_note": order.dn_no,
				"delivery_date": order.dn_date,
				"invoice_no": order.invoice_no,
				"invoice_date": order.invoice_date,
				"payment_entry_reference": order.payment_entry,
				"payment_date": order.advance_paid_date,
				"status": order.status,
				"total_amount": quote.get("amount", 0),  # taxes can be added later,
				"currency": frappe.get_value("Company", order.company, "default_currency")
			})

	return rows


def get_supply_orders(filters):
	"""Fetch Supply Orders within date and branch filters."""
	return frappe.get_all(
		"Supply Order Data",
		filters={
			"posting_date": ["between", (filters["from_date"], filters["to_date"])],
			"branch": filters.get("branch"),
		},
		fields=["*"],
	)


def get_supply_order_materials(order_name):
	"""Fetch materials linked to a Supply Order."""
	return frappe.db.sql(
		"""
		SELECT mfg, model_no, quantity, item_name, parent as quote_name
		FROM `tabSupply Order Table`
		WHERE parent = %s
		""",
		order_name,
		as_dict=1,
	)


def get_quotation_details(order_name, model_no):
	"""Fetch Quotation details for a given Supply Order and model."""
	result = frappe.db.sql(
		"""
		SELECT qi.net_amount as amount,
		       q.transaction_date as quoted_date,
		       q.approval_date as approval_date,
		       q.name as quote_name
		FROM `tabQuotation` q
		JOIN `tabQuotation Item` qi ON q.name = qi.parent
		WHERE qi.supply_order_data = %s
		  AND qi.model = %s
		  AND q.workflow_state = "Approved By Customer"
		LIMIT 1
		""",
		(order_name, model_no),
		as_dict=1,
	)
	return result[0] if result else {}
