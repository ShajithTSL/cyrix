import frappe
from frappe.core.doctype.communication.email import _make as make_communication

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