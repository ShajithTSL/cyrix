import frappe
from frappe.utils.pdf import get_pdf

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