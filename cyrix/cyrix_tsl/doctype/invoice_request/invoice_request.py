# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InvoiceRequest(Document):
	pass

@frappe.whitelist()
def get_quotation_details(quotation,type):
	if type == "Job Order":
		quote_details = frappe.db.sql(""" select  `tabQuotation Item`.job_order_data 
				from `tabQuotation` left join `tabQuotation Item` on `tabQuotation Item`.parent = `tabQuotation`.name
				where `tabQuotation`.name = '%s' """ %(quotation),as_dict = 1)
	else:
		quote_details = frappe.db.sql(""" select  `tabQuotation Item`.supply_order_data 
				from `tabQuotation` left join `tabQuotation Item` on `tabQuotation Item`.parent = `tabQuotation`.name
				where `tabQuotation`.name = '%s' """ %(quotation),as_dict = 1)
	
	return quote_details