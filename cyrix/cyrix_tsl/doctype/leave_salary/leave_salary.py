# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LeaveSalary(Document):
	def on_submit(self):
		if self.is_leaves_encashed and self.encashment_days:
			self.create_leave_encashment()
		
	def on_cancel(self):
		if self.leave_encashment:
			doc = frappe.get_doc("Leave Encashment Data",self.leave_encashment)
			if doc.docstatus == 1:
				ad_sal = frappe.get_doc("Additional Salary",{'ref_docname':doc.name})
				if ad_sal.docstatus ==1:
					ad_sal.cancel()
				doc.cancel()

	def after_insert(self):
		if self.leave_application:
			frappe.db.set_value("Leave Application Form",self.leave_application,"leave_salary_reference",self.name,update_modified = False)

	def on_trash(self):
		frappe.db.set_value("Leave Application Form",self.leave_application,"leave_salary_reference",'',update_modified = False)

	def create_leave_encashment(self):
		doc = frappe.new_doc("Leave Encashment Data")
		doc.company = self.company
		doc.employee = self.employee
		doc.currency = self.currency
		doc.encashment_days = self.encashment_days
		doc.leave_type = "Annual Leave"
		doc.save(ignore_permissions = True)
		doc.submit()
		self.leave_encashment = doc.name
		frappe.db.set_value("Leave Salary",self.name,"leave_encashment",doc.name,update_modified = False)

@frappe.whitelist()
def check_for_active_loans(name):
	status = "Not Exists"
	if frappe.db.exists("Loan Request",{'employee':name,'status':("not in",["Loan Settled"])}):
		status = "Exists"
	return status



@frappe.whitelist()
def check_balance_leaves(employee):
	actual_leave_balance = 0
	from frappe.utils import getdate
	today = getdate()
	from cyrix.hr_py.leave_application import get_leave_details
	val = get_leave_details(employee, today)

	# Check if 'Annual Leave' allocation exists
	if 'Annual Leave' in val['leave_allocation']:
		annual_leave_balance = val['leave_allocation']['Annual Leave']['remaining_leaves']
		
		# Check if there are any draft Planned Leaves
		if frappe.db.exists("Planned Leaves", {'employee': employee, 'docstatus': 0}):
			planned_leave_balance = frappe.db.get_value("Planned Leaves", 
													{'employee': employee, 'docstatus': 0}, 
													'leave_days') or 0
			# Subtract the planned leave balance from the annual leave balance
			actual_leave_balance = annual_leave_balance - planned_leave_balance
		else:
			# If no planned leaves are found, just use the annual leave balance
			actual_leave_balance = annual_leave_balance
	else:
		actual_leave_balance = 0

	return actual_leave_balance



from datetime import datetime, timedelta, date
from frappe.utils import (
	add_days,
	add_months,
	cint,
	date_diff,
	flt,
	get_first_day,
	get_last_day,
	get_link_to_form,
	getdate,
	rounded,
	today,
)
@frappe.whitelist()
def get_leave_application(leave_application):
	from hrms.hr.doctype.leave_application.leave_application import get_leave_details
	leave_app = frappe.db.sql(""" select * from `tabLeave Application Form` where name = '%s' """%(leave_application),as_dict=1)
	if leave_app:
		
		for lap in leave_app:
			remaining_leaves = 0
			val = get_leave_details(lap.employee,today())
			if val['leave_allocation'].get("Annual Leave", {}).get("remaining_leaves"):
				remaining_leaves = (val['leave_allocation'].get("Annual Leave", {}).get("remaining_leaves"))
			from_date = lap.leave_start_date or lap.from_date
			first_of_month = from_date.replace(day=1)
			if first_of_month != from_date:
				before_day = from_date - timedelta(days=1)
				to_date = lap.leave_end_date
				worked_days = validate_balance_leaves(lap.company,first_of_month,before_day,lap.employee,lap.leave_type)
				leave_days = date_diff(to_date,from_date) +1
				holiday_count = get_holidays(lap.employee, lap.leave_start_date,lap.leave_end_date , holiday_list=None, company = lap.company)
				return first_of_month,before_day,lap.leave_start_date,lap.leave_end_date,worked_days,lap.leave_days,lap.leave_balance,holiday_count
			else:
				to_date = lap.leave_end_date
				holiday_count = get_holidays(lap.employee, lap.leave_start_date,lap.leave_end_date , holiday_list=None, company = lap.company)
				return '','',lap.leave_start_date,lap.leave_end_date,0,lap.leave_days,lap.leave_balance,holiday_count


@frappe.whitelist()
def validate_balance_leaves(company,from_date,to_date,employee,leave_type,half_day = None,half_day_date = None):
	holiday_list = frappe.db.get_value("Employee",employee,'holiday_list') or None
	if company == "Cyrix TSL - Kuwait":
		total_leave_days = get_number_of_leave_days(
			company,
			employee,
			leave_type,
			from_date,
			to_date,
			half_day,
			half_day_date,
			holiday_list
		)
	else:
		total_leave_days = date_diff(to_date,from_date) +1
	return total_leave_days

@frappe.whitelist()
def get_number_of_leave_days(
	company,
	employee,
	leave_type,
	from_date,
	to_date,
	half_day,
	half_day_date,
	holiday_list,
) -> float:
	"""Returns number of leave days between 2 dates after considering half day and holidays
	(Based on the include_holiday setting in Leave Type)"""
	number_of_days = 0
	if cint(half_day) == 1:
		if getdate(from_date) == getdate(to_date):
			number_of_days = 0.5
		elif half_day_date and getdate(from_date) <= getdate(half_day_date) <= getdate(to_date):
			number_of_days = date_diff(to_date, from_date) + 0.5
		else:
			number_of_days = date_diff(to_date, from_date) + 1
	else:
		number_of_days = date_diff(to_date, from_date) + 1
	number_of_days = flt(number_of_days) - flt(
		get_holidays_no(employee, from_date, to_date, holiday_list=holiday_list, company=company)
	)
	return number_of_days

def get_holidays_no(employee, from_date, to_date, holiday_list=None, company = None):
	"""get holidays between two dates for the given employee"""
	from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
	if not holiday_list:
		holiday_list = get_holiday_list_for_employee(employee)
	holidays = frappe.db.sql(
		"""select count(distinct holiday_date) from `tabHoliday` h1, `tabHoliday List` h2
		where h1.parent = h2.name and h1.holiday_date between %s and %s
		and h2.name = %s and h1.weekly_off = 1 """,
		(from_date, to_date, holiday_list),
	)[0][0]

	return holidays

def get_holidays(employee, from_date, to_date, holiday_list=None, company = None):
	"""get holidays between two dates for the given employee"""
	from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
	if not holiday_list:
		holiday_list = get_holiday_list_for_employee(employee)
	holidays = frappe.db.sql(
		"""select count(distinct holiday_date) from `tabHoliday` h1, `tabHoliday List` h2
		where h1.parent = h2.name and h1.holiday_date between %s and %s
		and h2.name = %s and h1.weekly_off = 0 """,
		(from_date, to_date, holiday_list),
	)[0][0]

	return holidays