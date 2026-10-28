# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import datetime
from frappe.utils import (
	add_days,
	today,
	cint,
	cstr,
	date_diff,
	flt,
	formatdate,
	get_fullname,
	get_link_to_form,
	getdate,now_datetime,
	nowdate,
	get_first_day,
	get_last_day
)

from frappe import _

# ---- Adjust these to match your Leave Rejoining doctype / policy ----
F_EMPLOYEE = "emp_no"
F_LATE_DAYS = "late_days"
F_REJOIN_DATE = "actual_rejoining_date"
F_COMPANY = "company"                      # if not on the doctype, it's taken from Employee
F_APPROVED = "early_join_approved"         # custom Check field (hidden)
F_ADDL_SALARY = "early_join_additional_salary"  # custom Link -> Additional Salary (read only)
F_REMARKS = "early_join_remarks"
ADDL_REMARKS_FIELD = "custom_remarks"
SALARY_COMPONENT = "Additions"
# --------------------------------------------------------------------




class LeaveRejoiningForm(Document):
	def before_submit(self):
		if not _early_days(self):
			return
		
		if not cint(self.get(F_APPROVED)):
			frappe.throw(_("Please confirm the early-join Additional Salary before submitting."))

		if not (self.get(F_REMARKS) or "").strip():
			frappe.throw(_("Remarks are required for the early-join Additional Salary."))

	def on_cancel(self):
		self.cancel_leaves()
		name = self.get(F_ADDL_SALARY)
		if not name:
			return
		addl = frappe.get_doc("Additional Salary", name)
		if addl.docstatus == 1:
			addl.flags.ignore_permissions = True
			addl.cancel()
		
	def cancel_leaves(self):
		leave_apps = frappe.get_all("Leave Application", filters={"rejoining": self.name}, fields=["name"])
		for leave in leave_apps:
			leave_doc = frappe.get_doc("Leave Application", leave.name)
			if leave_doc.docstatus == 1:
				leave_doc.flags.ignore_permissions = True
				leave_doc.cancel()

	def after_insert(self):
		if self.leave_application:
			frappe.db.set_value("Leave Application Form",self.leave_application,"rejoining",self.name,update_modified = False)

	def on_submit(self):
		post_additional_salary(self, method=None)
		if self.leave_type:
			if self.unpaid_start_date and self.unpaid_end_date:
				lwp = frappe.new_doc("Leave Application")
				lwp.rejoining = self.name
				lwp.employee = self.emp_no
				lwp.leave_type = "Leave Without Pay"
				lwp.from_date = self.unpaid_start_date
				lwp.to_date = self.unpaid_end_date
				lwp.status = "Approved"
				lwp.leave_approver = get_leave_approver(self.emp_no)
				lwp.save()
				lwp.submit()
				
				l_ap = frappe.new_doc("Leave Application")
				l_ap.rejoining = self.name
				l_ap.employee = self.emp_no
				l_ap.leave_type = self.leave_type
				l_ap.from_date = self.rejoining_date
				l_ap.to_date = add_days(self.unpaid_start_date,-1)
				l_ap.status = "Approved"
				l_ap.leave_approver = get_leave_approver(self.emp_no)
				l_ap.save()
				l_ap.submit()
			else:
				l_ap = frappe.new_doc("Leave Application")
				l_ap.rejoining = self.name
				l_ap.employee = self.emp_no
				l_ap.leave_type = self.leave_type
				l_ap.from_date = self.rejoining_date
				l_ap.to_date = add_days(self.actual_rejoining_date,-1) 
				l_ap.status = "Approved"
				l_ap.leave_approver = get_leave_approver(self.emp_no)
				l_ap.save()
				l_ap.submit()


from hrms.hr.doctype.leave_application.leave_application import get_holidays
@frappe.whitelist()
def get_number_of_leave_days(
	employee: str,
	from_date: datetime.date,
	to_date: datetime.date,
	half_day = None,
	half_day_date = None,
	holiday_list = None,
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
	company = frappe.db.get_value("Employee",employee,'company')
	
	if company != "Cyrix TSL - Kuwait":
		number_of_days = flt(number_of_days) - flt(
			get_holidays_no_lop(employee, from_date, to_date, holiday_list=holiday_list)
		)
	
	if number_of_days < 0 and company == "Cyrix TSL - Kuwait":
		number_of_days = flt(number_of_days) + flt(
			get_weekoffs(employee, from_date, to_date, holiday_list=holiday_list)
		)
	return number_of_days

from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

def get_holidays_no_lop(employee, from_date, to_date, holiday_list=None, company = None):
	"""get holidays between two dates for the given employee"""
	if not holiday_list:
		holiday_list = get_holiday_list_for_employee(employee)
	company = frappe.db.get_value("Employee",employee,'company')
	holidays = frappe.db.sql(
		"""select count(distinct holiday_date) from `tabHoliday` h1, `tabHoliday List` h2
		where h1.parent = h2.name and h1.holiday_date between %s and %s
		and h2.name = %s and h1.weekly_off = 0 """,
		(from_date, to_date, holiday_list),
	)[0][0]

	return holidays

def get_weekoffs(employee, from_date, to_date, holiday_list=None, company = None):
	"""get holidays between two dates for the given employee"""
	if not holiday_list:
		holiday_list = get_holiday_list_for_employee(employee)
	company = frappe.db.get_value("Employee",employee,'company')
	holidays = frappe.db.sql(
		"""select count(distinct holiday_date) from `tabHoliday` h1, `tabHoliday List` h2
		where h1.parent = h2.name and h1.holiday_date between %s and %s
		and h2.name = %s and h1.weekly_off = 1 """,
		(to_date, from_date, holiday_list),
	)[0][0]
	return holidays

def get_leave_approver(employee):
	leave_approver, department = frappe.db.get_value("Employee", employee, ["leave_approver", "department"])

	if not leave_approver and department:
		leave_approver = frappe.db.get_value(
			"Department Approver",
			{"parent": department, "parentfield": "leave_approvers", "idx": 1},
			"approver",
		)

	return leave_approver

def _early_days(doc):
	late = cint(doc.get(F_LATE_DAYS))
	return abs(late) if late < 0 else 0


def _get_company(doc):
	return doc.get(F_COMPANY) or frappe.db.get_value("Employee", doc.get(F_EMPLOYEE), "company")

def per_day_salary(employee, payroll_date):
	ctc = frappe.db.get_value("Employee",employee,'ctc')
	company = frappe.db.get_value("Employee",employee,'company')
	if company == "Cyrix TSL - Kuwait":
		working_days = 26
	else:
		working_days = 30
	if ctc and ctc > 0:
		perday = ctc / working_days
	else:
		perday = 0
	return perday

def calculate(doc):
	days = _early_days(doc)
	if not days:
		return None

	payroll_date = get_first_day(today())
	ctc = frappe.db.get_value("Employee", doc.get(F_EMPLOYEE), "ctc")
	per_day = flt(per_day_salary(doc.get(F_EMPLOYEE), payroll_date))
	amount = flt(per_day * days, 2)

	return frappe._dict(
		employee=doc.get(F_EMPLOYEE),
		employee_name=frappe.db.get_value("Employee", doc.get(F_EMPLOYEE), "employee_name"),
		company=_get_company(doc),
		salary_component=SALARY_COMPONENT,
		early_days=days,
		monthly_base=flt(ctc),
		per_day_salary=flt(per_day, 2),
		amount=amount,
		currency=frappe.db.get_value("Employee", doc.get(F_EMPLOYEE), "salary_currency") or frappe.db.get_value("Company", _get_company(doc), "default_currency"),
		payroll_date=str(payroll_date)
	)

@frappe.whitelist()
def get_early_join_preview(doc):
	"""Called from the client before submit to show the HR Manager the popup."""
	doc = frappe.get_doc(frappe.parse_json(doc)) if isinstance(doc, str) else doc
	return calculate(doc)


def post_additional_salary(doc, method=None):
	data = calculate(doc)
	if not data or not data.amount:
		return

	addl = frappe.get_doc({
		"doctype": "Additional Salary",
		"employee": data.employee,
		"company": data.company,
		"salary_component": data.salary_component,
		"amount": data.amount,
		"currency": data.currency,
		"payroll_date": data.payroll_date,
		"overwrite_salary_structure_amount": 0,
		"ref_doctype": doc.doctype,
		"ref_docname": doc.name,
		ADDL_REMARKS_FIELD: doc.get(F_REMARKS) or data.default_remarks
	})
	addl.flags.ignore_permissions = True
	addl.insert()
	addl.submit()

	doc.db_set(F_ADDL_SALARY, addl.name)
	frappe.msgprint(
		_("Additional Salary {0} created for {1} early-joined day(s): {2}").format(
			frappe.utils.get_link_to_form("Additional Salary", addl.name),
			data.early_days,
			frappe.format_value(data.amount, {"fieldtype": "Currency", "options": data.currency}),
		),
		alert=True,
	)