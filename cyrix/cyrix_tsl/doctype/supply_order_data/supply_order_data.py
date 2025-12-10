# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date
from datetime import datetime


class SupplyOrderData(Document):	
	def update_qty(self):
		total_quantity = 0
		for i in self.get("material_list"):
			total_quantity += int(i.quantity)
		self.quantity = total_quantity
		frappe.db.set_value("Supply Order Data",self.name,'quantity',total_quantity,update_modified=False)

	def validate(self):
		self.update_qty()

	def before_submit(self):		
		now = datetime.now()
		self.append("status_duration_details",{
			"status":self.status,
			"date":now,
		})
		self.update_qty()
		
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
			doc = frappe.get_doc("Supply Order Data",self.name)
			doc.append("status_duration_details",{
				"status":self.status,
				"date":now,
			})
			doc.save(ignore_permissions=True)
		self.update_qty()

@frappe.whitelist()
def create_rfq(supply_order_data):
	doc = frappe.get_doc("Supply Order Data",supply_order_data)
	rfq = frappe.new_doc("Request for Quotation")
	rfq.company = doc.company
	rfq.branch = frappe.db.get_value("Supply Order Data",supply_order_data,"branch")
	rfq.supply_order_data = supply_order_data
	rfq.schedule_date = add_to_date(rfq.transaction_date,days = 2),
	rfq.department = doc.department
	rfq.items=[]
	warehouse = warehouse_based_on_branch_and_company(rfq.company,rfq.branch)
	for i in doc.get("material_list"):
		rfq.append("items",{
			"item_code":i.item_code,
			"item_name":i.description,
			"description":i.description,
			'model':i.model_no,
			"mfg":i.mfg,
			"uom":"Nos",
			"stock_uom":"Nos",
			"conversion_factor":1,
			"stock_qty":1,
			"qty":i.quantity,
			"schedule_date":add_to_date(rfq.transaction_date,days = 2),
			"warehouse":warehouse,
			"branch":rfq.branch,
			"supply_order_data":supply_order_data,
			"department":frappe.db.get_value("Supply Order Data",supply_order_data,"department")
		})

	return rfq

@frappe.whitelist()
def warehouse_based_on_branch_and_company(company,branch):
	warehouse = frappe.db.get_value("Warehouse List",{"branch":branch,"parent":company},["actual_warehouse"])
	return warehouse

from cyrix.custom_py.quotation import fetch_item_price_details
@frappe.whitelist()
def create_internal_quotation(supply_order_data):
	doc = frappe.get_doc("Supply Order Data",supply_order_data)
	new_doc= frappe.new_doc("Quotation")
	new_doc.sales_person = doc.sales_person
	if doc.branch:
		d = {
			"Internal Quotation - Supply":{
				"Kuwait":"IQS-K.YY.-",
				"Dammam":"IQS-D.YY.-",
				"Riyadh":"IQS-R.YY.-",
				"Jeddah":"IQS-J.YY.-",
				"Dubai":"IQS-DU.YY.-"
			},
			"Customer Quotation - Supply":{
				"Kuwait":"CQS-K.YY.-",
				"Dammam":"CQS-D.YY.-",
				"Riyadh":"CQS-R.YY.-",
				"Jeddah":"CQS-J.YY.-",
				"Dubai":"CQS-DU.YY.-"
			},
		}
	if new_doc.quotation_type:
		new_doc.naming_series = d[new_doc.quotation_type][doc.branch]
	new_doc.company = doc.company
	new_doc.party_name = doc.customer
	new_doc.plant = doc.plant
	new_doc.branch = doc.branch
	new_doc.quotation_type = "Internal Quotation - Supply"
	for i in doc.material_list:
		new_doc.append("items",{
			"item_code":i.item_code,
			"item_name":i.description,
			"description":i.description,
			"uom":'Nos',
			"qty":i.quantity,
			"model_no":i.model_no,
			"supply_order_data":doc.name,
			"warehouse":doc.warehouse
		})
	fetch_item_price_details(new_doc,method="validate")
	return new_doc



@frappe.whitelist()
def create_delivery_note(supply_order_data):
	doc = frappe.get_doc("Supply Order Data",supply_order_data)
	new_doc = frappe.new_doc("Delivery Note")
	new_doc.company = doc.company
	new_doc.customer = doc.customer
	new_doc.branch = doc.branch
	new_doc.department = doc.department
	new_doc.set_warehouse = doc.warehouse
	new_doc.purchase_order_no = doc.po_no
	new_doc.supply_order_data = doc.name
	new_doc.custom_sales_person = doc.sales_person
	new_doc.currency = frappe.db.get_value("Company",doc.company,"default_currency")
	list_ = []
	for i in doc.get("material_list"):
		remaining_qty = float(i.quantity) - float(i.delivered_quantity)
		if remaining_qty > 0:
			new_doc.append("items",{
				"item_name":i.item_name or i.description,
				"item_code":i.item_code,
				"manufacturer":i.mfg,
				"model":i.model_no,
				"rate":i.quoted_price,
				"amount":i.quoted_amount, 
				"serial_number":i.serial_no,
				"description":i.description,
				"qty":remaining_qty,
				"supply_order_data":supply_order_data,
				"uom":"Nos",
				"stock_uom":"Nos",
				"conversion_factor":1,
				"cost_center":doc.department,
				"income_account":"",
				"branch":doc.branch
			})
			list_.append({
				"item_name":i.item_name or i.description,
				"item_code":i.item_code,
				"manufacturer":i.mfg,
				"model":i.model_no,
				"rate":i.quoted_price,
				"amount":i.quoted_amount, 
				"serial_number":i.serial_no,
				"description":i.description,
				"qty":remaining_qty,
				"supply_order_data":supply_order_data,
				"uom":"Nos",
				"stock_uom":"Nos",
				"conversion_factor":1,
				"cost_center":doc.department,
				"income_account":"",
				"branch":doc.branch
			})
	return new_doc,list_


@frappe.whitelist()
def create_sales_invoice(supply_order_data):
	doc = frappe.get_doc("Supply Order Data",supply_order_data)
	new_doc = frappe.new_doc("Sales Invoice")
	new_doc.company = doc.company
	new_doc.customer = doc.customer
	new_doc.branch = doc.branch
	new_doc.department = doc.department
	new_doc.supply_order_data = supply_order_data
	new_doc.sales_person = doc.sales_person
	new_doc.currency = frappe.db.get_value("Company",doc.company,"default_currency")
	new_doc.cost_center = doc.department
	sales_invoice_list = []
	for i in doc.get("material_list"):
		qi_details = frappe.db.sql('''select 
			q.valid_till as valid_till,
			q.name,qi.qty as qty,
			qi.rate as rate,
			qi.amount as amount 
		from `tabQuotation Item` as qi 
			inner join `tabQuotation` as q on q.name = qi.parent 
		where qi.item_code = %s 
			and q.workflow_state = "Approved By Customer" 
			and qi.supply_order_data = %s 
			and q.docstatus = 1 
			order by q.modified desc limit 1''',(i.item_code,supply_order_data),as_dict=1)
		r = 0
		amt = 0
		qty = i.quantity
		if qi_details:
			r = qi_details[0]['rate']
			amt = qi_details[0]['amount']
			qty = qi_details[0]['qty']
			new_doc.due_date = qi_details[0]['valid_till']
		new_doc.append("items",{
			"item_name":i.item_name,
			"item_code":i.item_code,
			"manufacturer":i.mfg,
			"model":i.model_no,
			"rate":r,
			"amount":amt, 
			"serial_number":i.serial_no,
			"description":i.description,
			"qty":qty,
			"supply_order_data":supply_order_data,
			"uom":"Nos",
			"stock_uom":"Nos",
			"conversion_factor":1,
			"cost_center":frappe.db.get_value("Cost Center",{'cost_center_name':"Main",'company':doc.company}),
			"income_account":"",
			"branch":doc.branch
		})
		sales_invoice_list.append({
			"item_name":i.item_name,
			"item_code":i.item_code,
			"manufacturer":i.mfg,
			"model":i.model_no,
			"rate":r,
			"amount":amt, 
			"serial_number":i.serial_no,
			"description":i.description,
			"qty":qty,
			"supply_order_data":supply_order_data,
			"uom":"Nos",
			"stock_uom":"Nos",
			"conversion_factor":1,
			"cost_center":frappe.db.get_value("Cost Center",{'cost_center_name':"Main",'company':doc.company}),
			"income_account":"",
			"branch":doc.branch
		})

	return new_doc,sales_invoice_list


def list_desk():
	list = frappe.db.get_all("Desktop Icon","name")
	doc = frappe.get_doc("Desktop Icon","CYRIX")
	doc.delete()
	print(list)