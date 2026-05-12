# Copyright (c) 2025, Tsl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from collections import defaultdict

def execute(filters=None):
	columns = get_columns(filters or {})
	data = get_data(filters or {})
	return columns, data

def get_columns(filters):
	t = filters.get("type")
	if t == "Repair":
		reference_label = _("Job Order Data")
	elif t == "Supply":
		reference_label = _("Supply Order Data")
	else:
		reference_label = _("Reference")

	return [
		{"fieldname": "sales_invoice", "label": _("Sales Invoice"), "fieldtype": "Link", "options": "Sales Invoice", "width": 200},
		{"fieldname": "customer", "label": _("Customer"), "fieldtype": "Link", "options": "Customer", "width": 400},
		{"fieldname": "reference", "label": reference_label, "fieldtype": "Data", "width": 200},
		{"fieldname": "delivered_date", "label": _("RSC Date"), "fieldtype": "Date", "width": 200},
		{"fieldname": "payment_entry_date", "label": _("Payment Entry Date"), "fieldtype": "Date", "width": 200},
		{"fieldname": "payment_entry", "label": _("Payment Entry"), "fieldtype": "Link", "options": "Payment Entry", "width": 200},
		{"fieldname": "amount", "label": _("Amount"), "fieldtype": "Currency", "width": 120},
		{"fieldname": "sales_person", "label": _("Sales Person"), "fieldtype": "Link", "options": "Sales Person", "width": 200},
		{"fieldname": "department", "label": _("Department"), "fieldtype": "Link", "options": "Cost Center", "width": 200},
	]

def get_data(filters):
	from_date = filters.get('from_date')
	to_date = filters.get('to_date')
	company = filters.get('company')
	cost_center = filters.get('cost_center')
	sales_person = filters.get('sales_person')
	entry_type = filters.get('type')

	def extra_filters():
		extra = ""
		if sales_person:
			extra += " AND si.sales_person = %(sales_person)s"
		if cost_center:
			extra += " AND sii.cost_center = %(cost_center)s"
		return extra

	def build_query(reference_field, join_table, alias, delivered_field):
		return f"""
			SELECT
				{reference_field} AS reference,
				si.name AS sales_invoice,
				si.customer AS customer,
				{delivered_field} AS delivered_date,
				pe.posting_date AS payment_entry_date,
				pe.name AS payment_entry_name,
				(
					SELECT SUM(per2.allocated_amount)
					FROM `tabPayment Entry Reference` per2
					JOIN `tabPayment Entry` pe2 ON pe2.name = per2.parent
					WHERE per2.reference_name = si.name AND pe2.docstatus = 1
					AND pe2.posting_date BETWEEN %(from_date)s AND %(to_date)s
				) AS amount,
				si.sales_person AS sales_person,
				sii.cost_center AS department
			FROM `tabPayment Entry` pe
			JOIN `tabPayment Entry Reference` per ON pe.name = per.parent
			JOIN `tabSales Invoice` si ON si.name = per.reference_name
			LEFT JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
			LEFT JOIN {join_table} {alias} ON {alias}.name = {reference_field}
			WHERE
				pe.payment_type = 'Receive' and pe.docstatus = 1
				AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
				AND si.company = %(company)s
				AND {reference_field} IS NOT NULL
				AND {reference_field} != ''
				{extra_filters()}
		"""

	def build_unlinked_query():
		return f"""
			SELECT
				'' AS reference,
				si.name AS sales_invoice,
				si.customer AS customer,
				NULL AS delivered_date,
				pe.posting_date AS payment_entry_date,
				pe.name AS payment_entry_name,
				(
					SELECT SUM(per2.allocated_amount)
					FROM `tabPayment Entry Reference` per2
					JOIN `tabPayment Entry` pe2 ON pe2.name = per2.parent
					WHERE per2.reference_name = si.name AND pe2.docstatus = 1
					AND pe2.posting_date BETWEEN %(from_date)s AND %(to_date)s
				) AS amount,
				si.sales_person AS sales_person,
				sii.cost_center AS department
			FROM `tabPayment Entry` pe
			JOIN `tabPayment Entry Reference` per ON pe.name = per.parent
			JOIN `tabSales Invoice` si ON si.name = per.reference_name
			LEFT JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
			WHERE
				pe.payment_type = 'Receive'
				AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
				AND si.company = %(company)s
				AND (sii.job_order_data IS NULL OR sii.job_order_data = '')
				AND (sii.supply_order_data IS NULL OR sii.supply_order_data = '')
				{extra_filters()}
		"""

	def build_direct_customer_payment_query():
		"""Query for payment entries directly linked to customers (no sales invoice reference)"""
		sales_person_filter = ""
		if sales_person:
			sales_person_filter = f" AND st.sales_person = '{sales_person}'"
		
		cost_center_filter = ""
		if cost_center:
			cost_center_filter = f" AND c.custom_cost_center = '{cost_center}'"
		
		return f"""
			SELECT
				'' AS reference,
				'' AS sales_invoice,
				pe.party AS customer,
				NULL AS delivered_date,
				pe.posting_date AS payment_entry_date,
				pe.name AS payment_entry_name,
				pe.paid_amount AS amount,
				st.sales_person AS sales_person,
				'' AS department
			FROM `tabPayment Entry` pe
			LEFT JOIN `tabCustomer` c ON c.name = pe.party
			LEFT JOIN `tabSales Team` st ON st.parent = c.name AND st.parenttype = 'Customer'
			WHERE
				pe.payment_type = 'Receive'
				AND pe.docstatus = 1
				AND pe.party_type = 'Customer'
				AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
				AND pe.company = %(company)s
				AND pe.party IS NOT NULL
				AND pe.party != ''
				AND NOT EXISTS (
					SELECT 1 
					FROM `tabPayment Entry Reference` per 
					WHERE per.parent = pe.name
				)
				{sales_person_filter}
				{cost_center_filter}
			GROUP BY pe.name
		"""

	queries = []

	if entry_type == "Repair":
		queries.append(build_query("sii.job_order_data", "`tabJob Order Data`", "wo", "wo.delivery"))
		queries.append(build_unlinked_query())
		# Also include direct customer payments for Repair type
		queries.append(build_direct_customer_payment_query())
	elif entry_type == "Supply":
		queries.append(build_query("sii.supply_order_data", "`tabSupply Order Data`", "so", "so.delivery"))
		queries.append(build_unlinked_query())
		# Also include direct customer payments for Supply type
		queries.append(build_direct_customer_payment_query())
	else:
		# For other types, include all queries
		queries.append(build_query("sii.job_order_data", "`tabJob Order Data`", "wo", "wo.delivery"))
		queries.append(build_query("sii.supply_order_data", "`tabSupply Order Data`", "so", "so.delivery"))
		queries.append(build_unlinked_query())
		# Include direct customer payments
		queries.append(build_direct_customer_payment_query())

	query = " UNION ALL ".join(queries)

	raw_data = frappe.db.sql(query, {
		'from_date': from_date,
		'to_date': to_date,
		'sales_person': sales_person,
		'cost_center': cost_center,
		'company': company
	}, as_dict=True)

	grouped = defaultdict(list)
	amounts = defaultdict(float)

	for row in raw_data:
		if row['sales_invoice']:  # Group by sales invoice if exists
			grouped[row['sales_invoice']].append(row)
			amounts[row['sales_invoice']] = row['amount'] or 0
		elif row['payment_entry_name'] and not row['sales_invoice']:  # For direct customer payments, group by payment entry
			grouped[row['payment_entry_name']].append(row)
			amounts[row['payment_entry_name']] = row['amount'] or 0

	final_data = []

	for key, rows in grouped.items():
		parent_row = rows[0]
		
		# Determine if this is a direct customer payment or invoice-based
		if parent_row['sales_invoice']:
			# Invoice-based grouping
			final_data.append({
				"reference": "",
				"sales_invoice": key,
				"customer": parent_row['customer'],
				"delivered_date": "",
				"payment_entry_date": parent_row['payment_entry_date'],
				"payment_entry": parent_row['payment_entry_name'],
				"amount": amounts[key],
				"sales_person": parent_row['sales_person'],
				"department": "",
				"indent": 0,
				"is_group": 1
			})
			
			for child in rows:
				if child['reference']:  # Only add child rows if they have reference
					final_data.append({
						"reference": child['reference'],
						"sales_invoice": "",
						"customer": "",
						"delivered_date": child['delivered_date'],
						"payment_entry_date": child['payment_entry_date'],
						"payment_entry": child['payment_entry_name'],
						"amount": "",
						"sales_person": "",
						"department": child['department'],
						"indent": 1
					})
		else:
			# Direct customer payment (no sales invoice)
			final_data.append({
				"reference": "",
				"sales_invoice": "",
				"customer": parent_row['customer'],
				"delivered_date": "",
				"payment_entry_date": parent_row['payment_entry_date'],
				"payment_entry": parent_row['payment_entry_name'],
				"amount": amounts[key],
				"sales_person": parent_row['sales_person'],
				"department": "",
				"indent": 0,
				"is_group": 1
			})

	return final_data