import frappe
from frappe.utils.pdf import get_pdf
from frappe.core.doctype.communication.email import _make as make_communication
from frappe.utils.file_manager import get_file
from frappe.utils.csvutils import read_csv_content


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

@frappe.whitelist()
def update_jd():
	frappe.db.sql("""
		UPDATE `tabJob Order Data`
		SET docstatus = 1
		WHERE owner = 'Administrator'
		AND DATE(creation) = CURDATE()
	""")

	frappe.db.commit()
# @frappe.whitelist()
# def dlt_jo():
# 	frappe.db.sql("""
# 		DELETE FROM `tabJob Order Data`
# 		WHERE owner = 'Administrator'
# 		AND DATE(creation) = '2026-03-29'
# 	""")

# 	frappe.db.commit()
# 	return "Items deleted for 2026-03-28"


# @frappe.whitelist()
# def jo_import(import_file):
# 	"""
# 	import_file = File Doc name OR file URL
# 	"""
# 	# get file path
# 	file_doc = get_file(import_file)
# 	file_path = file_doc[1]

# 	# read csv
# 	data = read_csv_content(file_path)

# 	# skip header, process first 20 rows
# 	count = 0
# 	for i in data:
# 		print(i[0])
# 		s = frappe.new_doc("Item")
# 		s.description = i[0]
# 		s.item_group = "Scope"
# 		s.save()
	





import frappe
from frappe.utils.file_manager import get_file
from frappe.utils.csvutils import read_csv_content
from datetime import datetime


@frappe.whitelist()
def jo_import(import_file):

	# 🔹 Get file
	file_doc = get_file(import_file)
	file_path = file_doc[1]

	# 🔹 Read CSV
	data = read_csv_content(file_path)

	count = 0

	# 🔹 Status Mapping
	status_map = {
		"P": "P-Paid",
		"RNRC": "RNRC-Return Not Repaired Client",
		"A": "Approved",
		"C": "C-Comparison",
		"CC": "CC-Comparison Client",
		"EP": "EP-Extra Parts",
		"NE": "NE-Need Evaluation",
		"NER": "NER-Need Evaluation Return",
		"Q": "Quoted",
		"RNA": "RNA-Return Not Approved",
		"RNAC": "RNAC-Return Not Approved Client",
		"RNF": "RNF-Return No Fault",
		"RNFC": "RNFC-Return No Fault Client",
		"RNP": "RNP-Return No Parts",
		"RNPC": "RNPC-Return No Parts Client",
		"RNR": "RNR-Return Not Repaired",
		"RS": "RS-Repaired and Shipped",
		"RSC": "RSC-Repaired and Shipped Client",
		"RSI": "Invoiced",
		"SP": "SP-Searching Parts",
		"TR": "TR-Technician Repair",
		"UE": "UE-Under Evaluation",
		"UTR": "UTR-Under Technician Repair",
		"W": "W-Working",
		"WP": "WP-Waiting Parts",
		"CT": "CT-Customer Testing"
	}

	for i in data[1:]:

		# ✅ Skip invalid rows
		if len(i) < 5:
			continue

		# 🔹 Extract values safely
		jo_number = i[0]
		sales_person = i[1]
		date_str = i[2]
		customer = i[3]
		status_code = i[4]

		# 🔹 Convert Date (dd-mm-yyyy → yyyy-mm-dd)
		posting_date = None
		if date_str:
			try:
				posting_date = datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
			except:
				continue  # skip invalid date

		# 🔹 Create Customer if not exists
		if customer and not frappe.db.exists("Customer", customer):
			c = frappe.new_doc("Customer")
			c.customer_name = customer
			c.territory = "Kuwait"
			c.customer_type = "Company"
			c.insert(ignore_permissions=True)

		# 🔹 Map Status
		status = status_map.get(status_code, status_code)

		# 🔹 Naming (JO-xxxx)
		name = f"SO-{jo_number}"

		# 🔹 Avoid duplicate
		if frappe.db.exists("Supply Order Data", name):
			continue

		# 🔹 Create Job Order
		wo = frappe.new_doc("Supply Order Data")
		wo.name = name
		wo.naming_series = ""   # disable auto series

		wo.customer = customer
		wo.status = status
		wo.sales_person = sales_person
		wo.posting_date = posting_date

		# 🔹 Child table
		wo.append("material_list", {
			"item_code": "000240",
			"quantity": 1
		})

		# 🔹 Insert + Submit
		wo.insert(ignore_permissions=True)
		# wo.submit()

		count += 1

	# 🔹 Commit once
	# frappe.db.commit()

	return f"✅ Total Job Orders Created & Submitted: {count}"

@frappe.whitelist()
def preview_custom_pdf(doctype, name, print_format="Standard", no_letterhead=0):
	doc = frappe.get_doc(doctype, name)
	html = frappe.get_print(doctype, name, print_format, doc=doc, no_letterhead=no_letterhead)
	pdf = get_pdf(html)

	# Clean filename (remove spaces, special chars)
	customer = (doc.customer_name or "").replace(" ", "_").replace("/", "_")
	filename = f"{name}_{customer}.pdf"

	frappe.local.response.filename = filename
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "pdf"