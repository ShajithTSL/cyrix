# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
from cyrix.custom_py.quotation import fetch_item_price_details
from cyrix.custom_py import utils

from cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report import warehouse_based_on_branch_and_company
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
		"technician": "technician",
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

@frappe.whitelist()
def create_internal_quotation(job_order_data):
	doc = frappe.get_doc("Job Order Data",job_order_data)
	new_doc= frappe.new_doc("Quotation")
	new_doc.sales_person = doc.sales_person
	new_doc.naming_series = naming_series["Internal Quotation - Repair"][doc.branch]
	new_doc.company = doc.company
	new_doc.party_name = doc.customer
	new_doc.plant = doc.plant
	new_doc.branch = doc.branch
	new_doc.currency = frappe.db.get_value("Company",doc.company,"default_currency")
	new_doc.selling_price_list = utils.fetch_price_list(doc.company, "selling")

	new_doc.quotation_type = "Internal Quotation - Repair"
	for i in doc.material_list:
		new_doc.append("items",{
			"item_code":i.item_code,
			"item_name":i.item_name,
			"description":i.item_name,
			"uom":'Nos',
			"qty":i.quantity,
			"model_no":i.model_no,
			"job_order_data":doc.name,
			"warehouse":fetch_repair_warehouse(doc.company,doc.branch)
		})

	eval_report = frappe.db.sql('''select 
		status,
		evaluation_time,
		estimated_repair_time 
	from `tabEvaluation Report` 
		where docstatus = 1 
		and job_order_data = %s 
	order by creation desc limit 1''',job_order_data,as_dict =1)

	if eval_report:
		report = eval_report[0]
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
	fetch_item_price_details(new_doc,method="validate")
	return new_doc

@frappe.whitelist()
def create_delivery_note(job_order_data):
	doc = frappe.get_doc("Job Order Data",job_order_data)
	new_doc = frappe.new_doc("Delivery Note")
	new_doc.company = doc.company
	new_doc.customer = doc.customer
	new_doc.plant = doc.plant
	new_doc.custom_sales_person = doc.sales_person
	new_doc.branch = doc.branch
	new_doc.selling_price_list = utils.fetch_price_list(doc.company, "selling")
	new_doc.department = frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1}) or "",
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
			"qty":qty,
			"rate":rate,
			"amount":amount,
			"job_order_data":job_order_data,
			"uom":"Nos",
			"stock_uom":"Nos",
			"conversion_factor":1,
			"cost_center":frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1}) or "",
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
			"job_order_data":job_order_data,
			"uom":"Nos",
			"stock_uom":"Nos",
			"conversion_factor":1,
			"cost_center":frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1}) or "",
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
	new_doc.department = doc.department
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
