import frappe
from cyrix.custom_py.email_notification import sendmail
from frappe.utils import (
	getdate,
	date_diff,
	fmt_money,
	format_time,
	formatdate,
	get_link_to_report,
	get_url_to_form,
	get_url_to_list,
	now_datetime,
	today,
)
OFFSETS = [-70, -65, 2, 5, 7, 10]  # days after the expiry that trigger a reminder

OFFSET_LABELS = {
    -70: "70 days before expiry",
    -65: "65 days before expiry",
    2: "2 days after expiry",
    5: "5 days after expiry",
    7: "7 days after expiry",
    10: "10 days after expiry",
}

def schedule_qiwa_reminder():
    job1 = frappe.db.exists('Scheduled Job Type', {"method" : 'cyrix.hr_py.qiwa_contract_reminder.send_qiwa_contract_reminders'})
    if not job1:
        sjt = frappe.new_doc("Scheduled Job Type")  
        sjt.update({
            "method" : 'cyrix.hr_py.qiwa_contract_reminder.send_qiwa_contract_reminders',
            "cron_format" : '0 7 * * *'
        })
        sjt.save(ignore_permissions=True)

    job2 = frappe.db.exists('Scheduled Job Type', {"method" : 'cyrix.hr_py.qiwa_contract_reminder.send_qiwa_contract_reminders_on_further_action'})
    if not job2:
        sjt = frappe.new_doc("Scheduled Job Type")  
        sjt.update({
            "method" : 'cyrix.hr_py.qiwa_contract_reminder.send_qiwa_contract_reminders_on_further_action',
            "cron_format" : '0 7 * * *'
        })
        sjt.save(ignore_permissions=True)

def send_qiwa_contract_reminders():
    """Daily scheduler entry point."""
    employees = frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "company": "Company Al-Halloul Faniye Medical",
        },
        fields=[
            "name",
            "employee_name",
            "qiwa_contract_expiry_date",
            "branch",
            "civil_id_no",
        ],
    )

    today_date = getdate(today())

    for emp in employees:
        if not emp.qiwa_contract_expiry_date:
            continue

        offset = date_diff(today_date, getdate(emp.qiwa_contract_expiry_date))
        if offset in OFFSETS:
            if offset > 0:
                send_reminder_email(emp, offset)

def send_reminder_email(emp, offset):
    offset_label = OFFSET_LABELS.get(offset, f"{offset} days after expiry")

    message = frappe.render_template(
        """
        <p>Dear HR Team,</p>
        <p><strong>{{ employee_name }}</strong>'s Qiwa contract has auto-renewed
           and needs to be <strong>downloaded and updated</strong> in the
           Contract Folder.</p>
        <table cellpadding="6" cellspacing="0" border="1"
               style="border-collapse: collapse; margin: 12px 0;">
          <tr><td><strong>Employee Number</strong></td><td><a href="{{ url }}">{{ name }}</a></td></tr>
          <tr><td><strong>Employee Name</strong></td><td>{{ employee_name }}</td></tr>
          <tr><td><strong>Qiwa Contract Expiry Date</strong></td><td>{{ qiwa_contract_expiry_date }}</td></tr>
          <tr><td><strong>Branch</strong></td><td>{{ branch }}</td></tr>
          <tr><td><strong>Iqama Number</strong></td><td>{{ civil_id_no }}</td></tr>
        </table>
        <p>Reminder stage: <strong>{{ offset_label }}</strong>.</p>
        <p>Please download the renewed contract PDF from Qiwa and save it in
           this employee's Contract Folder.</p>
        """,
        {
            "url": get_url_to_form("Employee",emp.name),
            "employee_name": emp.employee_name,
            "qiwa_contract_expiry_date": formatdate(emp.qiwa_contract_expiry_date),
            "branch": emp.branch,
            "civil_id_no": emp.civil_id_no,
            "name": emp.name,
            "offset_label": offset_label,
        },
    )

    employee_doc = frappe.get_doc("Employee",emp.name)
    sendmail(
        employee_doc, 
        message=message,
        subject=f"Qiwa Contract Renewal Reminder — {emp.employee_name} ({offset_label})",
        sender = "no-reply@cyrix-tsl.com", 					
        recipients="admin@tsl-me.com",
        cc = "admin-sa1@tsl-me.com", 
        attachments = None, 
    )

def send_qiwa_contract_reminders_on_further_action():
    """Daily scheduler entry point."""
    employees = frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "company": "Company Al-Halloul Faniye Medical",
            "saudization": 0
        },
        fields=[
            "name",
            "employee_name",
            "qiwa_contract_expiry_date",
            "branch",
            "civil_id_no",
        ],
    )

    today_date = getdate(today())

    for emp in employees:
        if not emp.qiwa_contract_expiry_date:
            continue

        offset = date_diff(today_date, getdate(emp.qiwa_contract_expiry_date))
        if offset in OFFSETS:
            if offset < 0:
                send_reminder_email_on_further_action(emp, offset)

def send_reminder_email_on_further_action(emp, offset):
    offset_label = OFFSET_LABELS.get(offset, f"{offset} days before expiry")

    message = frappe.render_template(
        """
        <p>Dear HR Team,</p>

        <p>
        The Qiwa employment contract for
        <strong>{{ employee_name }}</strong> is approaching its expiry date.
        Please review the contract and decide whether to proceed with
        <strong>Renewal or Termination</strong>.
        </p>

        <table cellpadding="6" cellspacing="0" border="1"
            style="border-collapse: collapse; margin: 12px 0;">
        <tr>
            <td><strong>Employee Number</strong></td>
            <td><a href="{{ url }}">{{ name }}</a></td>
        </tr>
        <tr>
            <td><strong>Employee Name</strong></td>
            <td>{{ employee_name }}</td>
        </tr>
        <tr>
            <td><strong>Qiwa Contract Expiry Date</strong></td>
            <td>{{ qiwa_contract_expiry_date }}</td>
        </tr>
        <tr>
            <td><strong>Branch</strong></td>
            <td>{{ branch }}</td>
        </tr>
        <tr>
            <td><strong>Iqama Number</strong></td>
            <td>{{ civil_id_no }}</td>
        </tr>
        <tr>
            <td><strong>Reminder Stage</strong></td>
            <td>{{ offset_label }}</td>
        </tr>
        </table>

        <p>
        <strong>Required Action:</strong>
        </p>

        <ul>
        <li>
            <strong>Renewal:</strong> Coordinate with the concerned department
            and initiate the contract renewal process through Qiwa.
        </li>
        <li>
            <strong>Termination:</strong> Coordinate with the concerned department
            and initiate the applicable termination process in accordance with
            company policy and applicable requirements.
        </li>
        </ul>

        <p>
        Please confirm the intended action and ensure the necessary process
        is initiated well before the contract expiry date.
        </p>

        <p>
        <strong>Note:</strong> This is a {{ offset_label }} reminder.
        Timely action is required to avoid delays in contract processing.
        </p>

        <p>Best regards,<br>HR System Notification</p>
        """,
        {
            "url": get_url_to_form("Employee", emp.name),
            "employee_name": emp.employee_name,
            "qiwa_contract_expiry_date": formatdate(
                emp.qiwa_contract_expiry_date
            ),
            "branch": emp.branch,
            "civil_id_no": emp.civil_id_no,
            "name": emp.name,
            "offset_label": offset_label,
        },
    )

    employee_doc = frappe.get_doc("Employee",emp.name)
    sendmail(
        employee_doc, 
        message=message,
        subject=f"Qiwa Contract Renewal Reminder — {emp.employee_name} ({offset_label})",
        sender = "no-reply@cyrix-tsl.com", 					
        recipients="admin@tsl-me.com",
        attachments = None, 
    )