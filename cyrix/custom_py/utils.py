import frappe
from frappe.utils.pdf import get_pdf

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