import frappe
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
	get_last_day,
	get_url
)
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from frappe.core.doctype.communication.email import make

@frappe.whitelist()
def create_leave_allocation(name):
	employee = frappe.get_doc("Employee", name)

	# Skip E-Commerce employees
	if employee.designation == "E-Commerce":
		return

	current_year = getdate(today()).year
	last_date_of_year = getdate(f"{current_year}-12-31")

	# Fetch all allocation settings in ONE query instead of four/five queries
	allocation_settings = frappe.db.get_value(
		"Leave Allocation Table",
		{"company": employee.company},
		[
			"sick_leave_25",
			"sick_leave_50",
			"sick_leave_75",
			"sick_leave_100",
			"hajj_leave",
			"maternity_leave",
		],
		as_dict=True,
	) or {}

	leave_types = [
		{
			"type": "Sick Leave 25%",
			"days": allocation_settings.get("sick_leave_25") or 0,
		},
		{
			"type": "Sick Leave 50%",
			"days": allocation_settings.get("sick_leave_50") or 0,
		},
		{
			"type": "Sick Leave 75%",
			"days": allocation_settings.get("sick_leave_75") or 0,
		},
		{
			"type": "Sick Leave 100%",
			"days": allocation_settings.get("sick_leave_100") or 0,
		},
	]

	if employee.religion == "Islam":
		leave_types.append({
			"type": "Hajj Leave",
			"days": allocation_settings.get("hajj_leave") or 0,
		})

	if employee.gender == "Female":
		leave_types.append({
			"type": "Maternity Leave",
			"days": allocation_settings.get("maternity_leave") or 0,
		})

	messages = []

	for leave in leave_types:
		days = float(leave["days"] or 0)

		# Don't create allocations with zero days
		if days <= 0:
			continue

		allocation_name = frappe.db.exists(
			"Leave Allocation",
			{
				"employee": employee.employee,
				"company": employee.company,
				"leave_type": leave["type"],
				"to_date": last_date_of_year,
			},
		)

		if allocation_name:
			messages.append(
				f"Leave Allocation <b>{allocation_name}</b> already exists "
				f"for Employee - <b>{employee.employee}</b> "
				f"for type - <b>{leave['type']}</b>"
			)
			continue

		allocation = frappe.new_doc("Leave Allocation")
		allocation.employee = employee.employee
		allocation.company = employee.company
		allocation.leave_type = leave["type"]
		allocation.from_date = today()
		allocation.to_date = last_date_of_year
		allocation.new_leaves_allocated = days
		allocation.total_leaves_allocated = days

		allocation.save(ignore_permissions=True)
		allocation.submit()

		messages.append(
			f"Leave Allocation <b>{allocation.name}</b> created "
			f"for Employee - <b>{employee.employee}</b> "
			f"for type - <b>{leave['type']}</b>"
		)

	# Annual leave for new employees
	create_annual_leave_allocation(name)

	if messages:
		frappe.msgprint("<br>".join(messages))


@frappe.whitelist()
def create_annual_leave_allocation(name):
	employee = frappe.get_doc("Employee", name)

	# Skip E-Commerce employees
	if employee.designation == "E-Commerce":
		return

	joining_date = employee.date_of_joining
	current_date = getdate(today())

	if not joining_date:
		frappe.throw("Joining date is not defined for employee")

	joining_date = getdate(joining_date)

	if joining_date > current_date:
		frappe.throw("Joining date is after current date")

	monthly_entitlement = float(employee.monthly_eligible_days or 0)

	if monthly_entitlement <= 0:
		return

	# Check existing annual allocation
	existing = frappe.db.exists(
		"Leave Allocation",
		{
			"employee": employee.name,
			"leave_type": "Annual Leave",
			"docstatus": 1,
		},
	)

	if existing:
		return

	total_leave = 0.0

	# Start from the first day of joining month
	month_start = joining_date.replace(day=1)

	while month_start <= current_date:
		year = month_start.year
		month = month_start.month

		days_in_month = calendar.monthrange(year, month)[1]
		month_end = month_start.replace(day=days_in_month)

		# Effective period inside this month
		effective_start = max(month_start, joining_date)
		effective_end = min(month_end, current_date)

		days_eligible = (effective_end - effective_start).days + 1

		total_leave += (
			days_eligible / days_in_month
		) * monthly_entitlement

		month_start += relativedelta(months=1)

	# Avoid creating an allocation with zero days
	if total_leave <= 0:
		return

	allocation = frappe.new_doc("Leave Allocation")
	allocation.employee = employee.name
	allocation.leave_type = "Annual Leave"
	allocation.from_date = joining_date
	allocation.to_date = "2100-12-31"
	allocation.new_leaves_allocated = total_leave

	allocation.save(ignore_permissions=True)
	allocation.submit()

@frappe.whitelist()
def employee_series():
	last_number = frappe.db.get_value("HR Settings","HR Settings","last_number_in_series")
	next_in_series = int(last_number)+1
	next_in_series = check_for_employee(next_in_series)
	return str(next_in_series)

def check_for_employee(name):
	# Loop until a unique employee number is found
	while frappe.db.exists("Employee", str(name)):
		name += 1
	return name

def update_last_employee_number(doc,method):
	frappe.db.set_value("HR Settings","HR Settings","last_number_in_series",doc.name)

def get_annual_leave_days(doc,method):
	years_of_service = date_diff(nowdate(), doc.date_of_joining) / 365
	# Try to find a specific rule for the given nationality
	rule = frappe.db.get_value(
		"Annual Leave Policy",
		{
			"company": doc.company,
			"leave_type": "Annual Leave",
			"from_years": ("<=", years_of_service),
			"to_years": (">", years_of_service),
		},
		["total_days","monthly_allocation"],
		as_dict=True
	)

	doc.monthly_eligible_days = rule.monthly_allocation
	doc.save()


@frappe.whitelist()
def employee_notification_schedule():
	cid_job = frappe.db.exists('Scheduled Job Type', 'employee.civil_id_expiry')
	if not cid_job:
		cid = frappe.new_doc("Scheduled Job Type")  
		cid.update({
			"method" : 'cyrix.hr_py.employee.civil_id_expiry',
			"frequency" : 'Daily',
		})
		cid.save(ignore_permissions=True)

	lic_job = frappe.db.exists('Scheduled Job Type', 'employee.license_expiry_date')
	if not lic_job:
		lic = frappe.new_doc("Scheduled Job Type")  
		lic.update({
			"method" : 'cyrix.hr_py.employee.license_expiry_date',
			"frequency" : 'Daily',
		})
		lic.save(ignore_permissions=True)

	daf_job = frappe.db.exists('Scheduled Job Type', 'employee.dafter_expiry_date')
	if not daf_job:
		daf = frappe.new_doc("Scheduled Job Type")  
		daf.update({
			"method" : 'cyrix.hr_py.employee.dafter_expiry_date',
			"frequency" : 'Daily',
		})
		daf.save(ignore_permissions=True)

def civil_id_expiry():
	MAIL_HEADER = '''Dear Mam/Sir,<br><br>Civil ID is expiring within {days} days for the below listed employees.<br><br>'''

	MAIL_BODY = '''This is to inform you that the Civil ID of the below employee is due to expire in {days} Days.<br><br>
					HR is requested to initiate the Civil ID renewal process with the relevant authority in a timely manner to ensure continuity and compliance.<br><br>
					Once the renewal is completed, kindly obtain and file a scanned copy of the renewed Civil ID in the employee records.<br><br>'''


	employees = frappe.db.get_list(
		"Employee",
		filters={"status": "Active"},
		fields=[
			"name", "employee_name", "company",
			"location", "civil_id_no", "civil_id_expiry_date"
		]
	)

	tables = {"45": [], "30": [], "15": []}
	today = getdate(nowdate())
	base_url = get_url()

	for emp in employees:
		if not emp.civil_id_expiry_date or not emp.civil_id_no:
			continue

		days = date_diff(emp.civil_id_expiry_date, today)

		row = f"""
		<tr>
			<td><a href="{base_url}/app/employee/{emp.name}">{emp.name}</a></td>
			<td>{emp.employee_name}</td>
			<td>{emp.company}</td>
			<td>{emp.location or ""}</td>
			<td>{emp.civil_id_no}</td>
			<td>{formatdate(emp.civil_id_expiry_date, "dd-MM-yyyy")}</td>
			<td>{days}</td>
		</tr>
		"""

		if days == 45:
			tables["45"].append(row)
		elif days == 30:
			tables["30"].append(row)
		elif days == 15:
			tables["15"].append(row)

	def make_table(rows):
		if not rows:
			return ""

		return """
		<table class = "table table-bordered" style="font-size:12px;">
			<tr>
				<th>Employee</th>
				<th>Employee Name</th>
				<th>Company</th>
				<th>Location</th>
				<th>Civil ID No.</th>
				<th>Expiry Date</th>
				<th>Days</th>
			</tr>
		""" + "".join(rows) + "</table>"

	email_map = {
		"45": "Action Required: Civil ID Renewal Due in 45 Days !!!",
		"30": "Action Required: Civil ID Renewal Due in 30 Days !!!",
		"15": "Action Required: Civil ID Renewal Due in 15 Days !!!"
	}

	for key, subject in email_map.items():
		if not tables[key]:
			continue

		header = MAIL_HEADER.format(days=key)
		body = MAIL_BODY.format(days=key)
		table_html = make_table(tables[key])

		message=header + body + table_html
		make(
			recipients="hr1@tsl-me.com",
			cc = [
				"yousuf@tsl-me.com",
			],
			sender="no-reply@cyrix-tsl.com",
			reply_to="no-reply@cyrix-tsl.com",
			subject = subject,
			content = message,
			send_email=1
		)


def license_expiry_date():
	MAIL_HEADER = '''Dear Mam/Sir,<br><br>Driving License is expiring within {days} days for the below listed employees.<br><br>'''

	MAIL_BODY = '''This is to inform you that the Driving License of the below employee is due to expire in {days} Days.<br><br>
					HR is requested to initiate the driving license renewal process with the relevant authority in a timely manner to ensure continuity and compliance.<br><br>
					Once the renewal is completed, kindly obtain and file a scanned copy of the renewed Driving License in the employee records.<br><br>'''

	employees = frappe.db.get_list(
		"Employee",
		filters={"status": "Active"},
		fields=[
			"name", "employee_name", "company",
			"location", "custom_driving_license_id", "custom_driving_license_expiry_date"
		]
	)

	tables = {"45": [], "30": [], "15": []}
	today = getdate(nowdate())
	base_url = get_url()

	for emp in employees:
		if not emp.custom_driving_license_expiry_date or not emp.custom_driving_license_id:
			continue

		days = date_diff(emp.custom_driving_license_expiry_date, today)

		row = f"""
		<tr>
			<td><a href="{base_url}/app/employee/{emp.name}">{emp.name}</a></td>
			<td>{emp.employee_name}</td>
			<td>{emp.company}</td>
			<td>{emp.location or ""}</td>
			<td>{emp.custom_driving_license_id}</td>
			<td>{formatdate(emp.custom_driving_license_expiry_date, "dd-MM-yyyy")}</td>
			<td>{days}</td>
		</tr>
		"""

		if days == 45:
			tables["45"].append(row)
		elif days == 30:
			tables["30"].append(row)
		elif days == 15:
			tables["15"].append(row)

	def make_table(rows):
		if not rows:
			return ""

		return """
		<table class = "table table-bordered" style="font-size:12px;">
			<tr>
				<th>Employee</th>
				<th>Employee Name</th>
				<th>Company</th>
				<th>Location</th>
				<th>Driving License No.</th>
				<th>Expiry Date</th>
				<th>Days</th>
			</tr>
		""" + "".join(rows) + "</table>"

	email_map = {
		"45": "Action Required: Driving License Renewal Due in 45 Days !!!",
		"30": "Action Required: Driving License Renewal Due in 30 Days !!!",
		"15": "Action Required: Driving License Renewal Due in 15 Days !!!"
	}

	for key, subject in email_map.items():
		if not tables[key]:
			continue

		header = MAIL_HEADER.format(days=key)
		body = MAIL_BODY.format(days=key)
		table_html = make_table(tables[key])

		message=header + body + table_html
		make(
			recipients="hr1@tsl-me.com",
			cc = [
				"yousuf@tsl-me.com",
			],
			sender="no-reply@cyrix-tsl.com",
			reply_to="no-reply@cyrix-tsl.com",
			subject = subject,
			content = message,
			send_email=1
		)


def dafter_expiry_date():
	MAIL_HEADER = '''Dear Mam/Sir,<br><br>Dafter is expiring within {days} days for the below listed employees.<br><br>'''

	MAIL_BODY = '''This is to inform you that the Dafter of the below employee is due to expire in {days} Days.<br><br>
					HR is requested to initiate the dafter renewal process with the relevant authority in a timely manner to ensure continuity and compliance.<br><br>
					Once the renewal is completed, kindly obtain and file a scanned copy of the renewed Dafter in the employee records.<br><br>'''

	employees = frappe.db.get_list(
		"Employee",
		filters={"status": "Active"},
		fields=[
			"name", "employee_name", "company",
			"location", "dafter", "dafter_expiry_date"
		]
	)

	tables = {"45": [], "30": [], "15": []}
	today = getdate(nowdate())
	base_url = get_url()

	for emp in employees:
		if not emp.dafter_expiry_date or not emp.dafter:
			continue

		days = date_diff(emp.dafter_expiry_date, today)

		row = f"""
		<tr>
			<td><a href="{base_url}/app/employee/{emp.name}">{emp.name}</a></td>
			<td>{emp.employee_name}</td>
			<td>{emp.company}</td>
			<td>{emp.location or ""}</td>
			<td>{emp.dafter}</td>
			<td>{formatdate(emp.dafter_expiry_date, "dd-MM-yyyy")}</td>
			<td>{days}</td>
		</tr>
		"""

		if days == 45:
			tables["45"].append(row)
		elif days == 30:
			tables["30"].append(row)
		elif days == 15:
			tables["15"].append(row)

	def make_table(rows):
		if not rows:
			return ""

		return """
		<table class = "table table-bordered" style="font-size:12px;">
			<tr>
				<th>Employee</th>
				<th>Employee Name</th>
				<th>Company</th>
				<th>Location</th>
				<th>Dafter No.</th>
				<th>Expiry Date</th>
				<th>Days</th>
			</tr>
		""" + "".join(rows) + "</table>"

	email_map = {
		"45": "Action Required: Dafter Renewal Due in 45 Days !!!",
		"30": "Action Required: Dafter Renewal Due in 30 Days !!!",
		"15": "Action Required: Dafter Renewal Due in 15 Days !!!"
	}

	for key, subject in email_map.items():
		if not tables[key]:
			continue

		header = MAIL_HEADER.format(days=key)
		body = MAIL_BODY.format(days=key)
		table_html = make_table(tables[key])

		message=header + body + table_html
		make(
			recipients='hr1@tsl-me.com',
			cc = [
				"yousuf@tsl-me.com",
			],
			sender="no-reply@cyrix-tsl.com",
			reply_to="no-reply@cyrix-tsl.com",
			subject = subject,
			content = message,
			send_email=1
		)