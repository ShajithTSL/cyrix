import frappe
from frappe.utils.pdf import get_pdf
from frappe.model.mapper import get_mapped_doc
from frappe.core.doctype.communication.email import _make as make_communication
from frappe.utils.file_manager import get_file
from frappe.utils.csvutils import read_csv_content
from datetime import datetime


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


# def delete_doc():
# 	frappe.delete_doc("Stock Entry","2a15fc183a")

@frappe.whitelist()
def update_jd():
	frappe.db.sql("""
		UPDATE `tabSupply Order Data`
		SET docstatus = 1
		WHERE owner = 'Administrator'
		
	""")

	frappe.db.commit()


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
# 	for i in data[1:]:
# 		so_number = i[0]
# 		sales_person = i[1]
# 		date_str = i[2]
# 		customer = i[3]
# 		status_code = i[8]


# 		name = f"SO-{so_number}"
# 			# 🔹 Create Job Order
# 		wo = frappe.new_doc("Supply Order Data")
# 		wo.name = name
# 		wo.naming_series = ""   # disable auto series

# 		wo.customer = customer
# 		wo.status = status
# 		wo.sales_person = sales_person
# 		wo.posting_date = posting_date

# 		# 🔹 Child table
# 		wo.append("material_list", {
# 			"item_code": "000240",
# 			"quantity": 1
# 		})

# 		# 🔹 Insert + Submit
# 		wo.insert(ignore_permissions=True)
		# wo.submit()





# import frappe
# from frappe.utils.file_manager import get_file
# from frappe.utils.csvutils import read_csv_content
# from datetime import datetime


# @frappe.whitelist()
# def jo_import(import_file):

# 	# 🔹 Get file
# 	file_doc = get_file(import_file)
# 	file_path = file_doc[1]

# 	# 🔹 Read CSV
# 	data = read_csv_content(file_path)

# 	count = 0

# 	# 🔹 Status Mapping
# 	status_map = {
# 		"P": "P-Paid",
# 		"RNRC": "RNRC-Return Not Repaired Client",
# 		"A": "Approved",
# 		"C": "C-Comparison",
# 		"CC": "CC-Comparison Client",
# 		"EP": "EP-Extra Parts",
# 		"NE": "NE-Need Evaluation",
# 		"NER": "NER-Need Evaluation Return",
# 		"Q": "Quoted",
# 		"RNA": "RNA-Return Not Approved",
# 		"RNAC": "RNAC-Return Not Approved Client",
# 		"RNF": "RNF-Return No Fault",
# 		"RNFC": "RNFC-Return No Fault Client",
# 		"RNP": "RNP-Return No Parts",
# 		"RNPC": "RNPC-Return No Parts Client",
# 		"RNR": "RNR-Return Not Repaired",
# 		"RS": "RS-Repaired and Shipped",
# 		"RSC": "RSC-Repaired and Shipped Client",
# 		"RSI": "Invoiced",
# 		"SP": "SP-Searching Parts",
# 		"TR": "TR-Technician Repair",
# 		"UE": "UE-Under Evaluation",
# 		"UTR": "UTR-Under Technician Repair",
# 		"W": "W-Working",
# 		"WP": "WP-Waiting Parts",
# 		"CT": "CT-Customer Testing"
# 	}

# 	for i in data[1:]:

# 		# ✅ Skip invalid rows
# 		if len(i) < 5:
# 			continue

# 		# 🔹 Extract values safely
# 		jo_number = i[0]
# 		sales_person = i[1]
# 		date_str = i[2]
# 		customer = i[3]
# 		status_code = i[8]

# 		# 🔹 Convert Date (dd-mm-yyyy → yyyy-mm-dd)
# 		posting_date = None
# 		if date_str:
# 			try:
# 				posting_date = datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
# 			except:
# 				continue  # skip invalid date

# 		# 🔹 Create Customer if not exists
# 		if customer and not frappe.db.exists("Customer", customer):
# 			c = frappe.new_doc("Customer")
# 			c.customer_name = customer
# 			c.territory = "Kuwait"
# 			c.customer_type = "Company"
# 			c.insert(ignore_permissions=True)

# 		# 🔹 Map Status
# 		status = status_map.get(status_code, status_code)

# 		# 🔹 Naming (JO-xxxx)
# 		name = f"SO-{jo_number}"

# 		# 🔹 Avoid duplicate
# 		if frappe.db.exists("Supply Order Data", name):
# 			continue

# 		# 🔹 Create Job Order
# 		wo = frappe.new_doc("Supply Order Data")
# 		wo.name = name
# 		wo.naming_series = ""   # disable auto series

# 		wo.customer = customer
# 		wo.status = status
# 		wo.sales_person = sales_person
# 		wo.posting_date = posting_date

# 		# # 🔹 Child table
# 		# wo.append("material_list", {
# 		# 	"item_code": "000240",
# 		# 	"quantity": 1
# 		# })

# 		# 🔹 Insert + Submit
# 		wo.insert(ignore_permissions=True)
# 		# wo.submit()

# 		count += 1

# 	# 🔹 Commit once
# 	# frappe.db.commit()

# 	return f"✅ Total Job Orders Created & Submitted: {count}"

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


@frappe.whitelist()
def create_replacement_item(customer,wod,items):
	from datetime import date
	today = date.today()
	wd = frappe.new_doc("Replacement Unit")
	wd.name = wod
	
	doclist = get_mapped_doc("Job Order Data",wod, {
	"Job Order Data": {
		"doctype": "Job Order Data",	
	},
	},wd)
	
	wd.posting_date = today
	for i in doclist.get('material_list'):		
		i.serial_no = ""
	wd.status = "Inquiry"
	wd.status_duration_details = []
	wd.append("status_duration_details",{
		"status":wd.status,
		"date":datetime.now(),
	})
	wd.save(ignore_permissions =True)
	wd.submit()
	frappe.msgprint("Replacement Unit Created")

	# w = frappe.get_doc("Job Order Data",wod)
	# st = frappe.new_doc("Stock Entry")
	# st.company = w.company
	# st.stock_entry_type = "Material Issue"
	# # st.custom_replacement_unit = wd.name
	# for i in w.material_list:
	# 	has_serial_no = frappe.db.get_value("Item", {"item_code": i.item_code}, "has_serial_no")
	# 	if has_serial_no:

	# 		st.append("items",{
	# 		"item_code":i.item_code,
	# 		"qty":i.quantity,
	# 		"s_warehouse":w.repair_warehouse,
	# 		"uom":"Nos",
	# 		"stock_uom":"Nos",
	# 		"use_serial_batch_fields":1,
	# 		"serial_no":i.serial_no,
	# 		'conversion_factor':1,
	# 		"allow_zero_valuation_rate": 1,
	# 		"custom_replacement_unit": wod,
	# 		"work_order_data": wod
	# 	})
	# 	else:
	# 		st.append("items",{
	# 		"item_code":i.item_code,
	# 		"qty":i.quantity,
	# 		"s_warehouse":w.repair_warehouse,
	# 		"uom":"Nos",
	# 		"stock_uom":"Nos",
	# 		"custom_serial_number":i.serial_no,
	# 		'conversion_factor':1,
	# 		"allow_zero_valuation_rate": 1,
	# 		"custom_replacement_unit": wod,
	# 		"work_order_data": wod
					
	# 	})
		
	# st.save(ignore_permissions = True)
	# st.submit()



@frappe.whitelist()
def create_replacement_item(customer, wod, items, release_stock=0):

	from datetime import date, datetime

	today = date.today()

	# 🔹 Create Replacement Unit
	wd = frappe.new_doc("Replacement Unit")
	wd.name = wod

	doclist = get_mapped_doc("Job Order Data", wod, {
		"Job Order Data": {
			"doctype": "Job Order Data",
		},
	}, wd)

	wd.posting_date = today

	for i in doclist.get('material_list'):
		i.serial_no = ""

	wd.status = "Inquiry"
	wd.status_duration_details = []
	wd.append("status_duration_details", {
		"status": wd.status,
		"date": datetime.now(),
	})

	wd.save(ignore_permissions=True)
	# wd.submit()

	# 🔹 Only create Stock Entry if user confirmed
	if int(release_stock) == 1:

		w = frappe.get_doc("Job Order Data", wod)

		st = frappe.new_doc("Stock Entry")
		st.company = w.company
		st.stock_entry_type = "Material Issue"
		st.custom_replacement_unit = wod

		for i in w.material_list:

			has_serial_no = frappe.db.get_value(
				"Item", {"item_code": i.item_code}, "has_serial_no"
			)

			if has_serial_no:
				st.append("items", {
					"item_code": i.item_code,
					"qty": i.quantity,
					"s_warehouse": w.repair_warehouse,
					"uom": "Nos",
					"stock_uom": "Nos",
					"use_serial_batch_fields": 1,
					"serial_no": i.serial_no,
					"conversion_factor": 1,
					"allow_zero_valuation_rate": 1,
					"custom_replacement_unit": wod,
					"work_order_data": wod
				})
			else:
				st.append("items", {
					"item_code": i.item_code,
					"qty": i.quantity,
					"s_warehouse": w.repair_warehouse,
					"uom": "Nos",
					"stock_uom": "Nos",
					"custom_serial_number": i.serial_no,
					"conversion_factor": 1,
					"allow_zero_valuation_rate": 1,
					"custom_replacement_unit": wod,
					"work_order_data": wod
				})

		st.save(ignore_permissions=True)
		# st.submit()

	frappe.msgprint("Replacement Unit Created")
	return "Success"


@frappe.whitelist()
def item_import(import_file):
	"""
	import_file = File Doc name OR file URL
	"""
	# get file path
	file_doc = get_file(import_file)
	file_path = file_doc[1]

	# read csv
	data = read_csv_content(file_path)

	# skip header, process first 20 rows
	count = 0
	for i in data[1:]:
		if i[4]:
			if i[4] == "0":
				it = frappe.new_doc("Item")
				
				# it.item_name = i[3]
				# it.marking_code = i[0]
				# it.description =i[3]
				# it.stock_uom = "Nos"
				# it.item_group = "Equipments"
				# it.is_stock_item = 1
				# it.save(ignore_permissions =1)
				count = count + 1
				
			else:
				im = frappe.get_value("Item Model",{"model":i[4]})
				if im:
					
					item = frappe.db.exists("Item",{"model":im})
					if item:
						# print("Item\tModel\tCol1\tCol2")
						des = frappe.get_value("Item",item,"description")
						mc = frappe.get_value("Item",item,"marking_code")
						print(f"{item},{i[4]},{mc},{des}")
						# it = frappe.new_doc("Item")
						# it.model = im
						# it.item_name = i[3]
						# it.marking_code = i[0]
						# it.description =i[3]
						# it.stock_uom = "Nos"
						# it.item_group = "Equipments"
						# it.is_stock_item = 1
						# it.save(ignore_permissions =1)
						# count = count + 1
				
	

	
# @frappe.whitelist()
# def dlt_doc():
# 	frappe.db.sql("""
# 		DELETE FROM `tabReplacement Unit`
# 		WHERE name = "JO-6305" """)

# 	frappe.db.commit()
# 	return "Items deleted"


	