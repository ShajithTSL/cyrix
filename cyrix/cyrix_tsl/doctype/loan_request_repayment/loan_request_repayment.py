# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from cyrix.cyrix_tsl.doctype.loan_request.loan_request import update_total_amount_paid

class LoanRequestRepayment(Document):
	def make_payment_entry(self):
		if not self.salary_slip:
			pe = frappe.get_doc({
				"doctype": "Payment Entry",
				"payment_type": "Receive",
				"party_type": "Employee",
				"party": self.employee,
				"company": self.company,
				"posting_date": self.posting_date,
				"mode_of_payment": "Bank Draft",
				
				"paid_from": self.loan_account,   
				"paid_to": self.payment_account,
				
				"paid_amount": self.amount_paid,
				"received_amount": self.amount_paid,
				"reference_no": self.name,
				"reference_date": self.posting_date,
				"reference_remarks": "Repayment against loan: " + self.against_loan + "Reference: " + self.name,
			})
			pe.insert(ignore_permissions=True)
			pe.submit()
			frappe.msgprint("Payment Entry created for Repayment - <b>"+pe.name+"</b>")
			frappe.db.set_value("Loan Request Repayment", self.name, "payment_entry", pe.name, update_modified = False)

	def cancel_payment_entry(self):
		if self.payment_entry:
			pe = frappe.get_doc("Payment Entry",self.payment_entry)
			pe.cancel()
			pe.delete(ignore_permissions=1, force=1, delete_permanently=1)

	def on_submit(self):
		self.make_payment_entry()
		if self.get("repayment_details"):
			for repay in self.get("repayment_details"):
				paid_amount = frappe.db.get_value("Loan Request Repayment Schedule",repay.reference,"paid_amount") or 0
				principal_amount = frappe.db.get_value("Loan Request Repayment Schedule",repay.reference,"principal_amount") or 0
				parent = frappe.db.get_value("Loan Request Repayment Schedule",repay.reference,"parent")

				# Update schedule paid amount
				frappe.db.set_value("Loan Request Repayment Schedule",repay.reference,"paid_amount",paid_amount + repay.total_payment)
				if paid_amount + repay.total_payment == principal_amount:
					frappe.db.set_value("Loan Request Repayment Schedule",repay.reference,"is_accrued", 1)
				update_total_amount_paid(parent)

	def on_cancel(self):
		self.cancel_payment_entry()
		if self.get("repayment_details"):
			for repay in self.get("repayment_details"):
				paid_amount = frappe.db.get_value("Loan Request Repayment Schedule",repay.reference,"paid_amount") or 0
				principal_amount = frappe.db.get_value("Loan Request Repayment Schedule",repay.reference,"principal_amount") or 0
				parent = frappe.db.get_value("Loan Request Repayment Schedule",repay.reference,"parent")

				# Update schedule paid amount
				frappe.db.set_value("Loan Request Repayment Schedule",repay.reference,"paid_amount",paid_amount - repay.total_payment)
				if paid_amount + repay.total_payment == principal_amount:
					frappe.db.set_value("Loan Request Repayment Schedule",repay.reference,"is_accrued", 1)
				else:
					frappe.db.set_value("Loan Request Repayment Schedule",repay.reference,"is_accrued", 0)
				update_total_amount_paid(parent)
