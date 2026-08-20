# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

import erpnext

salary_slip = frappe.qb.DocType("Salary Slip")
salary_detail = frappe.qb.DocType("Salary Detail")
salary_component = frappe.qb.DocType("Salary Component")


def execute(filters=None):
	if not filters:
		filters = {}

	currency = None
	if filters.get("currency"):
		currency = filters.get("currency")
	company_currency = erpnext.get_company_currency(filters.get("company"))

	salary_slips = get_salary_slips(filters, company_currency)
	if not salary_slips:
		return [], []

	earning_types, ded_types = get_earning_and_deduction_types(salary_slips)
	# cost_to_company = ["Housing Allowance","Food Allowance","Transport Allowance","Other Allowances"]
	cost_to_company = [
		{"label_in_report": "Basic", "label": "Basic", "fieldname": "base"},
		{"label_in_report": "Housing", "label": "Housing Allowance", "fieldname": "housing_allowance"},
		{"label_in_report": "Food", "label": "Food Allowance", "fieldname": "food_allowance"},
		{"label_in_report": "Transport", "label": "Transport Allowance", "fieldname": "transport_allowance"},
		{"label_in_report": "Others", "label": "Other Allowances", "fieldname": "other_allowances"},	
	]
	columns = get_columns(earning_types, ded_types, salary_slips, cost_to_company)

	ss_earning_map = get_salary_slip_details(salary_slips, currency, company_currency, "earnings")
	ss_ded_map = get_salary_slip_details(salary_slips, currency, company_currency, "deductions")
	loan_map = get_salary_slip_loan_total(salary_slips)
	doj_map = get_employee_doj_map()

	data = []
	for ss in salary_slips:
		row = {
			"salary_slip_id": ss.name,
			"employee": ss.employee,
			"employee_name": ss.employee_name,
			"branch": ss.branch,
			"department": ss.department.split("-")[0].strip() if ss.department else "",
			"designation": ss.designation,
			"data_of_joining": doj_map.get(ss.employee),
			"company": ss.company,
			"start_date": ss.start_date,
			"end_date": ss.end_date,
			"leave_without_pay": ss.leave_without_pay,
			"payment_days": ss.payment_days,
			"currency": currency or company_currency,
			"total_loan_repayment": ss.total_loan_repayment_,
			"custom_loan": loan_map.get(ss.name, 0),
		}

		update_column_width(ss, columns)

		for c in cost_to_company:
			row.update({frappe.scrub(c["fieldname"]): frappe.db.get_value("Employee", ss.employee, frappe.scrub(c["label"])) or 0})

		for e in earning_types:
			row.update({frappe.scrub(e): ss_earning_map.get(ss.name, {}).get(e)})

		for d in ded_types:
			row.update({frappe.scrub(d): ss_ded_map.get(ss.name, {}).get(d)})
			
		row.update({"loan_amount":ss.total_loan_repayment_})
		if ded_types:
			for d in ded_types:
				if d == "Loan":
					l_amt = ss_ded_map.get(ss.name, {}).get(d) or 0
					l_ca= loan_map.get(ss.name, 0)
					loan_amt = l_amt + ss.total_loan_repayment_+l_ca
					row.update({"loan_amount":loan_amt})

		if currency == company_currency:
			row.update(
				{
					"gross_pay": flt(ss.gross_pay) * flt(ss.exchange_rate),
					"total_deduction": (flt(ss.total_deduction)+flt(ss.total_loan_repayment_)) * flt(ss.exchange_rate),
					"net_pay": flt(ss.net_pay) * flt(ss.exchange_rate),
				}
			)

		else:
			row.update(
				{"gross_pay": ss.gross_pay, "total_deduction": ss.total_deduction+ss.total_loan_repayment_, "net_pay": ss.net_pay}
			)

		data.append(row)
	return columns, data

def get_earning_and_deduction_types(salary_slips):
	salary_component_and_type = {_("Earning"): [],_("Deduction"): []}

	for row in get_salary_components(salary_slips):
		component = row["salary_component"]
		label = row.get("name_in_report") or component
		component_type = get_salary_component_type(component)

		if component_type:
			order = frappe.db.get_value("Salary Component", component, "order") or 0

			entry = {"label": label,"order": order}

			if entry not in salary_component_and_type[_(component_type)]:
				salary_component_and_type[_(component_type)].append(entry)

	# sort by order
	earnings = sorted(salary_component_and_type[_("Earning")],key=lambda x: x["order"])
	deductions = sorted(salary_component_and_type[_("Deduction")],key=lambda x: x["order"])

	# return only labels
	return ([e["label"] for e in earnings],[e["label"] for e in deductions])


def get_salary_slip_loan_total(salary_slips):
    loan_map = {}

    names = [ss.name for ss in salary_slips]

    if not names:
        return loan_map

    result = frappe.db.sql("""
        SELECT parent, SUM(total_payment) as total
        FROM `tabLoan Details`
        WHERE parent IN %s
        GROUP BY parent
    """, (tuple(names),), as_dict=1)

    for r in result:
        loan_map[r.parent] = r.total

    return loan_map

def update_column_width(ss, columns):
	if ss.branch is not None:
		columns[3].update({"width": 120})
	if ss.department is not None:
		columns[4].update({"width": 120})
	if ss.designation is not None:
		columns[5].update({"width": 120})
	if ss.leave_without_pay is not None:
		columns[9].update({"width": 120})


def get_columns(earning_types, ded_types, salary_slips, cost_to_company):
	columns = [
		{
			"label": _("Salary Slip ID"),
			"fieldname": "salary_slip_id",
			"fieldtype": "Link",
			"options": "Salary Slip",
			"width": 150,
		},
		{
			"label": _("ID"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Date of Joining"),
			"fieldname": "data_of_joining",
			"fieldtype": "Date",
			"width": 80,
		},
		{
			"label": _("Branch"),
			"fieldname": "branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": -1,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": -1,
		},
		{
			"label": _("Designation"),
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 120,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 120,
		},
		{
			"label": _("Start Date"),
			"fieldname": "start_date",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("End Date"),
			"fieldname": "end_date",
			"fieldtype": "Data",
			"width": 80,
		},
	]

	for emp in cost_to_company:
		columns.append(
			{
				"label": emp["label_in_report"],
				"fieldname": frappe.scrub(emp["fieldname"]),
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		)

	for earning in earning_types:
		columns.append(
			{
				"label": earning,
				"fieldname": frappe.scrub(earning),
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		)
	
	columns.extend(
		[
			{
				"label": _("Gross Pay"),
				"fieldname": "gross_pay",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Worked Days"),
				"fieldname": "payment_days",
				"fieldtype": "Float",
				"width": 120,
			},
			
		])
			
	
	# Check if there is any loan repayment data
	any_lwp = any(ss.leave_without_pay > 0 for ss in salary_slips)
	
	if any_lwp:
		columns.extend(
			[
				{
					"label": _("Leave Without Pay"),
					"fieldname": "leave_without_pay",
					"fieldtype": "Float",
					"width": 50,
				},
			])

	for deduction in ded_types:
		columns.append(
			{
				"label": deduction,
				"fieldname": frappe.scrub(deduction),
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			}
		)
	# Check if there is any loan repayment data
	any_loan_repayment = any(ss.total_loan_repayment_ > 0 for ss in salary_slips)
	
	if any_loan_repayment:
		columns.extend(
			[
				{
					"label": _("Loan Repayment"),
					"fieldname": "total_loan_repayment",
					"fieldtype": "Currency",
					"options": "currency",
					"width": 120,
				},
			])

	
	columns.extend(
		[
			{
				"label": _("Loan"),
				"fieldname": "loan_amount",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			
			{
				"label": _("Total Deduction"),
				"fieldname": "total_deduction",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Net Pay"),
				"fieldname": "net_pay",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120,
			},
			{
				"label": _("Currency"),
				"fieldtype": "Data",
				"fieldname": "currency",
				"options": "Currency",
				"hidden": 1,
			},
		]
	)
	return columns


def get_salary_components(salary_slips):
	salary_component = frappe.qb.DocType("Salary Component")

	return (
		frappe.qb.from_(salary_detail)
		.join(salary_component)
			.on(salary_detail.salary_component == salary_component.name)
		.where(
			(salary_detail.amount != 0) &
			(salary_detail.parent.isin([d.name for d in salary_slips]))
		)
		.select(
			salary_detail.salary_component,
			salary_component.name_in_report
		)
		.distinct()
	).run(as_dict=True)



def get_salary_component_type(salary_component):
	return frappe.db.get_value("Salary Component", salary_component, "type", cache=True)


def get_salary_slips(filters, company_currency):


	employee = frappe.qb.DocType("Employee")
	doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

	query = frappe.qb.from_(salary_slip).select(salary_slip.star).join(employee).on(employee.name == salary_slip.employee)

	if filters.get("docstatus"):
		query = query.where(salary_slip.docstatus == doc_status[filters.get("docstatus")])

	if filters.get("from_date"):
		query = query.where(salary_slip.start_date >= filters.get("from_date"))

	if filters.get("to_date"):
		query = query.where(salary_slip.end_date <= filters.get("to_date"))

	if filters.get("company"):
		query = query.where(salary_slip.company == filters.get("company"))

	# if filters.get("company") == "TSL COMPANY - UAE":
	# 	if filters.get("online") and filters.get("online") == 1:
	# 		query = query.where(employee.payroll_cost_center == "Online - TSL-UAE")
	# 	else:
	# 		query = query.where(employee.payroll_cost_center != "Online - TSL-UAE")

	if filters.get("employee"):
		query = query.where(salary_slip.employee == filters.get("employee"))

	if filters.get("currency") and filters.get("currency") != company_currency:
		query = query.where(salary_slip.currency == filters.get("currency"))
	salary_slips = query.run(as_dict=1)

	return salary_slips or []


def get_employee_doj_map():
	employee = frappe.qb.DocType("Employee")

	result = (frappe.qb.from_(employee).select(employee.name, employee.date_of_joining)).run()

	return frappe._dict(result)


def get_salary_slip_details(salary_slips, currency, company_currency, component_type):
	salary_slips = [ss.name for ss in salary_slips]
	salary_comp = frappe.qb.DocType("Salary Component")
	result = (
		frappe.qb.from_(salary_slip)
		.join(salary_detail)
			.on(salary_slip.name == salary_detail.parent)
		.join(salary_comp)
			.on(salary_detail.salary_component == salary_comp.name)
		.where((salary_detail.parent.isin(salary_slips)) & (salary_detail.parentfield == component_type))
		.select(
			salary_detail.parent,
			salary_detail.salary_component,
			salary_comp.name_in_report,
			salary_detail.amount,
			salary_slip.exchange_rate
		)
	).run(as_dict=1)
	ss_map = {}

	for d in result:
		ss_map.setdefault(d.parent, frappe._dict()).setdefault(d.name_in_report or d.salary_component, 0.0)
		if currency == company_currency:
			ss_map[d.parent][d.name_in_report or d.salary_component] += flt(d.amount) * flt(
				d.exchange_rate if d.exchange_rate else 1
			)
		else:
			ss_map[d.parent][d.name_in_report or d.salary_component] += flt(d.amount)
	return ss_map
