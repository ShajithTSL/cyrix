# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

# import frappe
# from frappe import _
# from datetime import datetime, timedelta
# from erpnext.setup.utils import get_exchange_rate

# status_list = [
# 	("RS-Repaired and Shipped", "rs_date"),
# 	("RNR-Return Not Repaired", "rnr_date"),
# 	("RNF-Return No Fault", "rnf_date"),
# 	("RNP-Return No Parts", "rnp_date")
# ]

# def execute(filters=None):
# 	columns = get_columns(filters)
# 	data = get_data(filters) 
# 	return columns, data

# def get_columns(filters):
# 	# Define columns you want to show in your report, including material columns
# 	columns = [
# 		{
# 			"label": _("Job Order"),
# 			"fieldname": "job_order",
# 			"fieldtype": "Link",
# 			"options": "Job Order Data",
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
# 		# {
# 		# 	"label": _(" Customer Reference"),
# 		# 	"fieldname": "customer_reference",
# 		# 	"fieldtype": "Data",
# 		# 	"width": 200
# 		# },
# 		# Contact Details columns
# 		{
# 			"label": _("Contact Person"),
# 			"fieldname": "contact_name",
# 			"fieldtype": "Data",
# 			"width": 200
# 		},
# 		{
# 			"label": _("Contact Email"),
# 			"fieldname": "email",
# 			"fieldtype": "Data",
# 			"width": 200
# 		},
# 		{
# 			"label": _("Contact Number"),
# 			"fieldname": "phone_number",
# 			"fieldtype": "Data",
# 			"width": 150
# 		},
# 		{
# 			"label": _("Technician"),
# 			"fieldname": "technician",
# 			"fieldtype": "Data",
# 			"width": 150
# 		},
# 		{
# 			"label": _("Quoted Price"),
# 			"fieldname": "quoted_price",
# 			"fieldtype": "Currency",
# 			"width": 150
# 		},
# 		{
# 			"label": _("Quoted Date"),
# 			"fieldname": "quoted_date",
# 			"fieldtype": "Date",
# 			"width": 150
# 		},
# 		{
# 			"label": _("Approval Type"),
# 			"fieldname": "approval_type",
# 			"fieldtype": "Data",
# 			"width": 150
# 		},
# 		{
# 			"label": _("Purchase Order"),
# 			"fieldname": "purchase_order",
# 			"fieldtype": "Data",
# 			"width": 140
# 		},
# 		{
# 			"label": _("Payment Reference"),
# 			"fieldname": "payment_reference",
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
# 			"label": _("Return Date"),
# 			"fieldname": "return_date",
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
# 			"label": _("RS Date"),
# 			"fieldname": "rs_date",
# 			"fieldtype": "Date",
# 			"width": 150
# 		},
# 		{
# 			"label": _("RNR Date"),
# 			"fieldname": "rnr_date",
# 			"fieldtype": "Date",
# 			"width": 150
# 		},
# 		{
# 			"label": _("RNF Date"),
# 			"fieldname": "rnf_date",
# 			"fieldtype": "Date",
# 			"width": 150
# 		},
# 		{
# 			"label": _("RNP Date"),
# 			"fieldname": "rnp_date",
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
# 			"label": _("Cost"),
# 			"fieldname": "actual_cost",
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
# 			"label": _("NER"),
# 			"fieldname": "ner",
# 			"fieldtype": "Data",
# 			"width": 150
# 		},
# 		{
# 			"label": _("NER Date"),
# 			"fieldname": "ner_date",
# 			"fieldtype": "Date",
# 			"width": 150
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
# 		# First query to get Job Order Data
# 		job_order_data = frappe.get_all(
# 			"Job Order Data",
# 			filters={
# 				"posting_date": ["between", (filters["from_date"], filters["to_date"])],
# 				"branch": filters.get('branch')
# 			},
# 			fields=["*"]
# 		)

# 		for jo in job_order_data:
# 			quoted_amount = 0
# 			quote_name = ''
# 			quoted_date = ''
# 			approval_type = ''
# 			approval_date = ''
# 			quote_details = frappe.db.sql(''' select `tabQuotation`.company as com,
# 				`tabQuotation`.taxes_and_charges as tax,
# 				`tabQuotation`.name as quote_name,
# 				`tabQuotation Item`.rate as up,
# 				`tabQuotation Item`.net_amount as amount,
# 				`tabQuotation`.transaction_date as transaction_date,
# 				`tabQuotation`.approval_date as approval_date,
# 				`tabQuotation`.type_of_approval as approval_type
# 			from `tabQuotation` 
# 				left join `tabQuotation Item` on  `tabQuotation`.name = `tabQuotation Item`.parent
# 			where  `tabQuotation`.workflow_state in ("Approved By Customer") 
# 				and `tabQuotation Item`.job_order_data = %s ''',jo.name,as_dict=1)
# 			if quote_details:
# 				quote_details = quote_details[0]
# 				quoted_amount = quote_details["amount"]
# 				quote_name = quote_details["quote_name"]
# 				quoted_date = quote_details["transaction_date"]
# 				approval_type = quote_details["approval_type"]
# 				approval_date = quote_details["approval_date"]

# 			status_dates = {}

# 			for status, key in status_list:
# 				result = frappe.db.sql("""
# 					SELECT DATE(sdd.date) AS date
# 					FROM `tabJob Order Data` wod
# 					LEFT JOIN `tabStatus Duration Details` sdd ON wod.name = sdd.parent
# 					WHERE sdd.status = %s AND wod.name = %s
# 					ORDER BY sdd.date ASC LIMIT 1
# 				""", (status, jo.name), as_dict=True)

# 				status_dates[key] = result[0]["date"] if result else ""

# 			# Access the individual dates if needed
# 			rs_date = status_dates["rs_date"]
# 			rnr_date = status_dates["rnr_date"]
# 			rnf_date = status_dates["rnf_date"]
# 			rnp_date = status_dates["rnp_date"]


# 			actual_cost = 0
# 			cost = frappe.db.sql(""" select  sum(`tabPart Sheet Item`.total) as cost
# 									from `tabEvaluation Report` 
# 									left join `tabPart Sheet Item` on `tabEvaluation Report`.name = `tabPart Sheet Item`.parent
# 									where  `tabEvaluation Report`.job_order_data = '%s' """ %(jo.name) ,as_dict=1)
# 			if cost:
# 				if cost[0]["cost"]:
# 					actual_cost = cost[0]["cost"]
				
# 			total_amount = quoted_amount    # taxes will be included later!

# 			technicians = frappe.db.sql('''
# 				SELECT t.technician AS technician_name
# 				FROM `tabTechnician List` tl
# 				JOIN `tabTechnician ID` t ON tl.technician = t.name
# 				WHERE tl.parenttype = 'Job Order Data' AND tl.parent = %s
# 			''', jo.name, as_dict=True)

# 			# Concatenate the technician names into a single comma-separated string
# 			technician_names = ", ".join([tech.technician_name for tech in technicians])

# 			# Fetch materials related to the current job order using a second query
# 			material_list_data = frappe.db.sql('''
# 				SELECT type, mfg, model_no, quantity, item_name
# 				FROM `tabMaterial List`
# 				WHERE parent = %s
# 			''', jo.name, as_dict=1)
# 			# Fetch contact details for the customer
# 			contact = frappe.db.sql('''
# 				SELECT name1, email_id, phone_number
# 				FROM `tabContact Details`
# 				WHERE parent = %s AND parenttype = "Customer"
# 			''', jo.customer, as_dict=1)

# 			# Initialize contact variables
# 			contact_name = ''
# 			email = ''
# 			phone_number = ''

# 			# If contact details exist, assign the values
# 			if contact:
# 				contact_name = contact[0]['name1']
# 				email = contact[0]['email_id']
# 				phone_number = contact[0]['phone_number']

# 			# For each material item, combine it with the job order data
# 			for material in material_list_data:
# 				row.append({
# 					"job_order": jo.name,
# 					"posting_date": jo.posting_date,
# 					"sales_person": jo.sales_rep,
# 					"company": jo.company,
# 					"branch": jo.branch,
# 					"mfg": material.mfg,
# 					"model_no": frappe.db.get_value("Item Model",material.model_no,"model"),
# 					"item_name": material.item_name,
# 					"quantity": material.quantity,
# 					"customer": jo.customer,
# 					# "customer_reference": jo.cus,
# 					"contact_name": contact_name,
# 					"email": email,
# 					"phone_number": phone_number,
# 					"technician": technician_names,
# 					"quoted_date":quoted_date,
# 					"approval_type":approval_type,
# 					"purchase_order":jo.po_no,
# 					"quotation": quote_name,
# 					"quoted_amount": quoted_amount,
# 					"actual_cost":actual_cost,
# 					"delivery_note": jo.dn_no,
# 					"delivery_date": jo.dn_date,
# 					"invoice_no": jo.invoice_no,
# 					"invoice_date": jo.invoice_date,
# 					"return_date": jo.returned_date,
# 					"approval_date": approval_date,
# 					"rs_date": rs_date,
# 					"rnr_date": rnr_date,
# 					"rnf_date": rnf_date,
# 					"rnp_date": rnp_date,
# 					"status": jo.status,
# 					"payment_reference": jo.payment_entry,
# 					"payment_date": jo.advance_paid_date,
# 					"total_amount":total_amount
# 				})

# 	else:
# 		frappe.throw(_("Invalid filters provided for date range."))

	
# 	return row


import frappe
from frappe import _
from datetime import datetime, timedelta

status_list = [
	("RS-Repaired and Shipped", "rs_date"),
	("RNR-Return Not Repaired", "rnr_date"),
	("RNF-Return No Fault", "rnf_date"),
	("RNP-Return No Parts", "rnp_date")
]

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		{"fieldname": "job_order", "label": _("Job Order"), "fieldtype": "Link", "options": "Job Order Data", "width": 140},
		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 150},
		{"fieldname": "sales_person", "label": _("Sales Person"), "fieldtype": "Link", "options": "Sales Person", "width": 130},
		{"fieldname": "company", "label": _("Company"), "fieldtype": "Link", "options": "Company", "width": 280},
		{"fieldname": "branch", "label": _("Branch"), "fieldtype": "Link", "options": "Branch", "width": 100},
		{"fieldname": "mfg", "label": _("MFG"), "fieldtype": "Data", "width": 100},
		{"fieldname": "model_no", "label": _("Model No"), "fieldtype": "Data", "width": 140},
		{"fieldname": "item_name", "label": _("Item Name"), "fieldtype": "Data", "width": 180},
		{"fieldname": "quantity", "label": _("Quantity"), "fieldtype": "Float", "width": 100},
		{"fieldname": "customer", "label": _("Customer"), "fieldtype": "Link", "options": "Customer", "width": 100},
		{"fieldname": "contact_name", "label": _("Contact Person"), "fieldtype": "Data", "width": 200},
		{"fieldname": "email", "label": _("Contact Email"), "fieldtype": "Data", "width": 200},
		{"fieldname": "phone_number", "label": _("Contact Number"), "fieldtype": "Data", "width": 150},
		{"fieldname": "technician", "label": _("Technician"), "fieldtype": "Data", "width": 150},
		{"fieldname": "quoted_price", "label": _("Quoted Price"), "fieldtype": "Currency", "width": 150},
		{"fieldname": "quoted_date", "label": _("Quoted Date"), "fieldtype": "Date", "width": 150},
		{"fieldname": "approval_type", "label": _("Approval Type"), "fieldtype": "Data", "width": 150},
		{"fieldname": "purchase_order", "label": _("Purchase Order"), "fieldtype": "Data", "width": 140},
		{"fieldname": "payment_reference", "label": _("Payment Reference"), "fieldtype": "Data", "width": 170},
		{"fieldname": "payment_date", "label": _("Payment Date"), "fieldtype": "Date", "width": 150},
		{"fieldname": "delivery_note", "label": _("Delivery Note"), "fieldtype": "Link", "options": "Delivery Note", "width": 160},
		{"fieldname": "delivery_date", "label": _("Delivery Date"), "fieldtype": "Date", "width": 150},
		{"fieldname": "invoice_no", "label": _("Invoice No"), "fieldtype": "Link", "options": "Sales Invoice", "width": 160},
		{"fieldname": "invoice_date", "label": _("Invoice Date"), "fieldtype": "Date", "width": 150},
		{"fieldname": "return_date", "label": _("Return Date"), "fieldtype": "Date", "width": 150},
		{"fieldname": "approval_date", "label": _("Approval Date"), "fieldtype": "Date", "width": 150},
		{"fieldname": "rs_date", "label": _("RS Date"), "fieldtype": "Date", "width": 150},
		{"fieldname": "rnr_date", "label": _("RNR Date"), "fieldtype": "Date", "width": 150},
		{"fieldname": "rnf_date", "label": _("RNF Date"), "fieldtype": "Date", "width": 150},
		{"fieldname": "rnp_date", "label": _("RNP Date"), "fieldtype": "Date", "width": 150},
		{"fieldname": "quoted_amount", "label": _("Quoted Amount"), "fieldtype": "Currency", "width": 150},
		{"fieldname": "actual_cost", "label": _("Cost"), "fieldtype": "Currency", "width": 150},
		{"fieldname": "vat_amount", "label": _("VAT Amount"), "fieldtype": "Currency", "width": 150},
		{"fieldname": "total_amount", "label": _("Total Amount"), "fieldtype": "Currency", "width": 150},
		{"fieldname": "quotation", "label": _("Quotation"), "fieldtype": "Link", "options": "Quotation", "width": 100},
		{"fieldname": "ner", "label": _("NER"), "fieldtype": "Data", "width": 150},
		{"fieldname": "ner_date", "label": _("NER Date"), "fieldtype": "Date", "width": 150},
		{"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 150}
	]
	return columns


def get_data(filters):
	row = []

	if not filters or not filters.get('from_date') or not filters.get('to_date') or not filters.get('branch'):
		frappe.throw(_("Invalid filters provided for date range."))

	job_order_data = get_job_order_data(filters)
	
	for jo in job_order_data:
		quote_details = get_quote_details(jo.name)
		technician_names = get_technician_names(jo.name)
		status_dates = get_status_dates(jo.name)
		actual_cost = get_actual_cost(jo.name)
		contact_details = get_contact_details(jo.customer)
		material_list_data = get_material_list(jo.name)

		total_amount = quote_details["amount"]  # taxes will be included later
		row.extend(create_rows(jo, material_list_data, quote_details, technician_names, status_dates, actual_cost, contact_details, total_amount))

	return row

def get_job_order_data(filters):
	return frappe.get_all(
		"Job Order Data", 
		filters={
			"posting_date": ["between", (filters["from_date"], filters["to_date"])],
			"branch": filters.get('branch')
		},
		fields=["*"]
	)

def get_quote_details(job_order_name):
	quote_details = frappe.db.sql('''
		SELECT q.name as quote_name, q.transaction_date as quoted_date, q.type_of_approval as approval_type, 
			q.approval_date as approval_date, qi.net_amount as amount
		FROM `tabQuotation` q
		JOIN `tabQuotation Item` qi ON q.name = qi.parent
		WHERE qi.job_order_data = %s AND q.workflow_state = "Approved By Customer"
	''', job_order_name, as_dict=True)

	if quote_details:
		return quote_details[0]
	return {"quote_name": "", "quoted_date": "", "approval_type": "", "approval_date": "", "amount": 0}

def get_technician_names(job_order_name):
	technicians = frappe.db.sql('''
		SELECT t.technician AS technician_name
		FROM `tabTechnician List` tl
		JOIN `tabTechnician ID` t ON tl.technician = t.name
		WHERE tl.parenttype = 'Job Order Data' AND tl.parent = %s
	''', job_order_name, as_dict=True)
	return ", ".join([tech.technician_name for tech in technicians])

def get_status_dates(job_order_name):
	status_dates = {}
	for status, key in status_list:
		result = frappe.db.sql('''
			SELECT DATE(sdd.date) AS date
			FROM `tabJob Order Data` wod
			LEFT JOIN `tabStatus Duration Details` sdd ON wod.name = sdd.parent
			WHERE sdd.status = %s AND wod.name = %s
			ORDER BY sdd.date ASC LIMIT 1
		''', (status, job_order_name), as_dict=True)
		status_dates[key] = result[0]["date"] if result else ""
	return status_dates

def get_actual_cost(job_order_name):
	cost = frappe.db.sql('''
		SELECT SUM(ps.total) AS cost
		FROM `tabEvaluation Report` er
		LEFT JOIN `tabPart Sheet Item` ps ON er.name = ps.parent
		WHERE er.job_order_data = %s
	''', job_order_name, as_dict=True)
	return cost[0]["cost"] if cost else 0

def get_contact_details(customer_name):
	contact = frappe.db.sql('''
		SELECT name1, email_id, phone_number
		FROM `tabContact Details`
		WHERE parent = %s AND parenttype = "Customer"
	''', customer_name, as_dict=True)
	
	if contact:
		return contact[0]
	return {"name1": "", "email_id": "", "phone_number": ""}

def get_material_list(job_order_name):
	return frappe.db.sql('''
		SELECT type, mfg, model_no, quantity, item_name
		FROM `tabMaterial List`
		WHERE parent = %s
	''', job_order_name, as_dict=True)

def create_rows(jo, material_list_data, quote_details, technician_names, status_dates, actual_cost, contact_details, total_amount):
	rows = []
	for material in material_list_data:
		rows.append({
			"job_order": jo.name,
			"posting_date": jo.posting_date,
			"sales_person": jo.sales_rep,
			"company": jo.company,
			"branch": jo.branch,
			"mfg": material.mfg,
			"model_no": frappe.db.get_value("Item Model", material.model_no, "model"),
			"item_name": material.item_name,
			"quantity": material.quantity,
			"customer": jo.customer,
			"contact_name": contact_details["name1"],
			"email": contact_details["email_id"],
			"phone_number": contact_details["phone_number"],
			"technician": technician_names,
			"quoted_date": quote_details["quoted_date"],
			"approval_type": quote_details["approval_type"],
			"purchase_order": jo.po_no,
			"quotation": quote_details["quote_name"],
			"quoted_amount": quote_details["amount"],
			"actual_cost": actual_cost,
			"delivery_note": jo.dn_no,
			"delivery_date": jo.dn_date,
			"invoice_no": jo.invoice_no,
			"invoice_date": jo.invoice_date,
			"return_date": jo.returned_date,
			"approval_date": quote_details["approval_date"],
			"rs_date": status_dates["rs_date"],
			"rnr_date": status_dates["rnr_date"],
			"rnf_date": status_dates["rnf_date"],
			"rnp_date": status_dates["rnp_date"],
			"status": jo.status,
			"payment_reference": jo.payment_entry,
			"payment_date": jo.advance_paid_date,
			"total_amount": total_amount
		})
	return rows
