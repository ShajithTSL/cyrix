# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, date_diff, add_months, get_first_day, get_last_day

def execute(filters=None):
	if not filters:
		filters = {}

	from_date = getdate(filters.get("from_date"))
	to_date = getdate(filters.get("to_date"))
	tolerance = float(filters.get("tolerance") or 0.005)

	if not from_date or not to_date:
		frappe.throw("Please select From Date and To Date")

	# Fetch active employees (excluding E-Commerce)
	employees = frappe.get_all(
		"Employee",
		filters={
			"status": "Active",
			"designation": ["!=", "E-Commerce"],
			"company": filters.get("company")
		},
		fields=["name", "employee_name", "monthly_eligible_days", "date_of_joining"]
	)

	if not employees:
		return [], []

	# Fetch Leave Ledger Entries
	emp_ids = [emp.name for emp in employees]
	leave_records = frappe.db.get_all(
		"Leave Ledger Entry",
		filters={
			"employee": ["in", emp_ids],
			"transaction_type": "Leave Allocation",
			"leave_type": "Annual Leave",
			"creation": ["between", [from_date, to_date]],
		},
		fields=["employee", "leaves"]
	)

	# Aggregate allocations
	emp_summary = {}
	for rec in leave_records:
		emp_summary.setdefault(rec.employee, 0)
		emp_summary[rec.employee] += rec.leaves

	data = []

	for emp in employees:
		join_date = getdate(emp.date_of_joining)
		if join_date > to_date:
			continue  # joined after selected range, skip

		monthly_eligible = emp.monthly_eligible_days or 0
		start_date = max(from_date, join_date)

		# ✅ Calculate prorated months (accurate with month days)
		prorated_months = get_prorated_month_fraction(start_date, to_date)

		prorated_leaves = round(monthly_eligible * prorated_months, 3)
		allocated = round(emp_summary.get(emp.name, 0), 3)
		difference = round(prorated_leaves - allocated, 3)

		# if abs(difference) > tolerance:
		data.append({
			"employee": emp.name,
			"employee_name": emp.employee_name,
			"date_of_joining": join_date,
			"eligible_months": round(prorated_months, 3),
			"monthly_eligible_days": monthly_eligible,
			"prorated_leaves": prorated_leaves,
			"allocated_leaves": allocated,
			"difference": difference,
		})

	return get_columns(), data


def get_prorated_month_fraction(start_date, end_date):
	"""
	Calculate total month-equivalent between two dates.
	Uses actual month day counts (28–31 days) for partial months.
	"""
	months = 0.0
	cur_month_start = get_first_day(start_date)

	while cur_month_start <= end_date:
		cur_month_end = get_last_day(cur_month_start)

		overlap_start = max(start_date, cur_month_start)
		overlap_end = min(end_date, cur_month_end)

		if overlap_start > overlap_end:
			break

		# Fraction of the month covered
		total_days = (cur_month_end - cur_month_start).days + 1
		active_days = (overlap_end - overlap_start).days + 1
		months += active_days / total_days

		cur_month_start = add_months(cur_month_start, 1)

	return months


def get_columns():
	return [
		{"label": "Employee ID", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": "Date of Joining", "fieldname": "date_of_joining", "fieldtype": "Date", "width": 130},
		{"label": "Eligible Months (Prorated)", "fieldname": "eligible_months", "fieldtype": "Float", "width": 160},
		{"label": "Monthly Eligible Days", "fieldname": "monthly_eligible_days", "fieldtype": "Float", "width": 150},
		{"label": "Prorated Leaves (Expected)", "fieldname": "prorated_leaves", "fieldtype": "Float", "width": 180},
		{"label": "Allocated Leaves (From Ledger)", "fieldname": "allocated_leaves", "fieldtype": "Float", "width": 180},
		{"label": "Difference", "fieldname": "difference", "fieldtype": "Float", "width": 120},
	]
