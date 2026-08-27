# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import datetime
from frappe import _
from frappe.query_builder.functions import Max, Min, Sum
from frappe.utils import (
	add_days,
	cint,
	cstr,
	date_diff,
	flt,
	formatdate,
	get_fullname,
	get_link_to_form,
	getdate,
	nowdate,
	get_first_day,
	get_last_day
)

from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee


from frappe.utils.dateutils import get_from_date_from_timespan, get_period_ending
from frappe.utils import add_to_date, formatdate, get_link_to_form, getdate, nowdate

# Updates in Mail notification
from cyrix.custom_py.boot import get_bootinfo as info
from cyrix.custom_py.email_notification import sendmail

class LeaveApplicationForm(Document):
	def validate(self):
		self.travel_days = date_diff(self.to_date, self.from_date) + 1
		self.validate_applicable_after()
		self.validate_overlapping_leaves()
		
	def validate_overlapping_leaves(self):
		if not (self.employee and self.from_date and self.to_date):
			return

		conflicts = get_overlapping_leaves(
			employee=self.employee,
			from_date=getdate(self.from_date),
			to_date=getdate(self.to_date),
			exclude_name=self.name,
			docstatus=[1],  # approved / submitted only
		)

		if conflicts:
			conflict_links = ", ".join(
				get_link_to_form("Leave Application Form", c.name) for c in conflicts
			)
			frappe.throw(
				_(
					"{0} already has an approved leave application ({1}) "
					"that overlaps {2} to {3}."
				).format(
					frappe.bold(self.employee),
					conflict_links,
					formatdate(self.from_date),
					formatdate(self.to_date),
				),
				title=_("Overlapping Approved Leave"),
			)
	
	def validate_applicable_after(self):
		if self.leave_type:
			leave_type = frappe.get_doc("Leave Type", self.leave_type)
			if leave_type.applicable_after > 0:
				date_of_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")
				leave_days = get_approved_leaves_for_period(
					self.employee, False, date_of_joining, self.from_date
				)
				number_of_days = date_diff(getdate(self.from_date), date_of_joining)
				if number_of_days >= 0:
					holidays = 0
					if not frappe.db.get_value("Leave Type", self.leave_type, "include_holiday"):
						holidays = get_holidays_no(self.employee, date_of_joining, self.from_date)
					number_of_days = number_of_days - leave_days - holidays
					if number_of_days < leave_type.applicable_after:
						frappe.throw(
							_("{0} applicable after {1} working days").format(
								self.leave_type, leave_type.applicable_after
							)
						)

	def trigger_mail_on_submission(self):
		parent_doc = frappe.get_doc("Leave Application Form", self.name)
		args = parent_doc.as_dict()

		email_template = frappe.get_doc("Email Template", "Leave Application Approved")
		subject = frappe.render_template(email_template.subject, args)
		message = frappe.render_template(email_template.response, args)
		if self.user_id:
			try:
				sendmail(parent_doc, message, subject, sender = self.user_id, recipients = self.user_id, attachments = None, cc = None )
				frappe.msgprint(_("Email sent to {0}").format(self.user_id))
				
			except frappe.OutgoingEmailError:
				pass
		else:
			try:
				sendmail(parent_doc, message, subject, sender =  "no-reply@cyrix-tsl.com", recipients = self.user_id, attachments = None, cc = None )
				frappe.msgprint(_("Email sent to {0}").format(self.user_id))

			except frappe.OutgoingEmailError:
				pass
		
	# def on_trash(self):
	# 	exists = frappe.db.exists("Planned Leaves",{"reference":self.name})
	# 	frappe.delete_doc("Planned Leaves", exists, force=1)

	def on_cancel(self):
		exists = frappe.db.exists("Planned Leaves", {"reference": self.name})
		if exists:
			planned_leave = frappe.get_doc("Planned Leaves", exists)
			
			if planned_leave.docstatus == 0:  # Draft status
				frappe.delete_doc("Planned Leaves", exists, force=1)
			elif planned_leave.docstatus == 1:  # Submitted status
				planned_leave.cancel()  # Cancel the document
				frappe.delete_doc("Planned Leaves", exists, force=1)
		else:
			l_app = frappe.db.exists("Leave Application", {"reference": self.name})
			if l_app:
				leave_application = frappe.get_doc("Leave Application", l_app)
				
				if leave_application.docstatus == 0:  # Draft status
					frappe.delete_doc("Leave Application", l_app, force=1)
				elif leave_application.docstatus == 1:  # Submitted status
					leave_application.cancel()  # Cancel the document


	def on_submit(self):
		if self.workflow_state == "Approved":
			self.trigger_mail_on_submission()
		from datetime import datetime
		if self.leave_projection == 1 and self.from_date > datetime.now().date():
			pl = frappe.new_doc("Planned Leaves")
			fields = [field.fieldname for field in frappe.get_meta(self.doctype).fields 
					if field.fieldtype not in ['HTML', 'Button', 'Tab Break', 'Section Break', 'Column Break']
					and field.fieldname not in ["amended_from"]]
			for field in fields:
				setattr(pl, field, getattr(self, field))
			pl.reference = self.name
			pl.status = "Approved"
			pl.save(ignore_permissions=1)


		else:
			if self.leave_type != "Leave Without Pay":
				if self.lop_start_date:
					lop = frappe.new_doc("Leave Application")
					lop.employee = self.employee
					lop.from_date = self.lop_start_date
					lop.to_date = self.lop_end_date
					lop.description = self.description
					lop.reference = self.name
					lop.leave_type = "Leave Without Pay"
					lop.posting_date = self.posting_date
					if self.workflow_state == "Approved":
						lop.status = "Approved"
					else:
						lop.status = "Rejected"

					lop.follow_via_email = 0
					lop.save(ignore_permissions=1)
					lop.submit()

				l_ap = frappe.new_doc("Leave Application")
				l_ap.employee = self.employee
				l_ap.from_date = self.leave_start_date
				l_ap.to_date = self.leave_end_date
				l_ap.description = self.description
				l_ap.reference = self.name
				l_ap.leave_type = self.leave_type
				l_ap.posting_date = self.posting_date
				if self.workflow_state == "Approved":
					l_ap.status = "Approved"
				else:
					l_ap.status = "Rejected"

				l_ap.follow_via_email = 0
				l_ap.save(ignore_permissions =1)
				l_ap.submit()
			else:
				l_ap = frappe.new_doc("Leave Application")
				l_ap.employee = self.employee
				l_ap.from_date = self.from_date
				l_ap.to_date = self.to_date
				l_ap.description = self.description
				l_ap.reference = self.name
				l_ap.leave_type = self.leave_type
				l_ap.posting_date = self.posting_date
				if self.workflow_state == "Approved":
					l_ap.status = "Approved"
				else:
					l_ap.status = "Rejected"

				l_ap.follow_via_email = 0
				l_ap.save(ignore_permissions =1)
				l_ap.submit()

	# ########################
	# ##### Loan Details #####
	# ########################

	@frappe.whitelist()
	def show_loan_details(self):
		if self.leave_type not in ["Annual Leave"]:
			return ""
		rows = []

		for loan in self.get_loan_details():
			amounts = self.calculate_amounts(loan.name)

			for a in amounts:
				rows.append(f"""
					<tr>
						<td>{a.get("payment_date")}</td>
						<td>{a.get("loan")}</td>
						<td style="text-align:right;">{frappe.utils.fmt_money(a.get("amount"), 2)}</td>
					</tr>
				""")

		if not rows:
			return ""
		html = """<style>
			table.custom-bordered-table, 
			table.custom-bordered-table th, 
			table.custom-bordered-table td {
				border: 1px solid #000;
			}
			table.custom-bordered-table th, 
			table.custom-bordered-table td {
				padding: 8px;
				text-align: left;
			}
		</style>
		"""
		html += f"""
			<h4> Loan Repayment Schedule </h4>
			<table class="custom-bordered-table" style="width: 100%; border: 1px solid black; margin-top: 10px;">
				<thead>
					<tr>
						<th>Payment Date</th>
						<th>Loan</th>
						<th>Pending Amount</th>
					</tr>
				</thead>
				<tbody>
					{''.join(rows)}
				</tbody>
			</table>
			<br>
			<p style = "color:red; font-weight:bold" > Note : If needed, pause the loan during the Vacation period</p>
		"""

		return html



	@frappe.whitelist()
	def get_loan_details(self):
		loan_details = frappe.get_all(
			"Loan Request",
			fields=["name", "loan_product", "is_term_loan"],
			filters={
				"employee": self.employee,
				"docstatus": 1,
				"repay_from_salary": 1,
				"company": self.company,
				"status": ("!=", "Closed"),
			},
		)
		return loan_details

	@frappe.whitelist()
	def calculate_amounts(self, loan):
		data = []
		schedule_entries = frappe.get_all(
			"Loan Request Repayment Schedule",
			filters={
				"parent": loan,
				"payment_date": ("between", (get_first_day(self.from_date),get_last_day(self.to_date))),
				"is_accrued": 0
			},
			fields=["name","total_payment","paid_amount","payment_date"]
		)

		for entry in schedule_entries:
			pending = (entry.total_payment or 0) - (entry.paid_amount or 0)

			link_to_loan = f"""<a href="/app/loan-request/{loan}" target="_blank">
				{loan}
			</a>"""

			if pending > 0:
				data.append({
					"payment_date":entry.payment_date,
					"loan": link_to_loan,
					"amount": pending
				})
		return data


	
@frappe.whitelist()
def get_dates_from_timegrain(from_date, to_date, timegrain, holidays, company):
	days = months = years = 0

	if timegrain == "Daily":
		days = 1

	# Normalize holidays to date objects
	holiday_dates = {getdate(h) for h in holidays or []}

	dates = []
	current_date = get_period_ending(from_date, timegrain)

	while getdate(current_date) <= getdate(to_date):
		# Skip if holiday
		if company != "Cyrix TSL - Kuwait":
			if getdate(current_date) not in holiday_dates:
				dates.append(current_date)
		else:
			dates.append(current_date)

		# Move to next period
		current_date = get_period_ending(
			add_to_date(current_date, years=years, months=months, days=days),
			timegrain
		)

	return dates

def get_holidays(employee, from_date, to_date, holiday_list=None):
	"""Get holidays between two dates for the given employee."""
	if not holiday_list:
		holiday_list = get_holiday_list_for_employee(employee)
	holidays = frappe.db.sql(
		"""select distinct holiday_date from `tabHoliday` h1, `tabHoliday List` h2
		where h1.parent = h2.name and h1.holiday_date between %s and %s
		and h2.name = %s and h1.weekly_off = 0 order by h1.holiday_date """,
		(from_date, to_date, holiday_list), as_dict=1
	)
	return [holiday['holiday_date'] for holiday in holidays]

@frappe.whitelist()
def get_roles(user_id):
	if "Leave Approver" in frappe.get_roles(user_id):
		return True
	else:
		return False

@frappe.whitelist()
def trigger_mail(name,workflow_state = None,email = None,leave_approver = None,hr_mail = None):
	if leave_approver:
		parent_doc = frappe.get_doc("Leave Application Form", name)
		args = parent_doc.as_dict()

		email_template = frappe.get_doc("Email Template", "Leave Approval Notification - Line Manager")
		subject = frappe.render_template(email_template.subject, args)
		message = frappe.render_template(email_template.response, args)

		if parent_doc.leave_type in ["Annual Leave"]:
			cc = info().get("hr_to").get(parent_doc.company)
		else:
			cc = info().get("hr_cc").get(parent_doc.company)

		try:
			sendmail(parent_doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = leave_approver, attachments = None, cc = cc )
			frappe.msgprint(_("Email sent to {0}").format(leave_approver))

		except frappe.OutgoingEmailError:
			pass
	else:
		parent_doc = frappe.get_doc("Leave Application Form", name)
		args = parent_doc.as_dict()

		email_template = frappe.get_doc("Email Template", "Leave Approval Notification - CEO")
		subject = frappe.render_template(email_template.subject, args)
		message = frappe.render_template(email_template.response, args)
		
		if parent_doc.leave_type in ["Annual Leave"]:
			cc = info().get("hr_to").get(parent_doc.company)
		else:
			cc = info().get("hr_cc").get(parent_doc.company)

		try:
			sendmail(parent_doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = email, attachments = None, cc = cc )
			frappe.msgprint(_("Email sent to {0}").format(email))
			
		except frappe.OutgoingEmailError:
			pass
			
@frappe.whitelist()
def trigger_mail_to_hr(name,workflow_state = None,company = None,leave_approver = None):
	doc = frappe.get_doc("Leave Application Form", name)
	args = {
		"cyrix":1,
		"employee_name":doc.employee_name,
		"employee":doc.employee,
		"department": frappe.db.get_value("Employee",doc.employee,"department") or '-',
		"branch": frappe.db.get_value("Employee",doc.employee,"branch") or '-',
		"nationality": frappe.db.get_value("Employee",doc.employee,"nationality") or '-',
		"valid_upto": frappe.db.get_value("Employee",doc.employee,"valid_upto") or '-',
		"leave_type":doc.leave_type or '-',
		"from_date":doc.from_date or '-',
		"to_date":doc.to_date or '-',
		"no_of_days":doc.no_of_days or '-',
		"reason":doc.description or '-',
	}

	email_template = frappe.get_doc("Email Template", "Leave Approval Notification - HR")
	subject = frappe.render_template(email_template.subject, args)
	message = frappe.render_template(email_template.response, args)
	
	if doc.leave_type in ["Annual Leave"]:
		recipents = info().get("hr_to").get(company)
	else:
		recipents = info().get("hr_cc").get(company)

	try:
		sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = recipents, attachments = None )
		frappe.msgprint(_("Email sent to {0}").format(recipents))
	except frappe.OutgoingEmailError:
		pass

@frappe.whitelist()
def validate_balance_leaves(company,from_date,to_date,employee,leave_type,half_day = None,half_day_date = None):
	holiday_list = frappe.db.get_value("Employee",employee,'holiday_list') or None
	total_leave_days = get_number_of_leave_days(
		company,
		employee,
		leave_type,
		from_date,
		to_date,
		half_day,
		half_day_date,
		holiday_list
	)
	return total_leave_days


@frappe.whitelist()
def validate_balance_leaves_lop(company,from_date,to_date,employee,leave_type,half_day = None,half_day_date = None):
	holiday_list = frappe.db.get_value("Employee",employee,'holiday_list') or None
	total_leave_days = get_number_of_leave_days_lop(
		company,
		employee,
		leave_type,
		from_date,
		to_date,
		half_day,
		half_day_date,
		holiday_list
	)
	return total_leave_days


@frappe.whitelist()
def get_number_of_leave_days(
	company:str,
	employee: str,
	leave_type: str,
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
	if company == "Cyrix TSL - Kuwait":
		number_of_days = flt(number_of_days)
	else:
		number_of_days = flt(number_of_days) - flt(
			get_holidays_no(employee, from_date, to_date, holiday_list=holiday_list, company=company)
		)
	return number_of_days

@frappe.whitelist()
def get_number_of_leave_days_lop(
	company:str,
	employee: str,
	leave_type: str,
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

	######################################################
	# Holidays within the period will be involved in LWP #
	############# Holidays will be excluded ##############
	######################################################

	# number_of_days = flt(number_of_days) - flt(
	# 	get_holidays_no(employee, from_date, to_date, holiday_list=holiday_list, company=company)
	# )

	return number_of_days

def get_holidays_no(employee, from_date, to_date, holiday_list=None, company = None):
	"""get holidays between two dates for the given employee"""
	if not holiday_list:
		holiday_list = get_holiday_list_for_employee(employee)

	holidays = frappe.db.sql(
		"""select count(distinct holiday_date) from `tabHoliday` h1, `tabHoliday List` h2
		where h1.parent = h2.name and h1.holiday_date between %s and %s
		and h2.name = %s and h1.weekly_off = 0 """,
		(from_date, to_date, holiday_list),
	)[0][0]

	return holidays

@frappe.whitelist()
def list_leave_dates(employee, from_date, to_date,leave_type,leave_balance,company):
	holidays = get_holidays(employee, from_date, to_date)
	dates = get_dates_from_timegrain(from_date, to_date, "Daily", holidays,company)
	if len(dates) > int(leave_balance):
		if frappe.db.exists("Leave Allocation",{"from_date": ["<=", from_date],"employee":employee,"leave_type":leave_type,"docstatus":1}):
			leave_days = int(leave_balance) or 0
			leave_start_date = dates[0]
			leave_end_date = dates[leave_days]
			return leave_start_date ,leave_end_date
	

@frappe.whitelist()
def trigger_mail_on_lap_form():
	current_date = nowdate()
	leaves = frappe.db.get_all("Leave Application Form",{'from_date':current_date,"leave_type":"Annual Leave","status":"Approved"},['*'])
	for self in leaves:
		parent_doc = frappe.get_doc("Leave Application Form", self.name)
		args = parent_doc.as_dict()
		email_template = frappe.get_doc("Email Template", "Employee Travelling Today")
		subject = frappe.render_template(email_template.subject, args)
		message = frappe.render_template(email_template.response, args)
		try:
			sendmail(parent_doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = "alkouh@tsl-me.com", attachments = None, cc = None )

		except frappe.OutgoingEmailError:
			pass

def schedule_trigger_mail_on_lap_form():
	job1 = frappe.db.exists('Scheduled Job Type', 'leave_application_form.trigger_mail_on_lap_form')
	if not job1:
		sjt1 = frappe.new_doc("Scheduled Job Type")  
		sjt1.update({
			"method" : 'cyrix.cyrix_tsl.doctype.leave_application_form.leave_application_form.trigger_mail_on_lap_form',
			"frequency" : 'Daily'
		})
		sjt1.save(ignore_permissions=True)

	job2 = frappe.db.exists('Scheduled Job Type', 'leave_application.create_leave_rejoining')
	if not job2:
		sjt2 = frappe.new_doc("Scheduled Job Type")  
		sjt2.update({
			"method" : 'cyrix.cyrix_tsl.doctype.leave_application_form.leave_application_form.create_leave_rejoining',
			"frequency" : 'Daily'
		})
		sjt2.save(ignore_permissions=True)

def get_approved_leaves_for_period(employee, leave_type, from_date, to_date):
	LeaveApplication = frappe.qb.DocType("Leave Application Form")
	query = (
		frappe.qb.from_(LeaveApplication)
		.select(
			LeaveApplication.employee,
			LeaveApplication.leave_type,
			LeaveApplication.from_date,
			LeaveApplication.to_date,
			LeaveApplication.total_leave_days,
		)
		.where(
			(LeaveApplication.employee == employee)
			& (LeaveApplication.docstatus == 1)
			& (LeaveApplication.status == "Approved")
			& (
				(LeaveApplication.from_date.between(from_date, to_date))
				| (LeaveApplication.to_date.between(from_date, to_date))
				| ((LeaveApplication.from_date < from_date) & (LeaveApplication.to_date > to_date))
			)
		)
	)

	if leave_type:
		query = query.where(LeaveApplication.leave_type == leave_type)

	leave_applications = query.run(as_dict=True)

	leave_days = 0
	for leave_app in leave_applications:
		if leave_app.from_date >= getdate(from_date) and leave_app.to_date <= getdate(to_date):
			leave_days += leave_app.total_leave_days
		else:
			if leave_app.from_date < getdate(from_date):
				leave_app.from_date = from_date
			if leave_app.to_date > getdate(to_date):
				leave_app.to_date = to_date

			leave_days += get_number_of_leave_days(
				employee, leave_type, leave_app.from_date, leave_app.to_date
			)

	return leave_days

@frappe.whitelist()
def return_last_rejoined_date(employee):
	last_rejoined = frappe.db.get_value("Leave Rejoining Form", filters={"emp_no": employee}, fieldname="actual_rejoining_date", order_by="actual_rejoining_date desc")
	if not last_rejoined:
		last_rejoined = frappe.db.get_value("Leave Rejoining Form", filters={"emp_no": employee}, fieldname="rejoining_date", order_by="rejoining_date desc")
	return last_rejoined


def update_pl():
	self = frappe.get_doc("Leave Application Form","HR-LAP-2026-00028")
	pl = frappe.new_doc("Planned Leaves")
	fields = [field.fieldname for field in frappe.get_meta(self.doctype).fields 
			if field.fieldtype not in ['HTML', 'Button', 'Tab Break', 'Section Break', 'Column Break']
			and field.fieldname not in ["amended_from"]]
	for field in fields:
		setattr(pl, field, getattr(self, field))
	pl.reference = self.name
	pl.status = "Approved"
	pl.save(ignore_permissions=1)


# @frappe.whitelist()
# def show_loan_details():
# 	self = frappe.get_doc("Leave Application Form","HR-LAP-2025-00591")
# 	if self.leave_type not in ["Annual Leave"]:
# 		return ""
# 	rows = []

# 	for loan in get_loan_details(self):
# 		amounts = calculate_amounts(self,loan.name)

# 		for a in amounts:
# 			rows.append(f"""
# 				<tr>
# 					<td>{a.get("payment_date")}</td>
# 					<td>{a.get("loan")}</td>
# 					<td style="text-align:right;">{frappe.utils.fmt_money(a.get("amount"), 2)}</td>
# 				</tr>
# 			""")

# 	if not rows:
# 		return ""
# 	html = """<style>
# 		table.custom-bordered-table, 
# 		table.custom-bordered-table th, 
# 		table.custom-bordered-table td {
# 			border: 1px solid #000;
# 		}
# 		table.custom-bordered-table th, 
# 		table.custom-bordered-table td {
# 			padding: 8px;
# 			text-align: left;
# 		}
# 	</style>
# 	"""
# 	html += f"""
# 		<h4> Loan Repayment Schedule </h4>
# 		<table class="custom-bordered-table" style="width:50%; border: 1px solid black; margin-top: 10px;">
# 			<thead>
# 				<tr>
# 					<th>Payment Date</th>
# 					<th>Loan</th>
# 					<th>Pending Amount</th>
# 				</tr>
# 			</thead>
# 			<tbody>
# 				{''.join(rows)}
# 			</tbody>
# 		</table>
# 		<br>
# 		<p style = "color:red; font-weight:bold" > Note : If needed, pause the loan during the Vacation period</p>
# 	"""

# 	return html



@frappe.whitelist()
def get_loan_details(self):
	loan_details = frappe.get_all(
		"Loan Request",
		fields=["name", "loan_product", "is_term_loan"],
		filters={
			"employee": self.employee,
			"docstatus": 1,
			"repay_from_salary": 1,
			# "company": self.company,
			"status": ("!=", "Closed"),
		},
	)
	print(loan_details)

	return loan_details

@frappe.whitelist()
def calculate_amounts(self, loan):
	data = []
	schedule_entries = frappe.get_all(
		"Loan Request Repayment Schedule",
		filters={
			"parent": loan,
			"payment_date": ("between", (get_first_day(self.from_date),get_last_day(self.to_date))),
			"is_accrued": 0
		},
		fields=["name","total_payment","paid_amount","payment_date"]
	)

	for entry in schedule_entries:
		pending = (entry.total_payment or 0) - (entry.paid_amount or 0)

		link_to_loan = f"""<a href="/app/loan-request/{loan}" target="_blank">
			{loan}
		</a>"""

		if pending > 0:
			data.append({
				"payment_date":entry.payment_date,
				"loan": link_to_loan,
				"amount": pending
			})
	return data

def get_overlapping_leaves(employee, from_date, to_date, exclude_name=None, docstatus=None):
	if docstatus is None:
		docstatus = [0, 1]

	filters = {
		"employee": employee,
		"docstatus": ["in", docstatus],
		"from_date": ["<=", to_date],
		"to_date": [">=", from_date],
	}
	if exclude_name:
		filters["name"] = ["!=", exclude_name]

	return frappe.get_all(
		"Leave Application Form",
		filters=filters,
		fields=["name", "employee", "from_date", "to_date", "docstatus"],
		order_by="from_date asc",
	)


@frappe.whitelist()
def check_date_conflicts(employee, from_date, to_date, name=None):
	"""
	Whitelisted endpoint used by the client script (requirement 3).
	Returns any DRAFT or APPROVED application for this employee that
	overlaps the given dates, excluding the current doc. Does NOT
	throw - this is informational only, used to render a banner.
	"""
	if not (employee and from_date and to_date):
		return []

	# ignore unsaved-doc temp names like "new-custom-leave-application-1"
	if name and name.startswith("new-"):
		name = None

	conflicts = get_overlapping_leaves(
		employee=employee,
		from_date=getdate(from_date),
		to_date=getdate(to_date),
		exclude_name=name,
		docstatus=[0, 1],
	)

	for c in conflicts:
		c["status_label"] = "Approved" if c.docstatus == 1 else "Draft"

	return conflicts

from datetime import datetime, timedelta
@frappe.whitelist()
def calculate_projected_leaves(employee,current_date, leave_start_date):
	current_date = datetime.strptime(current_date,"%Y-%m-%d")
	leave_start_date = datetime.strptime(leave_start_date,"%Y-%m-%d")
	if leave_start_date <= current_date:
		return 0.0  # No projection needed for past or today

	eligible_annual_leaves = frappe.db.get_value("Employee",employee,'monthly_eligible_days')
	monthly_leave_allocation = eligible_annual_leaves
	projected_leaves = 0.0
	days_until_leave = (leave_start_date - current_date).days
	
	for day in range(days_until_leave):
		projection_date = current_date + timedelta(days=day)
		
		if projection_date.month == 2:
			days_in_month = 29 if (projection_date.year % 4 == 0 and (projection_date.year % 100 != 0 or projection_date.year % 400 == 0)) else 28
		else:
			from calendar import monthrange
			days_in_month = monthrange(projection_date.year, projection_date.month)[1]

		if days_in_month > 0:
			projected_leaves += (monthly_leave_allocation / days_in_month)
		else:
			projected_leaves += 0  # Just in case, although days_in_month should never be 0

	return round(projected_leaves,3)



@frappe.whitelist()
def create_leave_rejoining():
	rejoining_required = frappe.db.get_all("Leave Type",{"rejoining_required":1}, ['name'])
	rejoining_required_types = [r.name for r in rejoining_required]
	if not rejoining_required_types:
		return
	leave_applications = frappe.db.get_all("Leave Application Form",{"docstatus":1, "leave_type": ["in", rejoining_required_types]}, ['*'])
	today_date = datetime.today().date() 

	for leave in leave_applications:
		leave_end_date = leave.leave_end_date
		lop_end_date = leave.lop_end_date

		# Check if leave has ended today
		if (leave_end_date and not lop_end_date and leave_end_date == today_date) or (lop_end_date and lop_end_date == today_date):
			# Check if rejoining form already exists
			if not frappe.db.exists("Leave Rejoining Form", {'leave_application': leave.name, "emp_no": leave.employee}):
				try:
					rejoin = frappe.new_doc("Leave Rejoining Form")
					rejoin.emp_no = leave.employee
					rejoin.leave_application = leave.name
					rejoin.from_date = leave.from_date
					rejoin.to_date = leave.to_date
					rejoin.rejoining_date = add_days(today_date, 1) 
					rejoin.save()
				except Exception as e:
					print(f"Error creating rejoining form for {leave.employee}: {e}")