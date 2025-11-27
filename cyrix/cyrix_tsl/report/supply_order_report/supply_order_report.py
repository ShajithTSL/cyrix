# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt



# import frappe
# from frappe import _
# from datetime import datetime, timedelta
# from erpnext.setup.utils import get_exchange_rate

# def execute(filters=None):
# 	columns = get_columns(filters)
# 	data = get_data(filters) 
# 	return columns, data

# def get_columns(filters):
# 	# Define columns you want to show in your report, including material columns
# 	columns = [
# 		{
# 			"label": _("Supply Order"),
# 			"fieldname": "job_order",
# 			"fieldtype": "Link",
# 			"options": "Supply Order Data",
# 			"width": 140
# 		},
# 		{
# 			"label": _("Posting Date"),
# 			"fieldname": "posting_date",
# 			"fieldtype": "Date",
# 			"width": 150
# 		},
# 		{
# 			"label": _("Sales Person"),
# 			"fieldname": "sales_person",
# 			"fieldtype": "Link",
# 			"options": "Sales Person",
# 			"width": 130
# 		},
# 		{
# 			"label": _("Company"),
# 			"fieldname": "company",
# 			"fieldtype": "Link",
# 			"options": "Company",
# 			"width": 280
# 		},
# 		{
# 			"label": _("Branch"),
# 			"fieldname": "branch",
# 			"fieldtype": "Link",
# 			"options": "Branch",
# 			"width": 100
# 		},
# 		{
# 			"label": _("MFG"),
# 			"fieldname": "mfg",
# 			"fieldtype": "Data",
# 			"width": 100
# 		},
# 		{
# 			"label": _("Model No"),
# 			"fieldname": "model_no",
# 			"fieldtype": "Data",
# 			"width": 140
# 		},
# 		{
# 			"label": _("Item Name"),
# 			"fieldname": "item_name",
# 			"fieldtype": "Data",
# 			"width": 180
# 		},
# 		{
# 			"label": _("Quantity"),
# 			"fieldname": "quantity",
# 			"fieldtype": "Float",
# 			"width": 100
# 		},
# 		{
# 			"label": _("Customer"),
# 			"fieldname": "customer",
# 			"fieldtype": "Link",
# 			"options": "Customer",
# 			"width": 100
# 		},
# 		{
# 			"label": _(" Customer Reference"),
# 			"fieldname": "customer_reference",
# 			"fieldtype": "Data",
# 			"width": 200
# 		},
# 		{
# 			"label": _("Quoted Date"),
# 			"fieldname": "quoted_date",
# 			"fieldtype": "Date",
# 			"width": 150
# 		},
# 		{
# 			"label": _("Approval Date"),
# 			"fieldname": "approval_date",
# 			"fieldtype": "Date",
# 			"width": 150
# 		},
# 		{
# 			"label": _("Payment Reference"),
# 			"fieldname": "payment_entry_reference",
# 			"fieldtype": "Data",
# 			"width": 170
# 		},
# 		{
# 			"label": _("Payment Date"),
# 			"fieldname": "payment_date",
# 			"fieldtype": "Date",
# 			"width": 150
# 		},
# 		{
# 			"label": _("Delivery Note"),
# 			"fieldname": "delivery_note",
# 			"fieldtype": "Link",
# 			"options": "Delivery Note",
# 			"width": 160
# 		},
# 		{
# 			"label": _("Delivery Date"),
# 			"fieldname": "delivery_date",
# 			"fieldtype": "Date",
# 			"width": 150
# 		},
# 		{
# 			"label": _("Invoice No"),
# 			"fieldname": "invoice_no",
# 			"fieldtype": "Link",
# 			"options": "Sales Invoice",
# 			"width": 160
# 		},
# 		{
# 			"label": _("Invoice Date"),
# 			"fieldname": "invoice_date",
# 			"fieldtype": "Date",
# 			"width": 150
# 		},
# 		{
# 			"label": _(" Quoted Amount"),
# 			"fieldname": "quoted_amount",
# 			"fieldtype": "Currency",
# 			"width": 150
# 		},
# 		{
# 			"label": _("VAT Amount"),
# 			"fieldname": "vat_amount",
# 			"fieldtype": "Currency",
# 			"width": 150
# 		},
# 		{
# 			"label": _("Total Amount"),
# 			"fieldname": "total_amount",
# 			"fieldtype": "Currency",
# 			"width": 150
# 		},
# 		{
# 			"label": _("Quotation"),
# 			"fieldname": "quotation",
# 			"fieldtype": "Link",
# 			"options": "Quotation",
# 			"width": 100
# 		},
# 		{
# 			"label": _("Status"),
# 			"fieldname": "status",
# 			"fieldtype": "Data",
# 			"width": 150
# 		}
# 	]
# 	return columns

# def get_data(filters):
# 	row = []
# 	# Ensure filters are being passed correctly
# 	if filters and filters.get('from_date') and filters.get('to_date') and filters.get('branch'):
# 		# First query to get Supply Order Data
# 		supply_order_data = frappe.get_all(
# 			"Supply Order Data",
# 			filters={
# 				"posting_date": ["between", (filters["from_date"], filters["to_date"])],
# 				"branch": filters.get('branch')
# 			},
# 			fields=["*"]
# 		)

# 		for jo in supply_order_data:
# 			# Fetch materials related to the current Supply order using a second query
# 			material_list_data = frappe.db.sql(''' 
# 				SELECT type, mfg, model_no, quantity, item_name, parent as quote_name
# 				FROM `tabSupply Order Table`
# 				WHERE parent = %s
# 			''', jo.name, as_dict=1)

# 			# For each material item, fetch the corresponding quotation details
# 			for material in material_list_data:
# 				# Fetch quoted amount for each material item from tabQuotation Item
# 				quote_details = frappe.db.sql(''' 
# 					SELECT `tabQuotation Item`.net_amount as amount,
# 						`tabQuotation`.transaction_date as quoted_date,
# 						`tabQuotation`.approval_date as approval_date,
# 						`tabQuotation`.type_of_approval as approval_type,
# 						`tabQuotation`.name as quote_name
# 					FROM `tabQuotation`
# 					JOIN `tabQuotation Item` 
# 					ON `tabQuotation`.name = `tabQuotation Item`.parent
# 					WHERE `tabQuotation Item`.supply_order_data = %s
# 					AND `tabQuotation Item`.model_no = %s
# 					AND `tabQuotation`.workflow_state = "Approved By Customer"
# 				''', (jo.name, material.model_no), as_dict=1)

# 				quoted_amount = 0
# 				quoted_date = ''
# 				approval_type = ''
# 				approval_date = ''
# 				quote_name = ''

# 				if quote_details:
# 					# Assuming that the quotation details will always return exactly one row for each material
# 					quoted_amount = quote_details[0]["amount"]
# 					quoted_date = quote_details[0]["quoted_date"]
# 					approval_type = quote_details[0]["approval_type"]
# 					approval_date = quote_details[0]["approval_date"]
# 					quote_name = quote_details[0]["quote_name"]
# 				total_amount = quoted_amount    # taxes will be included later!
# 				# Add the material row with the appropriate quoted amount
# 				row.append({
# 					"job_order": jo.name,
# 					"posting_date": jo.posting_date,
# 					"sales_person": jo.sales_rep,
# 					"company": jo.company,
# 					"branch": jo.branch,
# 					"mfg": material.mfg,
# 					"model_no": frappe.db.get_value("Item Model", material.model_no, "model"),
# 					"item_name": material.item_name,
# 					"quantity": material.quantity,
# 					"customer": jo.customer,
# 					"customer_reference": jo.customer_reference_number,
# 					"quoted_date": quoted_date,
# 					"approval_type": approval_type,
# 					"purchase_order": jo.po_no,
# 					"quotation": quote_name,
# 					"quoted_amount": quoted_amount,
# 					"delivery_note": jo.dn_no,
# 					"delivery_date": jo.dn_date,
# 					"invoice_no": jo.invoice_no,
# 					"invoice_date": jo.invoice_date,
# 					"approval_date": approval_date,
# 					"payment_entry_reference": jo.payment_entry,
# 					"payment_date": jo.advance_paid_date,
# 					"status": jo.status,
# 					"total_amount":total_amount
# 				})
# 	else:
# 		frappe.throw(_("Invalid filters provided for date range."))

# 	return row


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
		{"label": _("Quoted Amount"), "fieldname": "quoted_amount", "fieldtype": "Currency", "width": 150},
		{"label": _("VAT Amount"), "fieldname": "vat_amount", "fieldtype": "Currency", "width": 150},
		{"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 150},
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
				"sales_person": order.sales_rep,
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
				"total_amount": quote.get("amount", 0),  # taxes can be added later
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
		SELECT type, mfg, model_no, quantity, item_name, parent as quote_name
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
		  AND qi.model_no = %s
		  AND q.workflow_state = "Approved By Customer"
		LIMIT 1
		""",
		(order_name, model_no),
		as_dict=1,
	)
	return result[0] if result else {}
