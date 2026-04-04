# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from cyrix.custom_py.boot import get_bootinfo as info
from cyrix.custom_py.utils import sendmail

base_url = frappe.utils.get_url()

class InvoiceCancellation(Document):
	def on_submit(self):
		frappe.db.set_value("Invoice Cancellation",self.name,"submitted_by",frappe.session.user)

@frappe.whitelist()
def trigger_mail_on_invoice_cancellation(name):
	self = frappe.get_doc("Invoice Cancellation", name)

	sender = frappe.db.get_value("Branch", self.branch, "customer_support")

	if not sender:
		frappe.throw("Please set Customer Support Email for the branch")

	reference_lists = []

	if self.cancellation_list:
		reference_lists.extend([i.invoice_no for i in self.cancellation_list if i.invoice_no])

	if not reference_lists:
		return

	cc = [self.sales_email]

	for invoice_no in reference_lists:

		cus = frappe.get_value("Sales Invoice", invoice_no, "customer")

		message = f""" Dear Finance,<br><br>
						Sales Invoice <b>{invoice_no}</b> has been Requested for cancellation.<br>
						Customer Name : <b>{cus}</b>.<br><br>
						Please take action on cancellation.<br><br>
						<a href="{base_url}/app/invoice-cancellation/{self.name}" target="_blank">Click Here</a>
					"""
		recipients = info().get("finance_to").get(self.company)
		communication = None
		attachments = None
		subject=f"Invoice Cancellation - {invoice_no}"

		sendmail(self, message, subject, sender, recipients, attachments, cc )


@frappe.whitelist()
def invoice_cancellation_si(sales_invoice):
	si_details = frappe.db.sql(
		""" select  
				`tabSales Invoice Item`.job_order_data,
				`tabSales Invoice Item`.supply_order_data
			from `tabSales Invoice`
			left join `tabSales Invoice Item` on `tabSales Invoice Item`.parent = `tabSales Invoice`.name
			where `tabSales Invoice`.name = '%s'  """ %(sales_invoice),as_dict = 1)
	
	return si_details