# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, timedelta
from calendar import monthrange
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

from cyrix.hr_py.leave_application import (
    get_leave_balance_on,
    get_leaves_for_period,
    get_leave_allocation_records
)

def calculate_accruals_between(employee, start_date, end_date):
    """Accrual from start_date → end_date (start < end).
       If you want to reverse (past), call with reversed dates and negate.
    """
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    eligible_annual_leaves = frappe.db.get_value("Employee", employee, "monthly_eligible_days") or 0
    monthly_leave_allocation = eligible_annual_leaves

    total = 0.0
    days = (end_date - start_date).days

    for day in range(days):
        d = start_date + timedelta(days=day)

        # days in month
        days_in_month = monthrange(d.year, d.month)[1]
        total += (monthly_leave_allocation / days_in_month)

    return round(total, 3)


def calculate_projected_leaves(employee, current_date, leave_start_date):
    current_date = datetime.strptime(current_date, "%Y-%m-%d")
    leave_start_date = datetime.strptime(leave_start_date, "%Y-%m-%d")

    if leave_start_date <= current_date:
        return 0.0

    eligible_annual_leaves = frappe.db.get_value("Employee", employee, "monthly_eligible_days")
    monthly_leave_allocation = eligible_annual_leaves or 0
    projected_leaves = 0.0

    days_until_leave = (leave_start_date - current_date).days

    for day in range(days_until_leave):
        projection_date = current_date + timedelta(days=day)

        if projection_date.month == 2:
            if (projection_date.year % 4 == 0 and (projection_date.year % 100 != 0 or projection_date.year % 400 == 0)):
                days_in_month = 29
            else:
                days_in_month = 28
        else:
            days_in_month = monthrange(projection_date.year, projection_date.month)[1]

        projected_leaves += (monthly_leave_allocation / days_in_month)

    return round(projected_leaves, 3)

def execute(filters=None):
    if not filters or not filters.get("company"):
        return [], []

    company = filters.get("company")
    to_date = filters.get("to_date")
    selected_leave_type = filters.get("leave_type")
    from_date = "2000-01-01"

    # NEW: Check if the selected date is future
    is_future_date = getdate(to_date) > getdate(today())
    is_past_date = getdate(to_date) < getdate(today())
    # Get dynamic columns based on future/past
    columns = get_columns(is_future_date,is_past_date)
    data = []
    status = filters.get("status")

    if filters.get("employee"):
        employees = frappe.get_all(
            "Employee",
            filters={"company": company, "status": status, "name": filters.get("employee")},
            fields=["name", "employee_name"]
        )
    else:
        employees = frappe.get_all(
            "Employee",
            filters={"company": company, "status": status},
            fields=["name", "employee_name"]
        )

    precision = cint(frappe.db.get_single_value("System Settings", "float_precision")) or 2

    for emp in employees:
        allocation_records = get_leave_allocation_records(emp.name, to_date)

        for leave_type, allocation in allocation_records.items():

            if selected_leave_type and leave_type != selected_leave_type:
                continue

            remaining_leaves = get_leave_balance_on(
                emp.name,
                leave_type,
                to_date,
                to_date=to_date,
                consider_all_leaves_in_the_allocation_period=True
            )

            leaves_taken = get_leaves_for_period(emp.name, leave_type, from_date, to_date) * -1
            expired_leaves = allocation.total_leaves_allocated - (remaining_leaves + leaves_taken)
            taken = expired_leaves + leaves_taken

            # Values always present
            row = {
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "leave_type": leave_type,
                "remaining": flt(remaining_leaves, precision),
            }

            # Only compute and append projection if future date AND leave type = Annual Leave
            if is_future_date and leave_type == "Annual Leave":
                projected_accrual = calculate_projected_leaves(
                    employee=emp.name,
                    current_date=today(),
                    leave_start_date=to_date
                )

                projected_balance = remaining_leaves + projected_accrual

                row["projected_accrual"] = flt(projected_accrual, precision)
                row["projected_balance"] = flt(projected_balance, precision)

            data.append(row)

            selected_date = add_days(to_date, 1)
            today_date = today()

            if getdate(selected_date) < getdate(today_date):
                # PAST DATE SITUATION
                # accruals_after_selected = calculate_accruals_between(
                #     emp.name,
                #     selected_date,
                #     today_date
                # )
                accruals_after_selected = get_leave_balance_from_ledger(emp.name, leave_type, today_date, selected_date)
                frappe.errprint(accruals_after_selected)
                balance_on_past_date = remaining_leaves - accruals_after_selected

                row["removed_accruals"] = flt(accruals_after_selected, precision)
                row["past_balance"] = flt(balance_on_past_date, precision)


    return columns, data

def get_columns(is_future_date,is_past_date):
    base_columns = [
        {"label": "Employee ID", "fieldtype": "Link", "fieldname": "employee", "options": "Employee", "width": 250},
        {"label": "Employee Name", "fieldtype": "Data", "fieldname": "employee_name", "width": 250},
        {"label": "Leave Type", "fieldtype": "Link", "fieldname": "leave_type", "options": "Leave Type", "width": 120},
        {"label": "Remaining", "fieldtype": "Float", "fieldname": "remaining", "width": 150},
    ]

    # Add projection columns only when future date selected
    if is_future_date:
        base_columns.extend([
            {"label": "Projected Accrual", "fieldtype": "Float", "fieldname": "projected_accrual", "width": 150},
            {"label": "Projected Balance", "fieldtype": "Float", "fieldname": "projected_balance", "width": 150},
        ])
    if is_past_date:
        base_columns.extend([
            {"label": "Accruals Removed", "fieldtype": "Float", "fieldname": "removed_accruals", "width": 150},
            {"label": "Balance as on Selected Date", "fieldtype": "Float", "fieldname": "past_balance", "width": 180},
        ])

    return base_columns

def get_leave_balance_from_ledger(employee, leave_type, start_date, end_date):
    return frappe.db.sql("""
        SELECT IFNULL(SUM(leaves), 0)
        FROM `tabLeave Ledger Entry`
        WHERE employee = %s
            AND leave_type = %s
            AND transaction_type = "Leave Allocation"
            AND creation between %s and %s
            AND is_carry_forward = 0
    """, (employee, leave_type, end_date, start_date))[0][0]