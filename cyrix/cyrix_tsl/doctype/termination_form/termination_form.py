# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TerminationForm(Document):
	def on_submit(self):
		if not self.actual_relieving_date or not self.hods_relieving_date:
			frappe.throw("Termination Date is not given")
		frappe.db.set_value("Employee",self.employee,'relieving_date',self.actual_relieving_date)
		frappe.db.set_value("Employee",self.employee,'termination_date',self.actual_relieving_date)
	
	def on_update_after_submit(self):
		frappe.db.set_value("Employee",self.employee,'relieving_date',self.actual_relieving_date)
		frappe.db.set_value("Employee",self.employee,'termination_date',self.actual_relieving_date)