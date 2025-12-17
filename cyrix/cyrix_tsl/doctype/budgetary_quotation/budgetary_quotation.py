# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from cyrix.cyrix_tsl.doctype.evaluation_report.evaluation_report import warehouse_based_on_branch_and_company
from datetime import datetime

class BudgetaryQuotation(Document):
	def update_qty(self):
		total_qty = 0
		for i in self.get("items"):
			total_qty += int(i.qty)
		self.quantity = total_qty
		frappe.db.set_value("Budgetary Quotation",self.name,'quantity',total_qty,update_modified=False)
	
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
			doc = frappe.get_doc("Budgetary Quotation",self.name)
			doc.append("status_duration_details",{
				"status":self.status,
				"date":now,
			})
			doc.save(ignore_permissions=True)
		self.update_qty()

	@frappe.whitelist()
	def create_quotation(self):
		new_doc= frappe.new_doc("Quotation")
		new_doc.company = self.company
		new_doc.party_name = self.customer
		new_doc.currency = frappe.db.get_value("Company",self.company,"default_currency")
		new_doc.customer_name = frappe.db.get_value("Customer",self.customer,"customer_name")
		new_doc.sales_person = self.sales_person
		new_doc.branch = self.branch
		new_doc.budgetary_quotation = self.name
		new_doc.quotation_type = "Internal Quotation - BQ"
		for i in self.items:
			new_doc.append("items",{
				"item_code":i.sku,
				"item_name":i.description,
				"description":i.description,
				"uom":'Nos',
				"qty":i.qty,
				"model_no":i.model,
				"mfg":i.mfg,
				"budgetary_quotation":self.name,
			})
			
		return new_doc

	@frappe.whitelist()
	def create_rfq(self):
		new_doc= frappe.new_doc("Request for Quotation")
		new_doc.company = self.company
		new_doc.branch = self.branch
		new_doc.budgetary_quotation = self.name
		for i in self.items:
			new_doc.append("items",{
				"item_code":i.sku,
				"item_name":i.description,
				"description":i.description,
				"stock_uom":'Nos',
				"uom":"Nos",
				"qty":i.qty,
				"model":i.model,
				"mfg":i.mfg,
				"budgetary_quotation":self.name,
				"branch":self.branch,
				"conversion_factor":1,
				"warehouse":warehouse_based_on_branch_and_company(self.company,self.branch)
			})
			
		return new_doc


@frappe.whitelist()
def create_delivery_note(budgetary_quotation):
	doc = frappe.get_doc("Budgetary Quotation",budgetary_quotation)
	new_doc = frappe.new_doc("Delivery Note")
	new_doc.company = doc.company
	new_doc.customer = doc.customer
	new_doc.branch = doc.branch
	new_doc.department = frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_supply":1}) or ""
	new_doc.set_warehouse = warehouse_based_on_branch_and_company(doc.company,doc.branch)
	new_doc.purchase_order_no = doc.po_no
	new_doc.budgetary_quotation = doc.name
	new_doc.custom_sales_person = doc.sales_person
	new_doc.currency = frappe.db.get_value("Company",doc.company,"default_currency")
	list_ = []
	for i in doc.get("items"):
		remaining_qty = float(i.qty) - float(i.delivered_qty)
		if remaining_qty > 0:
			new_doc.append("items",{
				"item_name":i.description,
				"item_code":i.sku,
				"manufacturer":i.mfg,
				"model":i.model,
				"rate":i.quoted_price,
				"amount":i.quoted_amount, 
				"description":i.description,
				"qty":remaining_qty,
				"budgetary_quotation":budgetary_quotation,
				"uom":"Nos",
				"stock_uom":"Nos",
				"conversion_factor":1,
				"cost_center":frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_supply":1}) or "",
				"income_account":"",
				"branch":doc.branch
			})
			list_.append({
				"item_name":i.description,
				"item_code":i.sku,
				"manufacturer":i.mfg,
				"model":i.model,
				"rate":i.quoted_price,
				"amount":i.quoted_amount, 
				"description":i.description,
				"qty":remaining_qty,
				"budgetary_quotation":budgetary_quotation,
				"uom":"Nos",
				"stock_uom":"Nos",
				"conversion_factor":1,
				"cost_center":frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_supply":1}) or "",
				"income_account":"",
				"branch":doc.branch
			})
	return new_doc,list_

	
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
			AND t.reference_type = 'Budgetary Quotation'
			AND t.reference_name = %s
			AND p.docstatus = 1
	""", (name), as_dict=True)
	return data
