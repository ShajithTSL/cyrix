import frappe
from erpnext.setup.doctype.employee.employee import (
	InactiveEmployeeStatusError,
	get_holiday_list_for_employee,
)

def get_holidays_for_employee(employee, start_date, end_date, raise_exception=True, only_non_weekly=False):
	"""Get Holidays for a given employee
fr
	`employee` (str)
	`start_date` (str or datetime)
	`end_date` (str or datetime)
	`raise_exception` (bool)
	`only_non_weekly` (bool)

	return: list of dicts with `holiday_date` and `description`
	"""
	holiday_list = get_holiday_list_for_employee(employee, raise_exception=raise_exception)

	if not holiday_list:
		return []

	filters = {"parent": holiday_list, "holiday_date": ("between", [start_date, end_date])}

	filters["weekly_off"] = False

	holidays = frappe.get_all(
		"Holiday", fields=["description", "holiday_date"], filters=filters, order_by="holiday_date"
	)

	return holidays