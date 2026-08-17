# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import calendar
from cyrix.cyrix_tsl.report.leave_balance.leave_balance import execute
from datetime import date, datetime
from frappe.utils import (
	add_days,
	ceil,
	cint,
	cstr,
	date_diff,
	floor,
	flt,
	formatdate,
	get_first_day,
	get_last_day,
	get_link_to_form,
	getdate,
	money_in_words,
	rounded,
)
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

class FullandFinalSettlement(Document):
	pass

@frappe.whitelist()
def calculate_leave_payment_amount(company,basic,leave_balance):
	if company == "Cyrix TSL - Kuwait":
		days = 26
	else:
		days = 30
	return float(basic)/float(days) * float(leave_balance)

@frappe.whitelist()
def get_number_of_leave_days(
	company:str,
	employee: str,
	leave_type: str,
	from_date: datetime.date,
	to_date: datetime.date,
	half_day: None = None,
	half_day_date: None = None,
	holiday_list: str | None = None
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
	if not holiday_list:
		holiday_list = get_holiday_list_for_employee(employee)
	if company == "Cyrix TSL - Kuwait":
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

@frappe.whitelist()
def gratuity_amount(employee,date):
	filters = {'employee': employee,'date': date}
	from cyrix.cyrix_tsl.report.gratuity.gratuity import execute

	result = execute(filters)
	records = result[1]
	if records:
		gratuity = {
			'termination_days': records[0][7],
			'termination_amount': records[0][8], 
			'resignation_days': records[0][9],
			'resignation_amount': records[0][10]
		}
		return gratuity
	else:
		gratuity = {
			'termination_days': 0,
			'termination_amount': 0, 
			'resignation_days': 0,
			'resignation_amount': 0
		}
		return gratuity

@frappe.whitelist()
def get_reg_form(employee):
	if frappe.db.exists('Resignation Form', {'employee': employee}):
		name_reg = frappe.db.sql(   
			"""select name,hods_relieving_date,actual_relieving_date from `tabResignation Form` where employee = %s """ % (employee), as_dict=True)[0]
		current_date = name_reg.actual_relieving_date
		first_day_of_month = current_date.replace(day=1)
		leave_balance = check_actual_leave_balance(employee, current_date)
		return name_reg.name, first_day_of_month, name_reg.actual_relieving_date, leave_balance
	else:
		termination_date = frappe.get_value('Employee', {'name': employee}, ['relieving_date'])
		current_date = termination_date
		first_day_of_month = current_date.replace(day=1)
		leave_balance = check_actual_leave_balance(employee, current_date)
		return None,first_day_of_month, termination_date, leave_balance

def check_actual_leave_balance(employee, current_date):
	emp = frappe.get_doc('Employee', {'name': employee})
	if emp.status in ['Active', 'Left']:
		filters = {
			'company': emp.company,
			'to_date': str(current_date),
			'status': emp.status,
			'employee': employee,
			'leave_type': 'Annual Leave'
		}
		result = execute(filters)  
		records = result[1]

		remaining = records[0].get('remaining') if records[0].get('remaining') else 0
		past_balance = records[0].get('past_balance') if records[0].get('past_balance') else 0
		projected_balance = records[0].get('projected_balance') if records[0].get('projected_balance') else 0
		leave_balance = past_balance or projected_balance or remaining

		return leave_balance


@frappe.whitelist()
def get_current_month_date(employee):
	ff = frappe.get_value('Resignation Form', {'employee': employee}, ['actual_relieving_date']) or frappe.get_value('Employee', {'name': employee}, ['termination_date'])
	now = ff
	days = calendar.monthrange(now.year, now.month)[1]
	return days