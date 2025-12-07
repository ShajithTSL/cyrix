# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InvoiceCancellation(Document):
	pass

@frappe.whitelist()
def invoice_cancellation(job_order_data):
	si_details = frappe.db.sql(""" select  `tabSales Invoice`.name from `tabSales Invoice` 
		left join `tabSales Invoice Item` on `tabSales Invoice Item`.parent = `tabSales Invoice`.name
		where `tabSales Invoice Item`.job_order_data = '%s' and  `tabSales Invoice`.is_return != 1 and `tabSales Invoice`.docstatus = 1 """ %(job_order_data),as_dict = 1)
	return si_details


@frappe.whitelist()
def invoice_cancellation_si(sales_invoice):
	# sales_invoice = "INV-R25-00005"
	si_details = frappe.db.sql(""" select  `tabSales Invoice Item`.job_order_data
		left join `tabSales Invoice Item` on `tabSales Invoice Item`.parent = `tabSales Invoice`.name
		where `tabSales Invoice`.name = '%s'
		""" %(sales_invoice),as_dict = 1)
	return si_details