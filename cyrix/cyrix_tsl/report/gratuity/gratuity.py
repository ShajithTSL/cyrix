# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff,today,cstr
from dateutil.relativedelta import relativedelta
import datetime
from datetime import date,timedelta
from frappe.utils import date_diff, add_months,today,add_days,add_years,nowdate,flt


def execute(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for the report. It accepts the filters as a
	dictionary and should return columns and data. It is called by the framework
	every time the report is refreshed or a filter is updated.
	"""
	columns, data = [], []
	columns = get_columns(filters)
	data = calculate_gratuity(filters)
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
	data = calculate_gratuity(filters)

	return columns, data

def get_columns(filters):
	"""Return columns for the report.

	One field definition per column, just like a DocType field definition.
	"""
	return [
		{
			"fieldname": "employee_id",
			"label": _("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 230
		},
		{
			"fieldname": "date_of_joining",
			"label": _("Date of Joining"),
			"fieldtype": "Date",
			"width": 130
		},
		{
			"fieldname": "years_of_service",
			"label": _("Years of Service"),
			"fieldtype": "Data",
			"width": 250
		},
		{
			"fieldname": "company",
			"label": _("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"width": 210,
		},
		{
			"fieldname": "currency",
			"label": _("Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"width": 120,
			"hidden":1
		},
		{
			"fieldname": "ctc",
			"label": _("CTC"),
			"fieldtype": "Currency",
			"options": 'currency',
			"width": 150
		},

		
		{
			"fieldname": "termination_days",
			"label": _("Termination Days"),
			"fieldtype": "Float;",
			"options": 'float;',
			"width": 150
		},
		{
			"fieldname": "termination",
			"label": _("Termination"),
			"fieldtype": "Currency",
			"options": 'currency',
			"width": 150
		},
		{
			"fieldname": "resignation_days",
			"label": _("Resignation Days"),
			"fieldtype": "Float;",
			"options": 'float;',
			"width": 150
		},
		{
			"fieldname": "resignation",
			"label": _("Resignation"),
			"fieldtype": "Currency",
			"options": 'currency',
			"width": 150
		}
	]


def calculate_gratuity(filters):
	row = []
	data = []
	if filters.get("employee") and filters.get("company"):
		employees = frappe.get_all('Employee',{"status": ["in", ["Active", "Left"]],'employee':filters.get("employee"),'company':filters.get("company")},["*"])
	elif filters.get("employee") and not filters.get("company"):
		employees = frappe.get_all('Employee',{"status": ["in", ["Active", "Left"]],'employee':filters.get("employee")},["*"])
	elif not filters.get("employee") and filters.get("company"):
		employees = frappe.get_all('Employee',{"status": ["in", ["Active", "Left"]],'company':filters.get("company")},["*"])
	else:
		employees = frappe.get_all('Employee',{"status": ["in", ["Active", "Left"]]},["*"])
		
	for emp in employees:
		from datetime import datetime
		from dateutil import relativedelta
		if filters.get("date"):
			date_2 = datetime.strptime(str(filters.get("date")),"%Y-%m-%d")
		else:
			date_2 = datetime.now()
		diff = relativedelta.relativedelta(date_2, emp.date_of_joining)
		yos = cstr(diff.years) + ' years, ' + cstr(diff.months) +' months and ' + cstr(diff.days) + ' days'
		exp_years = diff.years
		exp_month = diff.months
		exp_days = diff.days
		total_days = (exp_years * 365) + (exp_month * 30) + exp_days
		currency = frappe.db.get_value("Company",emp.company,'default_currency')
		if emp.company == "Cyrix TSL - Kuwait":
			if exp_years < 1:
				# Termination
				per = (emp.ctc*15/26)
				for_years = per * exp_years
				for_days_months = ((exp_month/12)+ (exp_days/365)) * per
				gratuity = for_years + for_days_months

				# Termination Days
				days_in_year = 15 * exp_years
				days_months = 15 * ((exp_month/12)+ (exp_days/365))
				term_days = days_in_year + days_months

				row = [emp.name,emp.employee_name,emp.date_of_joining,yos,emp.company,currency,emp.ctc,round(term_days,2),round(gratuity,2),0,0]
				data.append(row)

			if(exp_years >= 1 and exp_years < 5):
				# Termination
				per = (emp.ctc*15/26)
				for_years = per * exp_years
				for_days_months = ((exp_month/12)+ (exp_days/365)) * per
				gratuity = for_years + for_days_months

				# Termination Days
				days_in_year = 15 * exp_years
				days_months = 15 * ((exp_month/12)+ (exp_days/365))
				term_days = days_in_year + days_months

				if(exp_years >= 3):
					# Resignation if geater than 3years of experience
					res_gratuity = (for_years + for_days_months) * (1/2)
					res_days = term_days * (1/2)
				else:
					# Resignation below 3yeras of experience
					res_gratuity = 0
					res_days = 0

				row = [emp.name,emp.employee_name,emp.date_of_joining,yos,emp.company,currency,emp.ctc,round(term_days,2),round(gratuity,2),round(res_days,2),round(res_gratuity,2)]
				data.append(row)
			
			elif(exp_years >= 5):
				# Termination Gratuity
				per = (emp.ctc * 30 / 26)
				first_five_years = (emp.ctc*15/26)*5
				additional_years = exp_years - 5
				gratuity_additional_years = per * additional_years
				for_days_months = ((exp_month/12)+ (exp_days/365)) * per
				gratuity = first_five_years +gratuity_additional_years+ for_days_months

				# Termination Days
				five_years = 15*5
				add_years = 30 * additional_years
				days_months = 30 * ((exp_month/12)+ (exp_days/365))
				term_days = five_years + add_years + days_months


				# Resignation Gratuity
				res = (emp.ctc * 30 / 26)
				res_additional_years = res * additional_years
				res_days_months = res * ((exp_month/12)+ (exp_days/365))

				# Resignation Days
				res_add_years = 30 * additional_years
				res_days_and_months = 30 * ((exp_month/12)+ (exp_days/365))

				if exp_years > 10:
					resignation = first_five_years + res_additional_years + res_days_months
					res_days = five_years + res_add_years + res_days_and_months
				else:
					resignation = (first_five_years + res_additional_years + res_days_months) * (2/3)
					res_days = (five_years + res_add_years + res_days_and_months) * (2/3)
				
				point = emp.ctc * 18
				if resignation >= point:
					resignation = point
				if gratuity >= point:
					gratuity = point
				

				row = [emp.name,emp.employee_name,emp.date_of_joining,yos,emp.company,currency,emp.ctc,round(term_days,2),round(gratuity,2),round(res_days,2),round(resignation,2)]
				data.append(row)

		elif emp.company == "Company Al-Halloul Faniye Medical":
			yos = cstr(diff.years) + ' years, ' + cstr(diff.months) +' months and ' + cstr(diff.days + 1) + ' days'
			exp_days = diff.days + 1
			if exp_years < 2:
				# Termination
				per = (emp.ctc*0.5)
				for_years = per * exp_years
				day_month_calc = per/12
				for_days_months = ((day_month_calc * exp_month) + ((day_month_calc/30) * exp_days))
				# for_days_months = ((exp_month/12)+ (exp_days/365)) * per
				gratuity = for_years + for_days_months

				# Termination Days
				days_in_year = 15 * exp_years
				days_months = 15 * ((exp_month/12)+ (exp_days/365))
				term_days = days_in_year + days_months

				row = [emp.name,emp.employee_name,emp.date_of_joining,yos,emp.company,currency,emp.ctc,round(term_days,2),round(gratuity,2),0,0]
				data.append(row)

			if(exp_years >= 2 and exp_years < 5):
				# Termination
				per = (emp.ctc*0.5)
				for_years = per * exp_years
				day_month_calc = per/12
				for_days_months = ((day_month_calc * exp_month) + ((day_month_calc/30) * exp_days))
				gratuity = for_years + for_days_months

				# Termination Days
				days_in_year = 15 * exp_years
				days_months = 15 * ((exp_month/12)+ (exp_days/365))
				term_days = days_in_year + days_months

				# Resignation
				res_days = 0
				
				per = emp.ctc * 0.5 * (1/3)
				for_years = per * exp_years
				day_month_calc = per/12
				for_days_months = ((day_month_calc * exp_month) + ((day_month_calc/30) * exp_days))
				res_gratuity = for_years + for_days_months

				# Resignation Days
				res_add_years = 15 * exp_years
				res_days_and_months = 15 * ((exp_month/12)+ (exp_days/365))
				res_days = (res_add_years + res_days_and_months) * (1/3)
			
				row = [emp.name,emp.employee_name,emp.date_of_joining,yos,emp.company,currency,emp.ctc,round(term_days,2),round(gratuity,2),round(res_days,2),round(res_gratuity,2)]
				data.append(row)

			elif(exp_years >= 5):
				# Termination Gratuity
				per = (emp.ctc)
				first_five_years = (emp.ctc*0.5)*5
				additional_years = exp_years - 5
				gratuity_additional_years = per * additional_years
				day_month_calc = per/12
				for_days_months = ((day_month_calc * exp_month) + ((day_month_calc/30) * exp_days))
				gratuity = first_five_years +gratuity_additional_years+ for_days_months

				# Termination Days
				five_years = 15*5
				add_years = 30 * additional_years
				days_months = 30 * ((exp_month/12)+ (exp_days/365))
				term_days = five_years + add_years + days_months


				# Resignation Gratuity
				res_first_five = emp.ctc * 0.5
				res = res_first_five * 5
				res_additional_years = emp.ctc * additional_years
				day_month_calc = emp.ctc/12
				res_days_months = ((day_month_calc * exp_month) + ((day_month_calc/30) * exp_days))

				# Resignation Days
				res_add_years = 30 * additional_years
				res_days_and_months = 30 * ((exp_month/12)+ (exp_days/365))
				if exp_years >= 10:
					resignation = res + res_additional_years + res_days_months
					res_days = five_years + res_add_years + res_days_and_months
				else:
					resignation = (res + res_additional_years + res_days_months) * (2/3)
					res_days = (five_years + res_add_years + res_days_and_months) * (2/3)
				
				row = [emp.name,emp.employee_name,emp.date_of_joining,yos,emp.company,currency,emp.ctc,round(term_days,2),round(gratuity,2),round(res_days,2),round(resignation,2)]
				data.append(row)

		elif emp.company == "Cyrix TSL - UAE":
			per_day = emp.basic / 30
			if exp_years > 0:
				if exp_years < 5:
					years = 21 * per_day * exp_years
					gratuity = (((exp_month/12)+ (exp_days/365)) * per_day * 21) + years
				else:
					gratuity = (21 * per_day * 5) + (30 * per_day * (exp_years - 5)) + ((exp_month/12)+ (exp_days/365)) * per_day * 30
				row = [emp.name,emp.employee_name,emp.date_of_joining,yos,emp.company,currency,emp.basic,0,gratuity,0,gratuity]
			else:
				row = [emp.name,emp.employee_name,emp.date_of_joining,yos,emp.company,currency,emp.basic,0,0,0,0]
			data.append(row)


		# else:
		# 	row = [emp.name,emp.employee_name,emp.date_of_joining,yos,emp.company,currency,emp.basic,0,0,0,0]
		# 	data.append(row)

	return data