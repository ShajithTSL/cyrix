# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from cyrix.custom_py.boot import get_bootinfo as info
from cyrix.custom_py.utils import sendmail

base_url = frappe.utils.get_url()

class InvoiceRequest(Document):
	# pass
	def on_submit(self):
		if self.workflow_state == "Invoice Created":
			manager = frappe.db.get_value("Branch", self.branch,"manager")
			self.submitted_by = frappe.session.user
			frappe.db.set_value("Invoice Request",self.name,"submitted_by",frappe.session.user)

			cc = [self.sales_email, manager]
			quotations = []

			if self.invoice_list:
				quotations.extend([i.quotation for i in self.invoice_list if i.quotation])

			if self.sod_quotation:
				quotations.extend([i.quotation for i in self.sod_quotation if i.quotation])

			for quotation in quotations:
				if quotation:
					cus = frappe.get_value("Quotation",quotation,"party_name")

					msg = f"""Dear Info,<br><br>
								I hope this email finds you well.<br><br>
								The Invoice has been created as per your request for the Quotation -{quotation}.<br><br>
								Please find the attached Invoice for your reference.<a href="{base_url}/app/invoice-request/{self.name}" target="_blank">Click Here</a>"""

					subject = "Invoice Created for - %s"%(quotation)
					sendmail(self, msg, subject, sender = self.submitted_by, recipients = self.requested_by, attachments = [{"file_url": self.get("attach")}], cc = cc )
	

@frappe.whitelist()
def trigger_mail_on_invoice_request(name):
	self = frappe.get_doc("Invoice Request", name)

	sender = frappe.db.get_value("Branch", self.branch, "customer_support")

	if not sender:
		frappe.throw("Please set Customer Support Email for the branch")

	quotations = []

	if self.invoice_list:
		quotations.extend([i.quotation for i in self.invoice_list if i.quotation])

	if self.sod_quotation:
		quotations.extend([i.quotation for i in self.sod_quotation if i.quotation])

	if not quotations:
		return

	cc = [self.sales_email]

	for quotation in quotations:

		cus = frappe.get_value("Quotation", quotation, "party_name")

		message = f""" Dear Finance,<br><br>
						Quotation <b>{quotation}</b> has been approved.<br>
						Customer Name : <b>{cus}</b>.<br><br>
						Please take action to make invoice.<br><br>
						<a href="{base_url}/app/invoice-request/{self.name}" target="_blank">Click Here</a>
					"""
		recipients = info().get("finance_to").get(self.company)
		communication = None
		attachments = None
		subject=f"Invoice Request - {quotation}"

		sendmail(self, message, subject, sender, recipients, attachments, cc )

@frappe.whitelist()
def get_quotation_details(quotation,type):
	if type == "Job Order":
		quote_details = frappe.db.sql(""" select  `tabQuotation Item`.job_order_data 
				from `tabQuotation` left join `tabQuotation Item` on `tabQuotation Item`.parent = `tabQuotation`.name
				where `tabQuotation`.name = '%s' """ %(quotation),as_dict = 1)
	else:
		quote_details = frappe.db.sql(""" select  distinct `tabQuotation Item`.supply_order_data 
				from `tabQuotation` left join `tabQuotation Item` on `tabQuotation Item`.parent = `tabQuotation`.name
				where `tabQuotation`.name = '%s' """ %(quotation),as_dict = 1)
	
	return quote_details