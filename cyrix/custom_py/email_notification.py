import frappe
import calendar
from frappe.core.doctype.communication.email import _make as make_communication, make
from frappe.utils import nowdate, date_diff, add_years, add_days, today, getdate,get_url_to_form
from cyrix.custom_py.boot import get_bootinfo as info
from frappe import _
from datetime import datetime

@frappe.whitelist()
def schedule_email_notifications():
	anniversary = frappe.db.exists('Scheduled Job Type', 'email_notification.send_advance_work_anniversary_reminders')
	if not anniversary:
		sjt1 = frappe.new_doc("Scheduled Job Type")  
		sjt1.update({
			"method" : 'cyrix.custom_py.email_notification.send_advance_work_anniversary_reminders',
			"frequency" : 'Daily',
		})
		sjt1.save(ignore_permissions=True)

	probation = frappe.db.exists('Scheduled Job Type', 'email_notification.send_probation_reminder')
	if not probation:
		sjt2 = frappe.new_doc("Scheduled Job Type")  
		sjt2.update({
			"method" : 'cyrix.custom_py.email_notification.send_probation_reminder',
			"frequency" : 'Daily',
		})
		sjt2.save(ignore_permissions=True)

	travel_reminder = frappe.db.exists('Scheduled Job Type', 'email_notification.send_travel_reminders')
	if not travel_reminder:
		sjt3 = frappe.new_doc("Scheduled Job Type")  
		sjt3.update({
			"method" : 'cyrix.custom_py.email_notification.send_travel_reminders',
			"frequency" : 'Daily',
		})
		sjt3.save(ignore_permissions=True)

	relieving = frappe.db.exists('Scheduled Job Type', 'email_notification.reminder_on_relieving')
	if not relieving:
		sjt4 = frappe.new_doc("Scheduled Job Type")  
		sjt4.update({
			"method" : 'cyrix.custom_py.email_notification.reminder_on_relieving',
			"frequency" : 'Daily',
		})
		sjt4.save(ignore_permissions=True)

	unapproved_leaves = frappe.db.exists('Scheduled Job Type', 'email_notification.unapproved_leaves_reminder')
	if not unapproved_leaves:
		sjt5 = frappe.new_doc("Scheduled Job Type")  
		sjt5.update({
			"method" : 'cyrix.custom_py.email_notification.unapproved_leaves_reminder',
			"frequency" : 'Daily',
		})
		sjt5.save(ignore_permissions=True)

	hr_birthday = frappe.db.exists('Scheduled Job Type', 'birthday_reminder.send_birthday_reminder_hr')
	if not hr_birthday:
		sjt6 = frappe.new_doc("Scheduled Job Type")  
		sjt6.update({
			"method" : 'cyrix.custom_py.email_notification.send_birthday_reminder_hr',
			"frequency" : 'Daily',
		})
		sjt6.save(ignore_permissions=True)

	birthday = frappe.db.exists('Scheduled Job Type', 'birthday_reminder.send_birthday_reminder')
	if not birthday:
		sjt7 = frappe.new_doc("Scheduled Job Type")  
		sjt7.update({
			"method" : 'cyrix.custom_py.email_notification.send_birthday_reminder',
			"frequency" : 'Daily',
		})
		sjt7.save(ignore_permissions=True)

@frappe.whitelist()
def sendmail(self, message = None, subject = None, sender = None, recipients = None, attachments = None, cc = None):
	communication = make_communication(
		doctype=get_reference_doctype(self),
		name=get_reference_name(self),
		content=message,
		subject=subject,
		sender=sender,
		recipients=recipients,
		communication_medium="Email",
		send_email=False,
		attachments=attachments,
		cc=cc,
		bcc=None,
		communication_type="Automated Message",
	).get("name")

	frappe.sendmail(
		recipients=recipients,
		subject=subject,
		sender=sender,
		cc=cc,
		bcc=None,
		message=message,
		reference_doctype=get_reference_doctype(self),
		reference_name=get_reference_name(self),
		attachments=attachments,
		expose_recipients="header",
		print_letterhead=((attachments and attachments[0].get("print_letterhead")) or False),
		communication=communication,
	)

def get_reference_doctype(doc):
	return doc.parenttype if doc.meta.istable else doc.doctype

def get_reference_name(doc):
	return doc.parent if doc.meta.istable else doc.name


#################################################
######### Work Anniversary Reminder #############
#################################################

def send_advance_work_anniversary_reminders():
	today = nowdate()
	milestones = [5, 10, 15, 20, 25]
	reminder_days = [15, 10, 5]

	# Fetch email template
	template = frappe.get_doc("Email Template", "Work Anniversary Reminder")
	
	# Get all active employees
	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active", "date_of_joining": ["is", "set"]},
		fields=[
			"company",
			"name",
			"employee_name",
			"date_of_joining",
			"department",
			"designation",
		],
	)

	for emp in employees:
		for year in milestones:
			milestone_date = add_years(emp.date_of_joining, year)
			days_left = date_diff(milestone_date, today)

			if days_left in reminder_days:
				context = {
					"doc":emp,
					"employee": emp.name,
					"employee_name": emp.employee_name,
					"department": emp.department,
					"designation": emp.designation,
					"years": year,
					"days_left": days_left,
				}

				make(
					recipients=info().get("hr_to").get(emp.company),
					cc = info().get("hr_cc").get(emp.company),
					sender="no-reply@cyrix-tsl.com",
					reply_to="no-reply@cyrix-tsl.com",
					subject = frappe.render_template(template.subject, context),
					content = frappe.render_template(template.response_html, context),
					send_email=1
				)

				break  # prevent duplicate mail per employee

#################################################
######### Rejoining Mail Notification ###########
#################################################

def send_mail_on_rejoining_creation(doc,method):
	if doc.company in ["Company Al-Halloul Faniye Medical"]:
		url = "To View {0} <a href='{1}'>Click Here</a>".format(doc.doctype,get_url_to_form(doc.doctype,doc.name))
		leave_type = frappe.db.get_value("Leave Application Form",doc.leave_application,"leave_type")
		args = {
			"url":url,
			"employee":doc.emp_no,
			"employee_name":doc.employee_name,
			"branch": frappe.db.get_value("Employee",doc.emp_no,"branch") or '-',
			"department": frappe.db.get_value("Employee",doc.emp_no,"department") or '-',
			"rejoining_date":doc.rejoining_date,
			"nationality": frappe.db.get_value("Employee",doc.emp_no,"nationality") or '-',
			"designation": frappe.db.get_value("Employee",doc.emp_no,"designation") or '-',
			"travel_date": frappe.db.get_value("Leave Application Form",doc.leave_application,"travel_date") or frappe.db.get_value("Leave Application Form",doc.leave_application,"from_date"),
			"leave_type": frappe.db.get_value("Leave Application Form",doc.leave_application,"leave_type") or '-',
			"return_date": frappe.db.get_value("Leave Application Form",doc.leave_application,"return_date") or frappe.db.get_value("Leave Application Form",doc.leave_application,"to_date"),
		}
		email_template = frappe.get_doc("Email Template", "Employee Rejoining")
		subject = frappe.render_template(email_template.subject, args)
		message = frappe.render_template(email_template.response, args)

		sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = info().get("hr_cc").get(frappe.db.get_value("Employee",doc.emp_no,"company")), attachments = None )



#################################################
######## Resignation Mail Notification ##########
#################################################

def send_mail_on_resignation_creation(doc,method):
	url = "To View {0} <a href='{1}'>Click Here</a>".format(doc.doctype,get_url_to_form(doc.doctype,doc.name))
	args = {
		"url":url,
		"employee":doc.employee,
		"employee_name":doc.employee_name,
		"branch": frappe.db.get_value("Employee",doc.employee,"branch") or '-',
		"department": frappe.db.get_value("Employee",doc.employee,"department") or '-',
		"nationality": frappe.db.get_value("Employee",doc.employee,"nationality") or '-',
		"designation": frappe.db.get_value("Employee",doc.employee,"designation") or '-',
		"relieving_date":doc.relieving_date,
		"posting_date":doc.posting_date,
		"reason":doc.reason or '-',
	}

	email_template = frappe.get_doc("Email Template", "Resignation Form")
	subject = frappe.render_template(email_template.subject, args)
	message = frappe.render_template(email_template.response, args)

	sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = info().get("hr_to").get(doc.company), attachments = None, cc =  info().get("hr_cc").get(doc.company) )

def test():
	print(get_url_to_form("Leave Application Form","HR-LAP-2026-00001"))


#################################################
######## Termination Mail Notification ##########
#################################################

def send_mail_on_termination_creation(doc,method):
	url = "To View {0} <a href='{1}'>Click Here</a>".format(doc.doctype,get_url_to_form(doc.doctype,doc.name))
	args = {
		"url":url,
		"employee":doc.employee,
		"employee_name":doc.employee_name,
		"branch": frappe.db.get_value("Employee",doc.employee,"branch") or '-',
		"department": frappe.db.get_value("Employee",doc.employee,"department") or '-',
		"nationality": frappe.db.get_value("Employee",doc.employee,"nationality") or '-',
		"designation": frappe.db.get_value("Employee",doc.employee,"designation") or '-',
		"hods_relieving_date":doc.hods_relieving_date,
		"reason":doc.reason or '-',
	}

	email_template = frappe.get_doc("Email Template", "Termination Form")
	subject = frappe.render_template(email_template.subject, args)
	message = frappe.render_template(email_template.response, args)

	sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = info().get("hr_to").get(doc.company), attachments = None, cc =  info().get("hr_cc").get(doc.company) )


#################################################
########### Leave Salary Notification ###########
#################################################

@frappe.whitelist()
def send_mail_on_leave_salary(name):
	doc = frappe.get_doc("Leave Salary", name)
	url = "To View {0} <a href='{1}'>Click Here</a>".format(doc.doctype, get_url_to_form(doc.doctype, doc.name))
	company = frappe.db.get_value("Employee", doc.employee, "company")

	args = {
		"url": url,
		"employee": doc.employee,
		"employee_name": doc.employee_name,
		"total_released_amount": doc.get("total_released_amount") or 0,
		"branch": frappe.db.get_value("Employee", doc.employee, "branch") or '-',
		"department": frappe.db.get_value("Employee", doc.employee, "department") or '-',
		"nationality": frappe.db.get_value("Employee", doc.employee, "nationality") or '-',
		"designation": frappe.db.get_value("Employee", doc.employee, "designation") or '-',
	}

	email_template = frappe.get_doc("Email Template", "Leave Salary")
	subject = frappe.render_template(email_template.subject, args)
	message = frappe.render_template(email_template.response, args)

	# Remove restricted email
	cc_list = info().get("hr_to").get(company)
	cc_list = [email for email in cc_list if email != "hr1@tsl-me.com"]

	sendmail(
		doc,
		message,
		subject,
		sender="no-reply@cyrix-tsl.com",
		recipients=info().get("finance_to").get(company),
		attachments=None,
		cc=cc_list
	)

	frappe.msgprint(_("Email sent to {0}").format(info().get("finance_to").get(company)))

#################################################
#### Full and Final Settlement Notification #####
#################################################

@frappe.whitelist()
def send_mail_on_fnf(name):
	doc = frappe.get_doc("Full and Final Settlement",name)
	url = "To View {0} <a href='{1}'>Click Here</a>".format(doc.doctype,get_url_to_form(doc.doctype,doc.name))
	company = frappe.db.get_value("Employee",doc.employee,"company")
	args = {
		"url":url,
		"employee":doc.employee,
		"employee_name":doc.employee_name,
		"net_pay":doc.get("net_pay") or 0,
		"branch": frappe.db.get_value("Employee",doc.employee,"branch") or '-',
		"department": frappe.db.get_value("Employee",doc.employee,"department") or '-',
		"nationality": frappe.db.get_value("Employee",doc.employee,"nationality") or '-',
		"designation": frappe.db.get_value("Employee",doc.employee,"designation") or '-',
	}

	email_template = frappe.get_doc("Email Template", "Full and Final Settlement")
	subject = frappe.render_template(email_template.subject, args)
	message = frappe.render_template(email_template.response, args)

	sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = info().get("finance_to").get(company), attachments = None, cc =  None )
	frappe.msgprint(_("Email sent to {0}").format(info().get("finance_to").get(company)))


#################################################
####### Fnf Rejection Mail Notification #########
#################################################

@frappe.whitelist()
def send_fnf_rejection_mail(name, rejection_reason):
	doc = frappe.get_doc("Full and Final Settlement",name)
	url = "To View {0} <a href='{1}'>Click Here</a>".format(doc.doctype,get_url_to_form(doc.doctype,doc.name))
	company = frappe.db.get_value("Employee",doc.employee,"company")
	args = {
		"url":url,
		"employee":doc.employee,
		"employee_name":doc.employee_name,
		"net_pay":doc.get("net_pay") or 0,
		"branch": frappe.db.get_value("Employee",doc.employee,"branch") or '-',
		"department": frappe.db.get_value("Employee",doc.employee,"department") or '-',
		"nationality": frappe.db.get_value("Employee",doc.employee,"nationality") or '-',
		"designation": frappe.db.get_value("Employee",doc.employee,"designation") or '-',
		"rejection_reason":rejection_reason or '-'
	}

	email_template = frappe.get_doc("Email Template", "Final Settlement Rejected")
	subject = frappe.render_template(email_template.subject, args)
	message = frappe.render_template(email_template.response, args)

	sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = info().get("hr_to").get(company), attachments = None, cc =  None )
	frappe.msgprint(_("Email sent to {0}").format(info().get("hr_to").get(company)))


#################################################
########## Loan Request Notification ############
#################################################

@frappe.whitelist()
def send_mail_on_loan_request(name, role):
	doc = frappe.get_doc("Loan Request",name)
	url = "To View {0} <a href='{1}'>Click Here</a>".format(doc.doctype,get_url_to_form(doc.doctype,doc.name))
	company = frappe.db.get_value("Employee",doc.employee,"company")
	args = {
		"url":url,
		"employee":doc.employee,
		"employee_name":doc.employee_name,
		"loan_amount":doc.get("loan_amount") or 0,
		"repayment_periods":doc.get("repayment_periods") or 0,
		"reason":doc.get("reason") or '-',
		"branch": frappe.db.get_value("Employee",doc.employee,"branch") or '-',
		"department": frappe.db.get_value("Employee",doc.employee,"department") or '-',
		"nationality": frappe.db.get_value("Employee",doc.employee,"nationality") or '-',
		"designation": frappe.db.get_value("Employee",doc.employee,"designation") or '-',
	}

	if role == "HR":
		email_template = frappe.get_doc("Email Template", "Loan Application - HR")
		subject = frappe.render_template(email_template.subject, args)
		message = frappe.render_template(email_template.response, args)
			
		sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = info().get("hr_to").get(company), attachments = None, cc =  None )
		frappe.msgprint(_("Email sent to {0}").format(info().get("hr_to").get(company)))

	else:
		email_template = frappe.get_doc("Email Template", "Loan Application - Finance")
		subject = frappe.render_template(email_template.subject, args)
		message = frappe.render_template(email_template.response, args)

		sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = info().get("finance_to").get(company), attachments = None, cc =  None )
		frappe.msgprint(_("Email sent to {0}").format(info().get("finance_to").get(company)))


#################################################
########## Loan Rejection Notification ##########
#################################################

@frappe.whitelist()
def send_loan_rejection_mail(name, rejection_reason):
	doc = frappe.get_doc("Loan Request",name)
	url = "To View {0} <a href='{1}'>Click Here</a>".format(doc.doctype,get_url_to_form(doc.doctype,doc.name))
	user = frappe.db.get_value("Employee",doc.employee, 'user_id') or frappe.db.get_value("Employee",doc.employee, 'company_email') or frappe.db.get_value("Employee",doc.employee, 'personal_email')
	
	args = {
		"url":url,
		"employee_name":doc.employee_name,
		"loan_amount":doc.get("loan_amount") or 0,
		"repayment_periods":doc.get("repayment_periods") or 0,
		"reason":doc.get("reason") or '-',
		"rejection_reason":rejection_reason or '-'
	}

	email_template = frappe.get_doc("Email Template", "Loan Application Rejected")
	subject = frappe.render_template(email_template.subject, args)
	message = frappe.render_template(email_template.response, args)
		
	sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = user, attachments = None, cc =  None )
	frappe.msgprint(_("Email sent to {0}").format(user))

#################################################
######## Employee Advance Notification ##########
#################################################

@frappe.whitelist()
def send_mail_on_employee_advance(name):
	doc = frappe.get_doc("Employee Advance",name)
	url = "To View {0} <a href='{1}'>Click Here</a>".format(doc.doctype,get_url_to_form(doc.doctype,doc.name))
	company = frappe.db.get_value("Employee",doc.employee,"company")
	args = {
		"url":url,
		"employee":doc.employee,
		"employee_name":doc.employee_name,
		"advance_amount":doc.get("advance_amount") or 0,
		"purpose":doc.get("purpose") or '-',
		"branch": frappe.db.get_value("Employee",doc.employee,"branch") or '-',
		"department": frappe.db.get_value("Employee",doc.employee,"department") or '-',
		"nationality": frappe.db.get_value("Employee",doc.employee,"nationality") or '-',
		"designation": frappe.db.get_value("Employee",doc.employee,"designation") or '-',
	}

	email_template = frappe.get_doc("Email Template", "Employee Advance - Finance")
	subject = frappe.render_template(email_template.subject, args)
	message = frappe.render_template(email_template.response, args)

	sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = info().get("finance_to").get(company), attachments = None, cc =  None )
	frappe.msgprint(_("Email sent to {0}").format(info().get("finance_to").get(company)))


#################################################
######## Leave Encashment Notification ##########
#################################################

@frappe.whitelist()
def send_mail_on_leave_encashment(name, role):
	doc = frappe.get_doc("Leave Encashment Data",name)
	url = "To View {0} <a href='{1}'>Click Here</a>".format(doc.doctype,get_url_to_form(doc.doctype,doc.name))
	company = frappe.db.get_value("Employee",doc.employee,"company")
	args = {
		"url":url,
		"employee":doc.employee,
		"employee_name":doc.employee_name,
		"encashment_amount":doc.get("encashment_amount") or 0,
		"encashment_days":doc.get("encashment_days") or 0,
		"branch": frappe.db.get_value("Employee",doc.employee,"branch") or '-',
		"department": frappe.db.get_value("Employee",doc.employee,"department") or '-',
		"nationality": frappe.db.get_value("Employee",doc.employee,"nationality") or '-',
		"designation": frappe.db.get_value("Employee",doc.employee,"designation") or '-',
	}

	if role == "HR":
		email_template = frappe.get_doc("Email Template", "Leave Encashment - HR")
		subject = frappe.render_template(email_template.subject, args)
		message = frappe.render_template(email_template.response, args)

		sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = info().get("hr_to").get(company), attachments = None, cc =  None )
		frappe.msgprint(_("Email sent to {0}").format(info().get("hr_to").get(company)))


	else:
		email_template = frappe.get_doc("Email Template", "Leave Encashment - Finance")
		subject = frappe.render_template(email_template.subject, args)
		message = frappe.render_template(email_template.response, args)

		sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = info().get("finance_to").get(company), attachments = None, cc =  None )
		frappe.msgprint(_("Email sent to {0}").format(info().get("finance_to").get(company)))

#################################################
######### Employee Probation Reminder ###########
#################################################

from cyrix.cyrix_tsl.report.employee_probation.employee_probation import execute
def send_probation_reminder():
	result = execute()  
	records = result[1]
	for rec in records:
		if rec.get('difference') in [15, 5]:
			company = frappe.db.get_value("Employee",rec.get("employee"),"company")
			args = {
				"employee":rec.get("employee"),
				"employee_name":rec.get("employee_name"),
				"branch": frappe.db.get_value("Employee",rec.get("employee"),"branch") or '-',
				"department": frappe.db.get_value("Employee",rec.get("employee"),"department") or '-',
				"designation": frappe.db.get_value("Employee",rec.get("employee"),"designation") or '-',
				"nationality": frappe.db.get_value("Employee",rec.get("employee"),"nationality") or '-',
				"probation_end_date": rec.get("probation_end_date") or '-',
				"no_of_days":rec.get('difference')
			}


			email_template = frappe.get_doc("Email Template", "Employee Probation")
			subject = frappe.render_template(email_template.subject, args)
			message = frappe.render_template(email_template.response, args)
			try:
				make(
					recipients=info().get("hr_cc").get(company),
					sender="no-reply@cyrix-tsl.com",
					reply_to="no-reply@cyrix-tsl.com",
					subject = subject,
					content = message,
					send_email=1
				)
			except frappe.OutgoingEmailError:
				pass

#################################################
############ Annual Leave Reminder ##############
#################################################

def send_travel_reminders():
	today_date = getdate(today())

	leave_apps = frappe.get_all(
		"Leave Application Form",
		filters={
			"company": ["in", ["Company Al-Halloul Faniye Medical"]],
			"docstatus": 1,
			"leave_type": "Annual Leave",
			"from_date": [">=", today_date]
		},
		fields=[
			"name",
			"employee",
			"employee_name",
			"from_date",
			"to_date"
		]
	)

	reminder_map = {
		15: "Leave Reminder - 15 days",
		9: "Leave Reminder - 9 days",
		4: "Leave Reminder - 4 days"
	}

	for leave in leave_apps:
		days_before = (leave.from_date - today_date).days

		if days_before not in reminder_map:
			continue

		doc = frappe.get_doc("Leave Application Form", leave.name)

		employee = frappe.db.get_value(
			"Employee",
			doc.employee,
			[
				"company",
				"department",
				"branch",
				"nationality",
				"valid_upto",
				"civil_id_no"
			],
			as_dict=True
		)

		args = {
			"employee_name": doc.employee_name,
			"employee": doc.employee,
			"department": employee.department or '-',
			"branch": employee.branch or '-',
			"nationality": employee.nationality or '-',
			"valid_upto": employee.valid_upto or '-',
			"leave_type": doc.leave_type or '-',
			"from_date": doc.from_date or '-',
			"to_date": doc.to_date or '-',
			"destination": doc.to_destination or '-',
			"civil_id": employee.civil_id_no or '-',
		}

		email_template = frappe.get_doc(
			"Email Template",
			reminder_map[days_before]
		)

		subject = frappe.render_template(email_template.subject, args)
		message = frappe.render_template(email_template.response, args)

		sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = "admin@tsl-me.com", attachments = None, cc =  ["admin-sa1@tsl-me.com","finance@tsl-me.com"] )


#################################################
#### Unapproved Leave application Reminder  #####
#################################################

def unapproved_leaves_reminder():
	lap_list = frappe.db.get_all(
		"Leave Application Form",
		{
			"docstatus":0,
			"workflow_state": ["not in",["Rejected"]]
		},
		["name","from_date"]
	)
	for lap in lap_list:
		diff = date_diff(lap.from_date,getdate(today()))
		if diff in [3, 5]:
			doc = frappe.get_doc("Leave Application Form", lap.name)
			args = {
				"employee_name":doc.employee_name,
				"employee":doc.employee,
				"department": frappe.db.get_value("Employee",doc.employee,"department") or '-',
				"branch": frappe.db.get_value("Employee",doc.employee,"branch") or '-',
				"nationality": frappe.db.get_value("Employee",doc.employee,"nationality") or '-',
				"valid_upto": frappe.db.get_value("Employee",doc.employee,"valid_upto"),
				"leave_type":doc.leave_type or '-',
				"from_date":doc.from_date or '-',
				"to_date":doc.to_date or '-',
				"no_of_days":doc.no_of_days or '-',
				"reason":doc.description or '-',
			}

			if doc.leave_type in ["Annual Leave"]:
				recipients = info().get("hr_to").get(doc.company)
			else:
				recipients = info().get("hr_cc").get(doc.company)

			email_template = frappe.get_doc("Email Template", "Leave Approval Reminder")
			subject = frappe.render_template(email_template.subject, args)
			message = frappe.render_template(email_template.response, args)

			try:
				sendmail(doc, message, subject, sender = "no-reply@cyrix-tsl.com", recipients = recipients, attachments = None)
			except frappe.OutgoingEmailError:
				pass

#################################################
#### Relieving Reminder Mail (3 and 5 days) #####
#################################################

def reminder_on_relieving():
	employee_list = frappe.db.get_list("Employee",{
		"relieving_date":["is","set"],
		"relieving_date":[">",getdate(today())]
	},['name','relieving_date'])
	for employee in employee_list:
		diff = date_diff(employee.relieving_date, getdate(today()))
		if diff in [3, 5]:
			emp = frappe.get_doc("Employee",employee.name)
			company = frappe.db.get_value("Employee",emp.name,"company")
			args = {
				"employee":emp.name,
				"employee_name":emp.employee_name,
				"branch": emp.branch or '-',
				"department": emp.department or '-',
				"nationality": emp.nationality or '-',
				"designation": emp.designation or '-',
				"relieving_date":emp.relieving_date,
				"no_of_days":diff
			}

			email_template = frappe.get_doc("Email Template", "Relieving Reminder")
			subject = frappe.render_template(email_template.subject, args)
			message = frappe.render_template(email_template.response, args)

			try:
				sendmail(
					emp, 
					message, 
					subject, 
					sender = "no-reply@cyrix-tsl.com", 					
					recipients=info().get("hr_to").get(emp.company),
					attachments = None, 
				)
			
			except frappe.OutgoingEmailError:
				pass

def send_birthday_reminder():
	today_date = today()
	today_month_day = getdate(today_date).strftime("%m-%d")
	is_leap_year = calendar.isleap(datetime.now().year)
	branch_and_mail_id = [
		{"name": "Jeddah - TSL-SA", "sender":"no-reply@cyrix-tsl.com" ,"recipient": "admin@tsl-me.com","cc":None},
		{"name": "Dammam - TSL-SA", "sender":"no-reply@cyrix-tsl.com" ,"recipient": "admin@tsl-me.com","cc":None},
		{"name": "Riyadh - TSL- KSA", "sender":"no-reply@cyrix-tsl.com" ,"recipient": "admin@tsl-me.com","cc":None},
		{"name": "Dubai - TSL", "sender":"no-reply@cyrix-tsl.com" ,"recipient": "support@cyrix-tsl.com" ,"cc":"hr1@tsl-me.com"},
		{"name": "Kuwait - TSL", "sender":"no-reply@cyrix-tsl.com" ,"recipient": "hr1@tsl-me.com" ,"cc":"info@cyrix-tsl.com"}
	]
	
	for branch in branch_and_mail_id:
		today_birthdays = []
		upcoming_birthdays = []
		all_today_birthdays = []
		all_upcoming_birthdays = []
		employees = frappe.get_all("Employee", 
			filters={
				"skip_reminder": 0,
				"status": "Active", 
				"branch": branch["name"],
				"user_id": ["not in", ["support@cyrix-tsl.com"]]
			},
			fields=['name', 'date_of_birth', 'employee_name','user_id']
		)
		for employee_doc in employees:
			birthday = getdate(employee_doc.date_of_birth)
			birthday_month_day = birthday.strftime("%m-%d")
			if not is_leap_year and birthday_month_day == "02-29":
				birthday_month_day = "02-28"
			if today_month_day == birthday_month_day:
				today_birthdays.append((branch["name"], employee_doc.employee_name, employee_doc.date_of_birth))
			elif today_month_day == add_days(birthday, -2).strftime("%m-%d"):
				upcoming_birthdays.append((branch["name"], employee_doc.employee_name, employee_doc.date_of_birth))
		
		all_today_birthdays.extend(today_birthdays)
		all_upcoming_birthdays.extend(upcoming_birthdays)
		print(all_today_birthdays)
		print(all_upcoming_birthdays)
	
		if all_today_birthdays or all_upcoming_birthdays:
			subject = "Birthday Reminder for the Day"
			message = """
			<html>
			<body>
			<p>Dear Team,</p>
			"""
			
			if all_today_birthdays:
				message += "<h3>Today's Birthdays:</h3>"
				message += "<table border='1' cellpadding='5' cellspacing='0'><tr><th>Name</th><th>Branch</th><th>Date of Birth</th></tr>"
				for branch_name, name, dob in all_today_birthdays:
					message += f"<tr><td>{name}</td><td>{branch_name}</td><td>{dob.strftime('%d-%m-%Y')}</td></tr>"
				message += "</table><br>"
			
			if all_upcoming_birthdays:
				message += "<h3>Upcoming Birthdays (In 2 Days):</h3>"
				message += "<table border='1' cellpadding='5' cellspacing='0'><tr><th>Name</th><th>Branch</th><th>Date of Birth</th></tr>"
				for branch_name, name, dob in all_upcoming_birthdays:
					message += f"<tr><td>{name}</td><td>{branch_name}</td><td>{dob.strftime('%d-%m-%Y')}</td></tr>"
				message += "</table><br>"
			
			make(
				sender = branch['sender'],
				reply_to = branch['sender'],
				recipients=branch['recipient'],
				subject=subject,
				content=message,
				send_email=1,
				cc=branch["cc"]
			)


def send_birthday_reminder_hr():
	today_date = today()
	today_month_day = getdate(today_date).strftime("%m-%d")
	is_leap_year = calendar.isleap(datetime.now().year)
	branch_and_mail_id = [
		{"name": "Dubai - TSL", "sender":"no-reply@cyrix-tsl.com" ,"recipient": "ronish@cyrix-tsl.com"}, #ronish
	]
	
	for branch in branch_and_mail_id:
		today_birthdays = []
		upcoming_birthdays = []
		all_today_birthdays = []
		all_upcoming_birthdays = []
		employees = frappe.get_all("Employee", 
			filters={
				"skip_reminder":0,
				"status": "Active", 
				"branch": branch["name"],
				"user_id": ["in", ["support@cyrix-tsl.com"]]
			},
			fields=['name', 'date_of_birth', 'employee_name','user_id']
		)
		for employee_doc in employees:
			birthday = getdate(employee_doc.date_of_birth)
			birthday_month_day = birthday.strftime("%m-%d")
			if not is_leap_year and birthday_month_day == "02-29":
				birthday_month_day = "02-28"
			if today_month_day == birthday_month_day:
				today_birthdays.append((branch["name"], employee_doc.employee_name, employee_doc.date_of_birth))
			elif today_month_day == add_days(birthday, -2).strftime("%m-%d"):
				upcoming_birthdays.append((branch["name"], employee_doc.employee_name, employee_doc.date_of_birth))
			
		all_today_birthdays.extend(today_birthdays)
		all_upcoming_birthdays.extend(upcoming_birthdays)
	
		if all_today_birthdays or all_upcoming_birthdays:
			subject = "Birthday Reminder for the Day"
			message = """
			<html>
			<body>
			<p>Dear Team,</p>
			"""
			
			if all_today_birthdays:
				message += "<h3>Today's Birthdays:</h3>"
				message += "<table border='1' cellpadding='5' cellspacing='0'><tr><th>Name</th><th>Branch</th><th>Date of Birth</th></tr>"
				for branch_name, name, dob in all_today_birthdays:
					message += f"<tr><td>{name}</td><td>{branch_name}</td><td>{dob.strftime('%d-%m-%Y')}</td></tr>"
				message += "</table><br>"
			
			if all_upcoming_birthdays:
				message += "<h3>Upcoming Birthdays (In 2 Days):</h3>"
				message += "<table border='1' cellpadding='5' cellspacing='0'><tr><th>Name</th><th>Branch</th><th>Date of Birth</th></tr>"
				for branch_name, name, dob in all_upcoming_birthdays:
					message += f"<tr><td>{name}</td><td>{branch_name}</td><td>{dob.strftime('%d-%m-%Y')}</td></tr>"
				message += "</table><br>"

			make(
				sender = branch['sender'],
				reply_to = branch['sender'],
				recipients=branch['recipient'],
				subject=subject,
				content=message,
				send_email=1,
			)