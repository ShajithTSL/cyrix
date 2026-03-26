import frappe
from frappe.utils.pdf import get_pdf
from frappe.core.doctype.communication.email import _make as make_communication

def fetch_price_list(company, document_type):
	field = "selling" if document_type == "selling" else "buying"

	price_list_details = frappe.db.sql(f"""
		SELECT pl.name
		FROM `tabCompany List` cl
		JOIN `tabPrice List` pl ON pl.name = cl.parent
		WHERE cl.parenttype = 'Price List'
		AND cl.company = %s
		AND pl.{field} = 1
	""", (company), as_dict=True)

	return price_list_details[0].name if price_list_details else None

@frappe.whitelist()
def download_custom_pdf(doctype, name, print_format="Standard", no_letterhead=0):
	doc = frappe.get_doc(doctype, name)
	html = frappe.get_print(doctype, name, print_format, doc=doc, no_letterhead=no_letterhead)
	pdf = get_pdf(html)

	# Clean filename (remove spaces, special chars)
	customer = (doc.customer_name or "").replace(" ", "_").replace("/", "_")
	filename = f"{name}_{customer}.pdf"

	frappe.local.response.filename = filename
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "download"

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


def delete_doc():
	frappe.delete_doc("Stock Ledger Entry","e29229ccc0")