import frappe
from frappe.core.doctype.communication.email import make
from frappe.core.doctype.communication.email import _make as make_communication


@frappe.whitelist()
def purchase_msg_to_info(com,branch,ev,sender):
    frappe.errprint(branch)
    frappe.errprint(com)
    info = "karthiksrinivasan1996.ks@gmail.com"
    if com == "Cyrix TSL - Kuwait":
        info = "info@cyrix-tsl.com"
        
    if com == "Company Al-Halloul Faniye Medical":
        info = "info-sa@cyrix-tsl.com"
        
   
    frappe.sendmail(recipients=[info],
			sender = sender,
			subject="Part sheet Comments",
			message=""" <b>Dear Lab Coordinator,</b><br>
            Kindly find the comment for the Evaluation report  <b>%s</b> . Please take action to  <a href="https://erp.tsl-me.com/app/evaluation-report/%s"target="_blank">click here.</a>
		   
			""" %(ev,ev)
			)
    frappe.msgprint("Message sent Successfully")


@frappe.whitelist()
def to_purchaser(com=None, branch=None, ev=None, sender=None, recipients=None):

    emp = frappe.get_value(
        "Employee",
        {"user_id": recipients},
        "employee_name"
    ) or "Purchase Team"

    subject = "Request for Purchase Action"

    message = f"""
    <div style="font-family: Arial, sans-serif; font-size:14px; color:#333; line-height:1.6;">

        <p>Dear <b>{emp}</b>,</p>

        <p>
            Kindly find the attached document for your reference and further action
            regarding the Evaluation Report <b>{ev}</b>.
        </p>

        <p>
            Please review the details and proceed with the necessary process at the earliest convenience.
        </p>

        <p>
            This is for your information and necessary action.
        </p>

        <br>

        <p>
            Regards,<br>
            <b>TSL Team</b>
        </p>

    </div>
    """

    # Create Communication
    communication = make_communication(
        doctype="Evaluation Report",
        name=ev,
        content=message,
        subject=subject,
        sender=sender,
        recipients=recipients,
        communication_medium="Email",
        send_email=False,
        communication_type="Automated Message",
    ).get("name")

    # Send Mail
    frappe.sendmail(
        recipients=[recipients],
        sender=sender,
        subject=subject,
        message=message,
        attachments=get_eval_print(ev, "Evaluation Report"),
        communication=communication
    )

    frappe.msgprint("Message Sent Successfully")

def get_eval_print(name,doctype):
	attachments = frappe.attach_print(doctype, name,file_name=doctype, print_format="EV-V1")
	return [attachments]



import frappe
from frappe.utils import add_days
from datetime import date
from frappe.utils import getdate

def amc():

	today = date.today()

	contracts = frappe.get_all(
		"Maintenance Contract",
		fields=["name", "customer", "to_date"]
	)

	for contract in contracts:

		new_date = add_days(contract.to_date, -2)

		if contract.to_date == today or new_date == today:

			doc = frappe.get_doc("Maintenance Contract", contract.name)
			rec = frappe.get_value("Branch", doc.branch, "customer_support")

			if contract.to_date == today:
				reminder_text = """
				This is a reminder that the following Maintenance Contract is due for Preventive Maintenance today.
				"""
			else:
				reminder_text = """
				This is a reminder that the following Maintenance Contract is due for Preventive Maintenance in 2 days.
				"""

			html = f"""
			<p>Dear Info,</p>

			<p>
				{reminder_text}
			</p>

			<p>
				<b>Maintenance Contract:</b> {doc.name}<br>
				<b>Customer:</b> {doc.customer}<br>
                <b>Branch:</b> {doc.branch}<br>
                <b>Due Date:</b> {getdate(doc.to_date).strftime('%d-%m-%Y')}
			</p>

			<br>

			<table border="1" cellpadding="5" cellspacing="0" width="100%" style="border-collapse:collapse;">
				<thead>
					<tr style="background:#f2f2f2;">
						<th>Item Code</th>
						<th>Model</th>
						<th>Manufacturer</th>
						<th>Description</th>
						<th>Serial No</th>
                        <th>Qty.</th>
						<th>Amount</th>
					</tr>
				</thead>
				<tbody>
			"""

			for row in doc.items:
				html += f"""
					<tr>
						<td style="text-align:center">{row.item_code or ''}</td>
						<td style="text-align:center">{row.model or ''}</td>
						<td style="text-align:center">{row.manufacturer or ''}</td>
						<td style="text-align:center">{row.description or ''}</td>
						<td style="text-align:center">{row.serial_number or ''}</td>
                        <td style="text-align:center">{row.qty or ''}</td>
						<td style="text-align:center"">{row.amount or 0}</td>
					</tr>
				"""

			html += """
				</tbody>
			</table>

			<br>

			<p>
				Kindly schedule the preventive maintenance accordingly.
			</p>

			<p>
				Regards,<br>
				ERPNext
			</p>
			"""

			frappe.sendmail(
				recipients=["karthick@tsl-me.com"],
				subject=f"Preventive Maintenance Reminder - {doc.name}",
				message=html
			)

			frappe.logger().info(f"Preventive Maintenance reminder sent for {doc.name}")