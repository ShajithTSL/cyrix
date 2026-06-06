import frappe
from frappe.utils.pdf import get_pdf
from frappe.model.mapper import get_mapped_doc
from frappe.core.doctype.communication.email import _make as make_communication
from frappe.utils.file_manager import get_file
from frappe.utils.csvutils import read_csv_content
from datetime import datetime



# @frappe.whitelist()
# def si_import(import_file):
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
# 		customer_name = (i[1] or "").strip()

# 		if customer_name:
# 			cus = frappe.db.exists("Customer", customer_name)

# 			if not cus:

				# similar = frappe.db.sql("""
				# 	SELECT name
				# 	FROM `tabCustomer`
				# 	WHERE name LIKE %s
				# 	LIMIT 300
				# """, (f"%{customer_name}%",), as_dict=True)

				# if similar:
				# 	for d in similar:
				# 		print(f"{customer_name} - {similar[0].name}")
						
				
				
			


	