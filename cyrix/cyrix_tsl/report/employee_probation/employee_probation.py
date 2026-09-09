# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate,add_months,date_diff


def execute(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for the report. It accepts the filters as a
	dictionary and should return columns and data. It is called by the framework
	every time the report is refreshed or a filter is updated.
	"""
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def execute_snapshot_report(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for snapshot report. When 'Synced
	Report' is enabled in report, framework will call this method
	every time the report is refreshed or a filter is updated. It
	accepts the same filters as normal execute. But a utility method -
	get_latest_sync, is also imported.

	"""
	from frappe.database.duckdb.database import get_latest_sync

	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def get_columns(filters) -> list[dict]:
	columns = [
		{"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150},
		{"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 300},
		{"label": "Date of Joining", "fieldname": "date_of_joining", "fieldtype": "Date", "width": 150},
		{"label": "End Date", "fieldname": "base_end_date", "fieldtype": "Date", "width": 190, "hidden":1},

	]

	if filters and filters.get("company") != "Cyrix TSL - UAE":
		columns += [
			{"label": "Leave Days (within probation)", "fieldname": "leave_days", "fieldtype": "Float", "width": 270},
			{"label": "Weekly Off/Holidays", "fieldname": "holiday_days", "fieldtype": "Float", "width": 270}

		]

	columns += [
		{"label": "Probation End Date", "fieldname": "probation_end_date", "fieldtype": "Date", "width": 190},
		{"label": "Probation Status", "fieldname": "probation_status", "fieldtype": "Data", "width": 150},
		{
			"label": "Difference",
			"fieldname": "difference",
			"fieldtype": "Int",
			"width": 190,
			"hidden": 1
		}
	]

	return columns

def get_data(filters) -> list[list]:

	employees = frappe.get_all(
		"Employee",
		fields=["name", "employee_name", "date_of_joining", "company"],
		filters={"status": "Active", "designation": ["!=", "E-Commerce"], "company": filters.get("company")}
		if filters and filters.get("company")
		else {"status": "Active", "designation": ["!=", "E-Commerce"]},
		order_by="date_of_joining asc",
	)

	data = []
	today = getdate(nowdate())
	one_year_ago = add_months(today, -12)

	for emp in employees:
		if not emp.date_of_joining:
			continue

		doj = getdate(emp.date_of_joining)

		# ---------------- UAE ----------------
		if emp.company == "Cyrix TSL - UAE":
			probation_end_date = add_months(doj, 6)

			if today <= probation_end_date or doj > one_year_ago:
				difference = max(date_diff(probation_end_date, today), 0)
				probation_status = "Active" if today <= probation_end_date else "Completed"

				data.append({
					"employee": emp.name,
					"employee_name": emp.employee_name,
					"date_of_joining": doj,
					"leave_days": 0,
					"probation_end_date": probation_end_date,
					"difference": difference,
					"probation_status": probation_status
				})

		# ---------------- KUWAIT ----------------
		elif emp.company == "Cyrix TSL - Kuwait":

			base_end_date = add_days(doj, 100)
			holiday_list = frappe.db.get_value("Employee",emp.name,"holiday_list")

			leave_days = frappe.db.sql("""
				SELECT SUM(total_leave_days)
				FROM `tabLeave Application Form`
				WHERE employee = %s
				AND docstatus = 1
				AND from_date <= %s
				AND to_date >= %s
			""", (emp.name, base_end_date, doj))[0][0] or 0


			holidays = frappe.db.sql(
				"""select count(distinct holiday_date) from `tabHoliday` h1, `tabHoliday List` h2
				where h1.parent = h2.name and h1.holiday_date between %s and %s
				and h2.name = %s """,
				(doj, base_end_date, holiday_list),
			)[0][0] or 0

			if holidays:
				needed = leave_days + holidays
			else:
				needed = leave_days
			probation_end_date = add_days(base_end_date, needed)


			if today <= probation_end_date or doj > one_year_ago:
				difference = max(date_diff(probation_end_date, today), 0)
				probation_status = "Active" if today <= probation_end_date else "Completed"

				data.append({
					"employee": emp.name,
					"employee_name": emp.employee_name,
					"date_of_joining": doj,
					"base_end_date":base_end_date,
					"leave_days": leave_days,
					"holiday_days": holidays,
					"probation_end_date": probation_end_date,
					"difference": difference,
					"probation_status": probation_status
				})

		# ---------------- OTHER COMPANIES ----------------
		else:
			probation_end_date = add_days(doj, 180)

			if today <= probation_end_date or doj > one_year_ago:
				difference = max(date_diff(probation_end_date, today), 0)
				probation_status = "Active" if today <= probation_end_date else "Completed"

				data.append({
					"employee": emp.name,
					"employee_name": emp.employee_name,
					"date_of_joining": doj,
					"leave_days": 0,
					"holiday_days": 0,
					"probation_end_date": probation_end_date,
					"base_end_date": probation_end_date,
					"difference": difference,
					"probation_status": probation_status
				})

	return data