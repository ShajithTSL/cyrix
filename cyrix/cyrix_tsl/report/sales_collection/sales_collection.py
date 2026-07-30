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
		{"fieldname": "journal_entry", "label": _("Journal Entry"), "fieldtype": "Link", "options": "Journal Entry", "width": 200},
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

	def build_journal_entry_query():
		"""Query for Journal Entry data linked to Sales Invoices"""
		sales_person_filter = ""
		if sales_person:
			sales_person_filter = f" AND jea.custom_sales_person = '{sales_person}'"

		cost_center_filter = ""
		if cost_center:
			cost_center_filter = f" AND jea.cost_center = '{cost_center}'"

		return f"""
			SELECT
				jea.reference_name AS sales_invoice,
				si.customer AS customer,
				'' AS reference,
				NULL AS delivered_date,
				je.posting_date AS payment_entry_date,
				'' AS payment_entry_name,
				je.name AS journal_entry,
				SUM(jea.credit_in_account_currency) AS amount,
				jea.custom_sales_person AS sales_person,
				jea.cost_center AS department,
				'Journal Entry' AS source_type,
				'' AS journal_entry_account_name,
				'' AS accounts,
				'' AS dummy_column
			FROM `tabJournal Entry` je
			JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
			JOIN `tabSales Invoice` si ON si.name = jea.reference_name
			WHERE
				je.docstatus = 1
				AND jea.reference_type = 'Sales Invoice'
				AND jea.reference_name IS NOT NULL
				AND jea.reference_name != ''
				AND je.posting_date BETWEEN %(from_date)s AND %(to_date)s
				AND si.company = %(company)s
				AND jea.credit_in_account_currency > 0
				{cost_center_filter}
				{sales_person_filter}
			GROUP BY
				jea.reference_name,
				je.name,
				jea.custom_sales_person,
				jea.cost_center
		"""

	def build_direct_journal_entry_query():
		"""Query for Journal Entry credit lines against a Customer that are
		NOT linked to a Sales Invoice (reference_type != 'Sales Invoice',
		or reference_name is blank). These are the equivalent of the
		'Direct Payment' rows, but posted via Journal Entry instead of a
		Payment Entry."""
		sales_person_filter = ""
		if sales_person:
			sales_person_filter = f" AND jea.custom_sales_person = '{sales_person}'"

		cost_center_filter = ""
		if cost_center:
			cost_center_filter = f" AND jea.cost_center = '{cost_center}'"

		return f"""
			SELECT
				'' AS sales_invoice,
				jea.party AS customer,
				'' AS reference,
				NULL AS delivered_date,
				je.posting_date AS payment_entry_date,
				'' AS payment_entry_name,
				je.name AS journal_entry,
				SUM(jea.credit_in_account_currency) AS amount,
				jea.custom_sales_person AS sales_person,
				jea.cost_center AS department,
				'Journal Entry' AS source_type,
				'' AS journal_entry_account_name,
				'' AS accounts,
				'' AS dummy_column
			FROM `tabJournal Entry` je
			JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
			WHERE
				je.docstatus = 1
				AND jea.party_type = 'Customer'
				AND jea.party IS NOT NULL
				AND jea.party != ''
				AND je.posting_date BETWEEN %(from_date)s AND %(to_date)s
				AND je.company = %(company)s
				AND jea.credit_in_account_currency > 0
				AND (
					jea.reference_type IS NULL
					OR jea.reference_type != 'Sales Invoice'
					OR jea.reference_name IS NULL
					OR jea.reference_name = ''
				)
				{cost_center_filter}
				{sales_person_filter}
			GROUP BY
				je.name,
				jea.party,
				jea.custom_sales_person,
				jea.cost_center
		"""

	def build_query(reference_field, join_table, alias, delivered_field):
		return f"""
			SELECT
				si.name AS sales_invoice,
				si.customer AS customer,
				{reference_field} AS reference,
				{delivered_field} AS delivered_date,
				pe.posting_date AS payment_entry_date,
				pe.name AS payment_entry_name,
				'' AS journal_entry,
				(
					SELECT SUM(per2.allocated_amount)
					FROM `tabPayment Entry Reference` per2
					JOIN `tabPayment Entry` pe2 ON pe2.name = per2.parent
					WHERE per2.reference_name = si.name AND pe2.docstatus = 1
					AND pe2.posting_date BETWEEN %(from_date)s AND %(to_date)s
				) AS amount,
				si.sales_person AS sales_person,
				sii.cost_center AS department,
				'Payment Entry' AS source_type,
				'' AS journal_entry_account_name,
				'' AS accounts,
				'' AS dummy_column
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
				si.name AS sales_invoice,
				si.customer AS customer,
				'' AS reference,
				NULL AS delivered_date,
				pe.posting_date AS payment_entry_date,
				pe.name AS payment_entry_name,
				'' AS journal_entry,
				(
					SELECT SUM(per2.allocated_amount)
					FROM `tabPayment Entry Reference` per2
					JOIN `tabPayment Entry` pe2 ON pe2.name = per2.parent
					WHERE per2.reference_name = si.name AND pe2.docstatus = 1
					AND pe2.posting_date BETWEEN %(from_date)s AND %(to_date)s
				) AS amount,
				si.sales_person AS sales_person,
				sii.cost_center AS department,
				'Payment Entry' AS source_type,
				'' AS journal_entry_account_name,
				'' AS accounts,
				'' AS dummy_column
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
				'' AS sales_invoice,
				pe.party AS customer,
				'' AS reference,
				NULL AS delivered_date,
				pe.posting_date AS payment_entry_date,
				pe.name AS payment_entry_name,
				'' AS journal_entry,
				pe.paid_amount AS amount,
				st.sales_person AS sales_person,
				'' AS department,
				'Direct Payment' AS source_type,
				'' AS journal_entry_account_name,
				'' AS accounts,
				'' AS dummy_column
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
		queries.append(build_direct_customer_payment_query())
		queries.append(build_journal_entry_query())
		queries.append(build_direct_journal_entry_query())
	elif entry_type == "Supply":
		queries.append(build_query("sii.supply_order_data", "`tabSupply Order Data`", "so", "so.delivery"))
		queries.append(build_unlinked_query())
		queries.append(build_direct_customer_payment_query())
		queries.append(build_journal_entry_query())
		queries.append(build_direct_journal_entry_query())
	else:
		queries.append(build_query("sii.job_order_data", "`tabJob Order Data`", "wo", "wo.delivery"))
		queries.append(build_query("sii.supply_order_data", "`tabSupply Order Data`", "so", "so.delivery"))
		queries.append(build_unlinked_query())
		queries.append(build_direct_customer_payment_query())
		queries.append(build_journal_entry_query())
		queries.append(build_direct_journal_entry_query())

	query = " UNION ALL ".join(queries)

	raw_data = frappe.db.sql(query, {
		'from_date': from_date,
		'to_date': to_date,
		'sales_person': sales_person,
		'cost_center': cost_center,
		'company': company
	}, as_dict=True)

	# Process the data
	final_data = []
	processed_groups = set()

	for row in raw_data:
		if row['source_type'] == 'Journal Entry':
			# Handle Journal Entry rows
			if row['sales_invoice']:
				# Journal Entry linked to Sales Invoice
				key = f"JE_{row['sales_invoice']}_{row['journal_entry']}"
				if key not in processed_groups:
					processed_groups.add(key)
					final_data.append({
						"reference": "",
						"sales_invoice": row['sales_invoice'],
						"customer": row['customer'],
						"delivered_date": "",
						"payment_entry_date": row['payment_entry_date'],
						"payment_entry": "",
						"journal_entry": row['journal_entry'],
						"amount": row['amount'],
						"sales_person": row['sales_person'] or "",
						"department": row['department'] or "",
						"indent": 0,
						"is_group": 0
					})
			else:
				# Journal Entry NOT linked to any Sales Invoice (direct
				# customer receipt posted via Journal Entry)
				key = f"JE_DIRECT_{row['journal_entry']}_{row['customer']}"
				if key not in processed_groups:
					processed_groups.add(key)
					final_data.append({
						"reference": "",
						"sales_invoice": "",
						"customer": row['customer'],
						"delivered_date": "",
						"payment_entry_date": row['payment_entry_date'],
						"payment_entry": "",
						"journal_entry": row['journal_entry'],
						"amount": row['amount'],
						"sales_person": row['sales_person'] or "",
						"department": row['department'] or "",
						"indent": 0,
						"is_group": 0
					})
		else:
			# Handle Payment Entry rows
			if row['sales_invoice'] and row['source_type'] != 'Direct Payment':
				key = f"PI_{row['sales_invoice']}"
				if key not in processed_groups:
					processed_groups.add(key)

					# Check if there are child rows with references
					child_rows = [r for r in raw_data if r.get('reference') and r.get('sales_invoice') == row['sales_invoice'] and r['source_type'] != 'Journal Entry']

					if child_rows:
						# Parent row
						final_data.append({
							"reference": "",
							"sales_invoice": row['sales_invoice'],
							"customer": row['customer'],
							"delivered_date": "",
							"payment_entry_date": row['payment_entry_date'],
							"payment_entry": row['payment_entry_name'],
							"journal_entry": "",
							"amount": row['amount'],
							"sales_person": row['sales_person'],
							"department": "",
							"indent": 0,
							"is_group": 1
						})

						# Child rows
						for child in child_rows:
							if child.get('reference'):
								final_data.append({
									"reference": child['reference'],
									"sales_invoice": "",
									"customer": "",
									"delivered_date": child['delivered_date'],
									"payment_entry_date": "",
									"payment_entry": "",
									"journal_entry": "",
									"amount": "",
									"sales_person": "",
									"department": child['department'],
									"indent": 1
								})
					else:
						# Single row without children
						final_data.append({
							"reference": "",
							"sales_invoice": row['sales_invoice'],
							"customer": row['customer'],
							"delivered_date": "",
							"payment_entry_date": row['payment_entry_date'],
							"payment_entry": row['payment_entry_name'],
							"journal_entry": "",
							"amount": row['amount'],
							"sales_person": row['sales_person'],
							"department": "",
							"indent": 0,
							"is_group": 0
						})
			elif row['source_type'] == 'Direct Payment':
				# Direct customer payment
				key = f"DP_{row['payment_entry_name']}"
				if key not in processed_groups:
					processed_groups.add(key)
					final_data.append({
						"reference": "",
						"sales_invoice": "",
						"customer": row['customer'],
						"delivered_date": "",
						"payment_entry_date": row['payment_entry_date'],
						"payment_entry": row['payment_entry_name'],
						"journal_entry": "",
						"amount": row['amount'],
						"sales_person": row['sales_person'],
						"department": "",
						"indent": 0,
						"is_group": 1
					})

	return final_data