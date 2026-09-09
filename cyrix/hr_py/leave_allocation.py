import frappe
from frappe.model.mapper import get_mapped_doc
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
from datetime import datetime
from cyrix.hr_py.employee import create_annual_leave_allocation

# Update the monthly eligibility once the employee reaches the 5 years of experience
def update_eligible_days():
	employees = frappe.get_all("Employee", {"status": "Active","monthly_eligible_days":1.75}, ["*"])
	current_date = datetime.today().date()
	for emp in employees:
		joining_date = emp.get('date_of_joining')
		if joining_date:
			years_of_service = (current_date - joining_date).days // 365
			if years_of_service >= 5:
				frappe.db.set_value("Employee",emp.name,"monthly_eligible_days",2.5, update_modified = False)

def update_leave_allocation():
	update_eligible_days() # run this before updating the Allocation
	employees = frappe.get_all("Employee", {"status": "Active","designation": ["not in","E-Commerce"]}, ["*"])
	current_date = datetime.today().date()
	first = get_first_day(current_date)
	last = get_last_day(current_date)
	total_days = date_diff(last, first) + 1

	for emp in employees:
		per_day = emp.get("monthly_eligible_days") / total_days
		exists = frappe.db.exists("Leave Allocation", {'employee': emp.employee, 'leave_type': "Annual Leave","docstatus":1,"expired":0})
		if exists:
			la = frappe.get_doc("Leave Allocation", exists)
			la.new_leaves_allocated = la.new_leaves_allocated + per_day
			la.save(ignore_permissions=True)
			la.submit()
		else:
			create_annual_leave_allocation(emp.employee) # this will prorate the leaves based on the joining date in the company

def monitor_leave_allocation_job():
	job_type = frappe.db.get_value("Scheduled Job Type",{"method":"cyrix.hr_py.leave_allocation.update_leave_allocation"},"name")

	# Get the last Scheduled Job Log for this method
	log = frappe.db.get_value(
		"Scheduled Job Log",
		{"scheduled_job_type": job_type},
		["status", "details", "creation"],
		order_by="creation desc",
		as_dict=True
	)

	if not log:
		send_alert("No execution logs found for Leave Allocation job.")
		return

	# Should have run at midnight → ~8 hours before 8 AM
	hours_since_run = (now_datetime() - log.creation).total_seconds() / 3600

	if hours_since_run > 9:
		send_alert(f"Leave Allocation job did NOT run at midnight. Last run was {int(hours_since_run)} hours ago.")
		return

	# If it ran, check status
	if log.status != "Complete":
		msg = (
			"Leave Allocation job FAILED at midnight.<br><br>"
			f"<b>Error:</b><br>{log.details}"
		)
		send_alert(msg)


def send_alert(message):
	frappe.log_error(message, "Leave Allocation Scheduler Failure")

	frappe.sendmail(
		recipients=["shajith@tsl-me.com"],
		subject="[ALERT] Leave Allocation Job Failed",
		message=message
	)

@frappe.whitelist()
def allocate_leave_on_new_year():
	current_date = getdate(today())

	emp_list = frappe.get_all(
		"Employee",
		filters={"status": "Active","designation": ["not in","E-Commerce"]},
		fields=["name", "company"]
	)

	for emp in emp_list:
		try:
			allocate_sick_leaves(
				employee=emp["name"],
				company=emp["company"],
				today=current_date
			)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"Leave allocation failed for Employee: {emp['name']}"
			)

	frappe.db.commit()

def allocate_sick_leaves(employee, company, today):
	try:
		# Allocate from Jan 1 to Dec 31 of the current year
		from_date = getdate(f"{today.year}-01-01")
		to_date = getdate(f"{today.year}-12-31")

		leave_types = [
			{
				"type": "Sick Leave 25%",
				"days": frappe.db.get_value(
					"Leave Allocation Table",
					{"company": company},
					"sick_leave_25"
				) or 0,
			},
			{
				"type": "Sick Leave 50%",
				"days": frappe.db.get_value(
					"Leave Allocation Table",
					{"company": company},
					"sick_leave_50"
				) or 0,
			},
			{
				"type": "Sick Leave 75%",
				"days": frappe.db.get_value(
					"Leave Allocation Table",
					{"company": company},
					"sick_leave_75"
				) or 0,
			},
			{
				"type": "Sick Leave 100%",
				"days": frappe.db.get_value(
					"Leave Allocation Table",
					{"company": company},
					"sick_leave_100"
				) or 0,
			},
		]

		for leave in leave_types:
			if leave["days"] <= 0:
				continue

			exists = frappe.db.exists(
				"Leave Allocation",
				{
					"employee": employee,
					"leave_type": leave["type"],
					"from_date": from_date,
					"to_date": to_date,
					"docstatus": ["!=", 2],  # Ignore cancelled allocations
				},
			)

			if exists:
				continue

			allocation = frappe.new_doc("Leave Allocation")
			allocation.employee = employee
			allocation.leave_type = leave["type"]
			allocation.from_date = from_date
			allocation.to_date = to_date
			allocation.new_leaves_allocated = leave["days"]
			allocation.total_leaves_allocated = leave["days"]

			allocation.insert(ignore_permissions=True)
			allocation.submit()

	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"Failed to allocate sick leaves for Employee: {employee}"
		)

# for schedule job creation, called in after_migrate
def leave_allocation_schedule():
	job1 = frappe.db.exists('Scheduled Job Type', {"method" : 'cyrix.hr_py.leave_allocation.update_leave_allocation'})
	if not job1:
		sjt1 = frappe.new_doc("Scheduled Job Type")  
		sjt1.update({
			"method" : 'cyrix.hr_py.leave_allocation.update_leave_allocation',
			"frequency" : 'Daily'
		})
		sjt1.save(ignore_permissions=True)
		
	job2 = frappe.db.exists('Scheduled Job Type', {"method" : 'cyrix.hr_py.leave_allocation.monitor_leave_allocation_job'})
	if not job2:
		sjt2 = frappe.new_doc("Scheduled Job Type")  
		sjt2.update({
			"method" : 'cyrix.hr_py.leave_allocation.monitor_leave_allocation_job',
			"cron_format" : '0 8 * * *'
		})
		sjt2.save(ignore_permissions=True)

	job3 = frappe.db.exists('Scheduled Job Type', {"method" : 'cyrix.hr_py.leave_allocation.allocate_leave_on_new_year'})
	if not job3:
		sjt3 = frappe.new_doc("Scheduled Job Type")  
		sjt3.update({
			"method" : 'cyrix.hr_py.leave_allocation.allocate_leave_on_new_year',
			"frequency": "Yearly",
		})
		sjt3.save(ignore_permissions=True)