# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import (
	add_days,
	getdate,
	today
)

class ResignationForm(Document):
	def on_submit(self):
		if not self.actual_relieving_date or not self.hods_relieving_date:
			frappe.throw("HR Relieving Date is not given")
		frappe.db.set_value("Employee",self.employee,'relieving_date',self.actual_relieving_date)

	def on_update_after_submit(self):
		frappe.db.set_value("Employee",self.employee,'relieving_date',self.actual_relieving_date)

def update_employee_status():
	update_resignation_date()
	today_date = frappe.flags.current_date or getdate()

	emp_list = frappe.db.get_all("Employee", {'status': "Active"}, ["name", "relieving_date", "termination_date"])
	for emp in emp_list:
		relieving_date = emp['relieving_date'] or emp['termination_date']	
		if relieving_date and relieving_date <= today_date:
			frappe.db.set_value("Employee", emp['name'], 'status', "Left")

def update_resignation_date():
	res_list = frappe.db.get_all(
		"Resignation Form",
		filters={
			"docstatus": 1,
			"actual_relieving_date": (">=", today())
		},
		fields=["name", "employee", "hods_relieving_date"]
	)

	if not res_list:
		return

	employee_ids = [res.employee for res in res_list]	
	employee_relieving_dates = frappe.db.get_all(
		"Employee",
		filters={"name": ("in", employee_ids)},
		fields=["name", "relieving_date"]
	)
	employee_map = {emp.name: emp.relieving_date for emp in employee_relieving_dates}
	for res in res_list:
		relieving_date = employee_map.get(res.employee)
		calculated = calculate_relieving_date(res.employee, res.hods_relieving_date)

		# Skip if no change
		if relieving_date != calculated:
			doc = frappe.get_doc("Resignation Form",res.name)
			doc.actual_relieving_date = calculated
			doc.save(ignore_permissions = True)
	

@frappe.whitelist()
def schedule_update_employee_status():
	job = frappe.db.exists('Scheduled Job Type', 'resignation_form.update_employee_status')
	if not job:
		sjt = frappe.new_doc("Scheduled Job Type")  
		sjt.update({
			"method" : 'cyrix.cyrix_tsl.doctype.resignation_form.resignation_form.update_employee_status',
			"frequency" : 'Daily',
		})
		sjt.save(ignore_permissions=True)

@frappe.whitelist()
def calculate_relieving_date(employee,posting_date):
	posting_date = getdate(posting_date)
	calculated_relieving_date = add_days(posting_date, 90)
	return calculated_relieving_date