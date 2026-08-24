# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
from cyrix.custom_py.quotation import fetch_item_price_details
from cyrix.custom_py import utils

from cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report import warehouse_based_on_branch_and_company, check_for_shared_docs_on_evaluation
naming_series = {
	"Internal Quotation - Repair":{
		"Kuwait":"IQR-K.YY.-",
		"Dammam":"IQR-D.YY.-",
		"Riyadh":"IQR-R.YY.-",
		"Jeddah":"IQR-J.YY.-",
		"Dubai":"IQR-DU.YY.-"
	},
	"Internal Quotation - Supply":{
		"Kuwait":"IQS-K.YY.-",
		"Dammam":"IQS-D.YY.-",
		"Riyadh":"IQS-R.YY.-",
		"Jeddah":"IQS-J.YY.-",
		"Dubai":"IQS-DU.YY.-"
	},
	"Customer Quotation - Repair":{
		"Kuwait":"CQR-K.YY.-",
		"Dammam":"CQR-D.YY.-",
		"Riyadh":"CQR-R.YY.-",
		"Jeddah":"CQR-J.YY.-",
		"Dubai":"CQR-DU.YY.-"
	},
	"Customer Quotation - Supply":{
		"Kuwait":"CQS-K.YY.-",
		"Dammam":"CQS-D.YY.-",
		"Riyadh":"CQS-R.YY.-",
		"Jeddah":"CQS-J.YY.-",
		"Dubai":"CQS-DU.YY.-"
	},
}
class JobOrderData(Document):

	def set_unit_status(self):

		if self.unit_status not in ["Yet to be Received"]:

			if not self.delivery:
				unit_status = "In Lab"

			elif not self.returned_date:
				unit_status = "With Customer"

			elif self.delivery >= self.returned_date:
				unit_status = "With Customer"

			else:
				unit_status = "In Lab"

			self.unit_status = unit_status
			frappe.db.set_value("Job Order Data", self.name, "unit_status", unit_status, update_modified=False)
		
		if self.status in ["A-Approved"]:
			frappe.db.set_value("Job Order Data", self.name, "is_approved", 1, update_modified=False)


	def after_insert(self):
		if self.get("maintenance_contract"):
			doc = frappe.get_doc("Maintenance Contract", self.get("maintenance_contract"))
			doc.append("reference_documents",{
				"reference_name": self.name,
				"ref_doctype": "Job Order Data"
			})
			doc.save(ignore_permissions=True)

	def before_submit(self):
		self.status = "NE-Need Evaluation"
		now = datetime.now()
		self.append("status_duration_details",{
			"status":self.status,
			"date":now,
		})
	
		if self.status != self.status_duration_details[-1].status:
			ldate = self.status_duration_details[-1].date
			now = datetime.now()
			time_date = str(ldate).split(".")[0]
			format_data = "%Y-%m-%d %H:%M:%S"
			date = datetime.strptime(time_date, format_data)
			duration = now - date
			duration_in_s = duration.total_seconds()
			minutes = divmod(duration_in_s, 60)[0]/60
			data = str(minutes).split(".")[0]+"hrs "+str(minutes).split(".")[1][:2]+"min"
			self.status_duration_details[-1].duration = data
			self.append("status_duration_details",{
				"status":self.status,
				"date":now,
			})

	def on_update_after_submit(self):
		self.set_unit_status()
		check_for_shared_docs_on_jo(self)
		if self.status != self.status_duration_details[-1].status:
			ldate = self.status_duration_details[-1].date
			now = datetime.now()
			time_date = str(ldate).split(".")[0]
			format_data = "%Y-%m-%d %H:%M:%S"
			date = datetime.strptime(time_date, format_data)
			duration = now - date
			duration_in_s = duration.total_seconds()
			minutes = divmod(duration_in_s, 60)[0]/60
			data = str(minutes).split(".")[0]+"hrs "+str(minutes).split(".")[1][:2]+"min"
			frappe.db.set_value("Status Duration Details",self.status_duration_details[-1].name,"duration",data)
			self.append("status_duration_details",{
				"status":self.status,
				"date":now,
			})
			doc = frappe.get_doc("Job Order Data",self.name)
			doc.append("status_duration_details",{
				"status":self.status,
				"date":now,
			})
			doc.save(ignore_permissions=True)
		update_child_jo_status(self)

# This function updates the status of child Job Orders to match the parent Job Order's status, except when the status is in a specific list of statuses.
def update_child_jo_status(self):
	if self.status not in ["Board Evaluation", "AP-Available Parts", "EP-Extra Parts", "NE-Need Evaluation", "SP-Searching Parts", "WP-Waiting Parts",
						"TR-Technician Repair", "UE-Under Evaluation", "UTR-Under Technician Repair", "Parts Priced", "IP-Internal Extra Parts"]:
		
		child_jo_list = frappe.get_all("Job Order Data",{"parent_jo":self.name,"name":("!=",self.name)},"name")
		if child_jo_list:
			for jo in child_jo_list:
				doc = frappe.get_doc("Job Order Data",jo.name)
				doc.status = self.status
				doc.save(ignore_permissions=True)

def check_for_shared_docs_on_jo(self):
	tech_user = frappe.db.get_value(
		"Technician ID", self.technician, "user_email"
	)

	technicians = []

	if tech_user:
		technicians.append(tech_user)

	# Additional technicians
	for row in self.multiple_technicians:
		if row.email and row.email not in technicians:
			technicians.append(row.email)

	if self.parent_jo:
		parent_doc = frappe.get_doc("Job Order Data",self.parent_jo)
		parent_tech_user = frappe.db.get_value("Technician ID",parent_doc.technician,"user_email")
		technicians.append(parent_tech_user)
		for pa_jo in parent_doc.multiple_technicians:
			if pa_jo.get("email") not in technicians:
				technicians.append(pa_jo.get("email"))

	# Existing shares
	existing_shares = frappe.get_all(
		"DocShare",
		filters={
			"share_doctype": self.doctype,
			"share_name": self.name
		},
		fields=["name", "user"]
	)

	existing_users = [d.user for d in existing_shares]

	# Add missing shares
	for user in technicians:
		if user not in existing_users:
			doc = frappe.new_doc("DocShare")
			doc.user = user
			doc.share_doctype = self.doctype
			doc.share_name = self.name
			doc.read = 1
			doc.write = 1
			doc.save(ignore_permissions=True)

	# Remove shares for users no longer assigned
	for share in existing_shares:
		if share.user not in technicians:
			frappe.delete_doc(
				"DocShare",
				share.name,
				ignore_permissions=True,
				force=True
			)

	# Update Evaluation Reports
	eval_list = frappe.get_all(
		"Evaluation Report",
		filters={"job_order_data": self.name},
		pluck="name"
	)

	for name in eval_list:
		eval_doc = frappe.get_doc("Evaluation Report", name)
		check_for_shared_docs_on_evaluation(eval_doc)
	
@frappe.whitelist()
def create_evaluation_report(doc_no):
	# Fetch the source document
	doc = frappe.get_doc("Job Order Data", doc_no)

	# Create a new Evaluation Report
	new_doc = frappe.new_doc("Evaluation Report")

	# Direct field mappings from source to target
	field_map = {
		"company": "company",
		"customer": "customer",
		"sales_person": "attn",
		"name": "job_order_data",
		"attach_image": "attach_image",
		# "technician": "technician",
		"parent_jo": "parent_jo",
		"branch": "branch",
		"repair_warehouse": "warehouse",
		"complaints": "customer_complaint",
		"priority_status": "priority_status",
		"item_photo": "attach_image"
	}

	for src_field, target_field in field_map.items():
		new_doc.set(target_field, doc.get(src_field))

	# Set naming series based on branch
	branch_series_map = {
		"Dammam": "EVAL-D.YY.-",
		"Jeddah": "EVAL-J.YY.-",
		"Riyadh": "EVAL-R.YY.-",
		"Kuwait": "EVAL-K.YY.-",
		"Dubai": "EVAL-DU.YY.-"
	}
	new_doc.naming_series = branch_series_map.get(doc.branch, "")

	# Map checkbox fields
	checkbox_fields = [
		"no_power",
		"no_output",
		"not_working",
		"no_display",
		"no_communication",
		"supply_voltage",
		"touch_keypad_not_working",
		"no_backlight",
		"error_code",
		"short_circuit",
		"overload_overcurrent",
		"others"
	]

	for field in checkbox_fields:
		if doc.get(field):
			new_doc.set(field, 1)

	# If "others" is checked, also copy the "specify" field
	if doc.get("others"):
		new_doc.specify = doc.get("specify")

	# Copy items from material_list to evaluation_details
	for item in doc.get("material_list", []):
		new_doc.append("evaluation_details", {
			"item": item.item_code,
			"description": item.item_name,
			"manufacturer": item.mfg,
			"model": item.model_no,
			"serial_no": item.serial_no,
		})

	new_doc.warehouse = warehouse_based_on_branch_and_company(doc.company, doc.branch)

	return new_doc


def update_tech_hours(new_doc, job_order_data):
	eval_report = frappe.db.sql('''select 
		status,
		evaluation_time,
		estimated_repair_time 
	from `tabEvaluation Report` 
		where docstatus = 1 
		and job_order_data = %s 
	order by creation desc limit 1''',job_order_data,as_dict =1)

	if eval_report:
		for report in eval_report:
			evaluation_time = report.get('evaluation_time', 0)
			estimated_repair_time = report.get('estimated_repair_time', 0)
			total_hours = round((evaluation_time + estimated_repair_time) / 3600, 2) if evaluation_time and estimated_repair_time else 0
			new_doc.append("technician_hours_spent", {
				"job_order_data": job_order_data,
				"comments": report.get("status"),
				"total_hours_spent": total_hours,
				"value": 20,
				"total_price": total_hours * 20
			})

	# include child_jo
	child_eval_report = frappe.db.sql('''select 
		job_order_data,
		status,
		evaluation_time,
		estimated_repair_time 
	from `tabEvaluation Report` 
		where docstatus = 1 
		and parent_jo = %s 
	''',job_order_data,as_dict =1)

	if child_eval_report:
		for child_report in child_eval_report:
			evaluation_time = child_report.get('evaluation_time', 0)
			estimated_repair_time = child_report.get('estimated_repair_time', 0)
			total_hours = round((evaluation_time + estimated_repair_time) / 3600, 2) if evaluation_time and estimated_repair_time else 0
			new_doc.append("technician_hours_spent", {
				"job_order_data": child_report.get("job_order_data"),
				"comments": child_report.get("status"),
				"total_hours_spent": total_hours,
				"value": 20,
				"total_price": total_hours * 20
			})

@frappe.whitelist()
def create_internal_quotation(job_order_data, pre_evaluation, customer,replacement):
	doc = frappe.get_doc("Job Order Data",job_order_data)
	new_doc= frappe.new_doc("Quotation")
	new_doc.sales_person = doc.sales_person
	new_doc.pre_evaluation = pre_evaluation
	new_doc.custom_replacement = replacement
	new_doc.naming_series = naming_series["Internal Quotation - Repair"][doc.branch]
	new_doc.company = doc.company
	new_doc.party_name = customer
	new_doc.parent_customer = frappe.db.get_value("Customer",customer,"parent_customer")
	if doc.customer != customer:
		new_doc.child_customer = doc.customer
	new_doc.plant = doc.plant
	new_doc.branch = doc.branch
	new_doc.currency = frappe.db.get_value("Company",doc.company,"default_currency")
	new_doc.selling_price_list = utils.fetch_price_list(doc.company, "selling")
	
	rp_unit = ""
	if replacement == 1:
		rp_unit = doc.name

	new_doc.quotation_type = "Internal Quotation - Repair"
	for i in doc.material_list:
		new_doc.append("items",{
			"item_code":i.item_code,
			"item_name":i.item_name,
			"description":i.item_name,
			"serial_number":i.serial_no,
			"uom":'Nos',
			"qty":i.quantity,
			"model":i.model_no,
			"mfg":i.mfg,
			"job_order_data":doc.name,
			"custom_replacement_unit":rp_unit,
			
			"warehouse":fetch_repair_warehouse(doc.company,doc.branch)
		})
	
	
	
	update_tech_hours(new_doc, job_order_data)
	fetch_item_price_details(new_doc,method="validate")
	

	return new_doc

@frappe.whitelist()
def create_delivery_note(job_order_data, customer):
	doc = frappe.get_doc("Job Order Data",job_order_data)
	new_doc = frappe.new_doc("Delivery Note")
	new_doc.company = doc.company
	new_doc.customer = customer
	if doc.customer != customer:
		new_doc.child_customer = doc.customer
	new_doc.plant = doc.plant
	new_doc.sales_person = doc.sales_person
	new_doc.branch = doc.branch
	new_doc.po_no = doc.po_no
	new_doc.customer_reference_number = (frappe.db.get_value("Quotation", doc.quotation, "customer_reference_number")if doc.quotation else None)
	new_doc.selling_price_list = utils.fetch_price_list(doc.company, "selling")
	new_doc.currency = frappe.db.get_value("Company",doc.company,"default_currency")
	new_doc.cost_center = doc.department
	new_doc.set_warehouse = fetch_repair_warehouse(doc.company,doc.branch)
	new_doc.customer_address = doc.address
	new_doc.contact_person = doc.incharge
	new_doc.job_order_data = job_order_data

	# new_doc.sales_person = frappe.get_value("Sales Person",doc.sales_person,"custom_user")
	quote = []
	for i in doc.get("material_list"):
		qi_details = frappe.db.sql('''select q.name,
			qi.qty as qty,
			qi.rate as rate,
			qi.amount as amount 
		from `tabQuotation Item` as qi 
			inner join `tabQuotation` as q on q.name = qi.parent 
		where qi.item_code = %s
			and q.workflow_state = "Approved By Customer" 
			and qi.job_order_data = %s 
			order by q.creation desc''',(i.item_code,job_order_data),as_dict=1)
		
		qty = i.quantity
		rate = 0
		amount = 0
		if qi_details:
			qty = qi_details[0]['qty']
			rate = qi_details[0]['rate']
			amount = qi_details[0]['amount']
		new_doc.append("items",{
			"item_name":i.item_name,
			"item_code":i.item_code,
			"manufacturer":i.mfg,
			"model":i.model_no,
			"description":i.item_name,			
			"serial_number":i.serial_no,
			"qty":qty,
			"rate":rate,
			"amount":amount,
			"job_order_data":job_order_data,
			"uom":"Nos",
			"stock_uom":"Nos",
			"conversion_factor":1,
			"cost_center":doc.department or frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1}) or "",
			"warehouse":doc.repair_warehouse
		})
		quote.append({
			"item_name":i.item_name,
			"item_code":i.item_code,
			"manufacturer":i.mfg,
			"model":i.model_no,
			"description":i.item_name,
			"qty":qty,
			"rate":rate,
			"amount":amount,
			"serial_number":i.serial_no,
			"job_order_data":job_order_data,
			"uom":"Nos",
			"stock_uom":"Nos",
			"conversion_factor":1,
			"cost_center":doc.department or frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1}) or "",
			"warehouse":doc.repair_warehouse
		})
		return new_doc, quote

@frappe.whitelist()
def create_return_note(job_order_data):
	doc = frappe.get_doc("Job Order Data",job_order_data)
	new_doc = frappe.new_doc("Return Note")
	new_doc.company = doc.company
	new_doc.customer = doc.customer
	new_doc.branch = doc.branch
	new_doc.plant = doc.plant
	branch_series_map = {
		"Dammam": "RE-D-.YY.-",
		"Jeddah": "RE-J-.YY.-",
		"Riyadh": "RE-R-.YY.-",
		"Kuwait": "RE-K-.YY.-",
		"Dubai": "RE-DU-.YY.-"
	}
	new_doc.naming_series = branch_series_map.get(doc.branch, "")
	new_doc.cost_center = doc.department
	new_doc.warehouse = fetch_repair_warehouse(doc.company, doc.branch)
	new_doc.customer_address = doc.address
	new_doc.contact_person = doc.incharge
	new_doc.job_order_data = job_order_data
	new_doc.status = "Return"
	new_doc.is_return = 1

	for i in doc.material_list:
		new_doc.append("items",{
			"item_name":i.item_name,
			"item_code":i.item_code,
			"manufacturer":i.mfg,
			"model":i.model_no,
			"rate":0,
			"amount":0, 
			"description":i.item_name,
			"qty":i.quantity,
			"job_order_data":doc.name, 
			"uom":"Nos",
			"stock_uom":"Nos",
			"conversion_factor":1,
			"cost_center":frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1}) or "",
			"warehouse":fetch_repair_warehouse(doc.company, doc.branch)
		})
	return new_doc



@frappe.whitelist()
def fetch_repair_warehouse(company,branch):	
	warehouse = frappe.db.get_value("Warehouse List",{"branch":branch,"parent":company},["repair_warehouse"])

	return warehouse

@frappe.whitelist()
def fetch_payment_details(name):
	data = frappe.db.sql("""
		SELECT 
			t.parent AS payment_entry,
			t.allocate_amount AS amount,
			p.posting_date,
			p.paid_to_account_currency AS currency
		FROM `tabJob Order table` t
		JOIN `tabPayment Entry` p
			ON p.name = t.parent
		WHERE 
			t.parenttype = 'Payment Entry'
			AND t.reference_type = 'Job Order Data'
			AND t.reference_name = %s
			AND p.docstatus = 1
	""", (name), as_dict=True)
	return data


@frappe.whitelist()
def get_eval_list(job_order_data):
	return fetch_eval_list([], job_order_data)


def fetch_eval_list(eval_list, job_order_data):
	child_jo_list = frappe.get_all(
		'Job Order Data',
		filters={'parent_jo': job_order_data, 'docstatus': 1},
		fields=['name']
	)

	eval_list = [job_order_data] + [child['name'] for child in child_jo_list]
	return eval_list


@frappe.whitelist()
def get_or_create_item(i):

	new_doc = frappe.new_doc('Item')
	new_doc.item_name = i['item_name']
	new_doc.item_group = "Equipments"
	new_doc.description = i['item_name']
	new_doc.model = i['model']
	new_doc.is_stock_item = 1
	new_doc.mfg = i['mfg']
	new_doc.insert(ignore_permissions=True)

	return new_doc.name

@frappe.whitelist()
def change_or_create_item(job_order_data, row_name, values):

	values = frappe.parse_json(values)

	jod = frappe.get_doc("Job Order Data", job_order_data)
	row = next(d for d in jod.material_list if d.name == row_name)

	old_item = row.item_code

	# 1️⃣ Check if stock entry exists
	stock_entry = frappe.db.get_value(
		"Stock Entry",
		{"job_order_data": jod.name, "docstatus": 1},
		"name"
	)
	
	if values.get("action") == "update":
		# Safe to update
		item = frappe.get_doc("Item", old_item)
		item.model = values.get("model")
		item.mfg = values.get("mfg")
		item.description = values.get("description")
		item.save(ignore_permissions=True)

		frappe.msgprint("Item updated successfully.")
		return

	# -------- CREATE NEW ITEM -------- #

	new_item = get_or_create_item(values)

	# Cancel linked stock entry if exists
	stock_entry = frappe.db.get_value(
		"Stock Entry",
		{"job_order_data": jod.name, "docstatus": 1},
		"name"
	)

	if stock_entry:
		se = frappe.get_doc("Stock Entry", stock_entry)
		se.cancel()

	# Update WOD row
	row.item_code = new_item
	row.model = values.get("model")
	row.mfg = values.get("mfg")

	jod.save(ignore_permissions=True)

	
	eval_list = frappe.db.get_list("Evaluation Report",{"job_order_data":jod.name},["name"])
	for eval in eval_list:
		er = frappe.get_doc("Evaluation Report",eval.name)
		for item in er.evaluation_details:
			if item.item == old_item:
				item.item = new_item
				item.model = values.get("model")
				item.manufacturer = values.get("mfg")
				item.serial_no = row.get("serial_no")
		er.save(ignore_permissions=True)

	
	
	frappe.errprint(f"Updated JOD {jod.name} row {row.name} with new item {new_item}")
	# Recreate stock entry
	if stock_entry:
		create_stock_entry_jod(jod.name)

	frappe.msgprint("New Item created and replaced successfully.")

def create_stock_entry_jod(jod_name):
	jod = frappe.get_doc("Job Order Data", jod_name)
	new_doc = frappe.new_doc("Stock Entry")
	new_doc.posting_date = jod.creation
	new_doc.set_posting_time = 1
	new_doc.stock_entry_type = "Material Receipt"
	new_doc.company = jod.company
	new_doc.branch = jod.branch
	new_doc.job_order_data = jod.name
	for i in jod.material_list:
		new_doc.append("items", {
			't_warehouse': jod.repair_warehouse,
			'item_code': i.item_code,
			'item_name': i.item_name,
			'description': i.item_name,
			# 'serial_no': i.serial_no,
			'custom_serial_no': i.serial_no,
			'qty': i.quantity,
			'uom': frappe.db.get_value("Item", i.item_code, 'stock_uom'),
			'conversion_factor': 1,
			'allow_zero_valuation_rate': 1
		})
		sn_exist = frappe.db.exists("Serial Number",i.serial_no)
		if sn_exist:
			sn_doc = frappe.get_doc("Serial Number",i.serial_no)
			sn_doc.serial_no = i.serial_no or ''
			sn_doc.item_code = i.item_code
			sn_doc.status = "Active"
			sn_doc.save(ignore_permissions=True)
	new_doc.save(ignore_permissions=True)
	if new_doc.name:
		new_doc.submit()


@frappe.whitelist()
def change_serial_number(job_order_data, row_name, new_serial_no):

	jod = frappe.get_doc("Job Order Data", job_order_data)
	row = next(d for d in jod.material_list if d.name == row_name)

	old_serial_no = row.serial_no
	row.serial_no = new_serial_no
	jod.save(ignore_permissions=True)
	if old_serial_no and old_serial_no != new_serial_no:
		# try deleting old serial number and if not possible, update it with new serial number
		frappe.db.delete("Serial Number", old_serial_no)
		sn_doc = frappe.new_doc("Serial Number")
		sn_doc.item_code = row.item_code
		sn_doc.status = "Active"
		sn_doc.company = jod.company
		sn_doc.serial_no = new_serial_no
		sn_doc.save(ignore_permissions=True)

		frappe.msgprint("Serial Number updated successfully.")

	
		eval_list = frappe.db.get_list("Evaluation Report",{"job_order_data":jod.name},["name"])
		for eval in eval_list:
			frappe.db.set_value("Evaluation Item",{"parent":eval.name,"item":row.item_code,"serial_no":old_serial_no},"serial_no",new_serial_no)

	# if there is no old serial number, just create a new one
	elif new_serial_no:
		sn_doc = frappe.new_doc("Serial Number")
		sn_doc.item_code = row.item_code
		sn_doc.status = "Active"
		sn_doc.company = jod.company
		sn_doc.serial_no = new_serial_no
		sn_doc.save(ignore_permissions=True)

		frappe.msgprint("Serial Number created successfully.")


def update_jo_state():
	jo_list = frappe.get_all("Job Order Data",{"docstatus":1},["name"])
	for jo in jo_list:
		self = frappe.get_doc("Job Order Data", jo.name)

		if not self.delivery:
			unit_status = "In Lab"

		elif not self.returned_date:
			unit_status = "With Customer"

		elif self.delivery >= self.returned_date:
			unit_status = "With Customer"

		else:
			unit_status = "In Lab"
		frappe.db.set_value("Job Order Data", self.name, "unit_status", unit_status, update_modified=False)

# def updates():
# 	jo_list = frappe.get_all("Job Order Data",{"company":"Company Al-Halloul Faniye Medical","docstatus":2,"technician":["is", "not set"]},["name"])
# 	for jo in jo_list:
# 		print(jo.name)
# 		# dl = frappe.get_doc("Document Log", {"document_reference":jo.name})
# 		# dl.delete()
# 		frappe.db.set_value("Stock Entry Detail", {"job_order_data": jo.name}, "job_order_data", None, update_modified=False)
# 		frappe.db.set_value("Stock Entry", {"job_order_data": jo.name}, "job_order_data", None, update_modified=False)
# 		frappe.db.set_value("Stock Entry", {"job_order_data": jo.name}, "job_order_data", None, update_modified=False)
# 		self = frappe.get_doc("Job Order Data", jo.name)
# 		self.delete()
# 		frappe.db.commit()

def update_rfq():
	rfq_list = frappe.get_all("Purchase Order Item",{"branch": ["is", "not set"]},["name","parent","supply_order_data","job_order_data"])
	for rfq in rfq_list:
		# if rfq.job_order_data:
		# 	jo_doc = frappe.get_doc("Job Order Data", rfq.job_order_data)
		branch = frappe.db.get_value("Purchase Order", rfq.parent, "branch")
		print(branch)
		frappe.db.set_value("Purchase Order Item", rfq.name, "branch",branch, update_modified=False)
		# elif rfq.supply_order_data:
		# 	so_doc = frappe.get_doc("Supply Order Data", rfq.supply_order_data)
		# 	frappe.db.set_value("Purchase Order Item", rfq.name, "branch", so_doc.branch, update_modified=False)
		# frappe.db.set_value("Request for Quotation", rfq.name, "branch", "Kuwait", update_modified=False)

@frappe.whitelist()
def create_rfq_from_jo(name):
	doc = frappe.get_doc("Job Order Data",name)
	rfq = frappe.new_doc("Request for Quotation")
	rfq.company = doc.company
	rfq.branch = frappe.db.get_value("Job Order Data",doc.name,"branch")
	rfq.job_order_data = doc.name
	rfq.cost_center = frappe.db.get_value("Job Order Data",doc.name,"department") or frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1})
	# rfq.schedule_date = add_to_date(rfq.transaction_date,days = 2)
	rfq.maintenance_contract = doc.get("maintenance_contract")
	rfq.items=[]
	warehouse = warehouse_based_on_branch_and_company(rfq.company,rfq.branch)
	for i in doc.get("material_list"):
		item = frappe.db.get_value(
			"Item",
			{"name": i.item_code},
			["item_name", "description"],
			as_dict=True
		)

		item_name = item.item_name if item else ""
		description = item.description if item else ""			
		rfq.append("items",{
				"item_code":i.item_code,
				"item_name":item_name,
				"description":description,
				'model':i.model_no,
				"mfg":i.mfg,
				"uom":"Nos",
				"stock_uom":"Nos",
				"conversion_factor":1,
				"stock_qty":i.get('quantity') or 1,
				"qty":i.get('quantity') or 1,
				# "schedule_date":add_to_date(rfq.transaction_date,days = 2),
				"warehouse":warehouse,
				"branch":rfq.branch,
				"parent_jo":doc.parent_jo,
				"job_order_data":doc.name,
				"cost_center":frappe.db.get_value("Job Order Data",doc.name,"department") or frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1}),
				"maintenance_contract":doc.get("maintenance_contract")
			})

	return rfq

# Create Supply Order Data from Job Order Data
@frappe.whitelist()
def create_supply_order_data(job_order_data):
	
	so_naming_series = {
		"Dammam": {
			"Supply":"SO-D.YY.-",
			"tender":"ST-D.YY.-"
		},
		"Riyadh": {
			"Supply":"SO-R.YY.-",
			"tender":"ST-R.YY.-"
		},
		"Jeddah": {
			"Supply":"SO-J.YY.-",
			"Tender":"ST-J.YY.-"
		},
		"Kuwait": {
			"Supply":"SO-K.YY.-",
			"Tender":"ST-K.YY.-"
		},
		"Dubai": {
			"Supply":"SO-DU.YY.-",
			"Tender":"ST-DU.YY.-"
		},
	}
	doc = frappe.get_doc("Job Order Data", job_order_data)
	so = frappe.new_doc("Supply Order Data")
	so.naming_series = so_naming_series[doc.branch]["Supply"]
	so.department = frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_supply":1}) or ""
	so.customer = doc.customer
	so.customer_name = doc.customer_name
	so.document_type = "Supply"
	so.sales_person = doc.sales_person
	so.incharge = doc.incharge
	if doc.priority_status == "Normal":
		so.priority_status = "Not Urgent"
	else:
		so.priority_status = doc.priority_status
	so.branch = doc.branch
	so.job_order_data = doc.name
	so.warehouse = frappe.db.get_value('Warehouse', {'is_repair_warehouse':0,'company':doc.company,"name":["like","%"+doc.branch+"%"]}, 'name')
	for i in doc.get("material_list"):
		so.append("material_list",{
			"item_code": i.get('item_code'),
			"item_name":i.get('item_name'),
			"item_group":frappe.db.get_value("Item",i.get('item_code'),"item_group"),
			"unit": frappe.db.get_value("Item",i.get('item_code'),"stock_uom"),
			"description":i.get('description') or i.get('item_name'),
			"model_no":i.get('model_no', ""),
			"mfg":i.get('mfg'),
			"quantity":i.get('quantity', 0),
		})

	return so

@frappe.whitelist()
def create_received_unit(job_order_data, serial_number, attach_image):
	if attach_image:
		frappe.db.set_value("Job Order Data", job_order_data,"attach_image",attach_image.replace(" ","%20"), update_modified = False)
	doc = frappe.get_doc("Job Order Data",job_order_data)
	se_doc = frappe.new_doc("Stock Entry")
	se_doc.stock_entry_type = "Material Receipt"
	se_doc.company = doc.company
	se_doc.branch = doc.branch
	se_doc.to_warehouse = doc.repair_warehouse
	se_doc.job_order_data = doc.name
	for i in doc.material_list:
		if serial_number:
			s_number = frappe.db.exists("Serial Number",{"name":serial_number})
			if s_number:
				sn_doc = frappe.get_doc("Serial Number",serial_number)
				sn_doc.item_code = i.item_code
				sn_doc.status = "Active"
				sn_doc.save()
				
			else:
				sn_doc = frappe.new_doc("Serial Number")
				sn_doc.serial_no = serial_number
				sn_doc.item_code = i.item_code
				sn_doc.company = doc.company
				sn_doc.status = "Active"
				sn_doc.save(ignore_permissions=True)
				frappe.db.set_value('Material List',{'name':i.name,"parenttype":"Job Order Data"},"serial_no",sn_doc.name, update_modified = False)

		se_doc.append("items",{
			't_warehouse': doc.repair_warehouse,
			'item_code':i.item_code,
			'item_name':i.item_name,
			'description':i.description,
			'serial_number':i.get('serial_no') or serial_number,
			'qty':1,
			'uom':frappe.db.get_value("Item",i.item_code,'stock_uom') or "Nos",
			'branch':doc.branch,
			'cost_center':frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1}) or "",
			'job_order_data':doc.name,
			'conversion_factor':1,
			'allow_zero_valuation_rate':1
		})
	se_doc.save(ignore_permissions = True)
	if se_doc.name:
		try:
			se_doc.submit()
			frappe.db.set_value("Job Order Data",job_order_data,"unit_status","In Lab", update_modified = False)
		except Exception as e:
			frappe.log_error(frappe.get_traceback())
		pass