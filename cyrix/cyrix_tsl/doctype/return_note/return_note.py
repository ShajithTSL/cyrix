# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime

class ReturnNote(Document):
	def on_submit(self):
		self.update_job_order_status()
		self.create_stock_entry()

	def on_update_after_submit(self):
		self.update_job_order_status()

	def on_cancel(self):
		self.create_reverse_entry()

	def update_job_order_status(self):
		for jo in self.items:
			doc = frappe.get_doc("Job Order Data",jo.job_order_data)
			if doc.status == "RNP-Return No Parts":
				doc.status = "RNPC-Return No Parts Client"
				
			if doc.status == "RNA-Return Not Approved":
				doc.status = "RNAC-Return Not Approved Client"

			if doc.status == "RNR-Return Not Repaired":
				doc.status = "RNRC-Return Not Repaired Client"

			if doc.status == "RNF-Return No Fault":
				doc.status = "RNFC-Return No Fault Client"

			if doc.status == "C-Comparison":
				doc.status = "CC-Comparison Client"
		
			doc.return_note = self.name
			frappe.log_error("type",type(self.posting_date))
			doc.delivery = datetime.strptime(str(self.posting_date), "%Y-%m-%d").date()
			doc.return_note_date = self.posting_date
			doc.save(ignore_permissions = 1)
	
	def create_stock_entry(self):
		for jo in self.items:
			doc = frappe.get_doc("Job Order Data",jo.job_order_data)
			se = frappe.new_doc("Stock Entry")
			se.stock_entry_type = "Material Issue"
			se.company = doc.company
			se.branch = doc.branch
			se.from_warehouse = doc.repair_warehouse
			se.job_order_data = doc.name
			for i in doc.material_list:
				se.append("items",{
					's_warehouse': doc.repair_warehouse,
					'item_code':i.item_code,
					'item_name':i.item_name,
					'description':i.item_name,
					'qty':i.quantity,
					'uom':frappe.db.get_value("Item",i.item_code,'stock_uom') or "Nos",
					'branch':doc.branch,
					'cost_center':frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1}) or "",
					'job_order_data':doc.name,
					'conversion_factor':1,
					'allow_zero_valuation_rate':1
				})
			se.save(ignore_permissions = True)
			se.submit()

	def create_reverse_entry(self):
		for jo in self.items:
			doc = frappe.get_doc("Job Order Data",jo.job_order_data)
			frappe.db.sql('''update `tabJob Order Data` set status = %s where name = %s ''',("NE-Need Evaluation",jo.job_order_data))
			se_doc = frappe.new_doc("Stock Entry")
			se_doc.stock_entry_type = "Material Receipt"
			se_doc.company = doc.company
			se_doc.branch = doc.branch
			se_doc.from_warehouse = doc.repair_warehouse
			se_doc.job_order_data = doc.name
			for i in doc.material_list:
				se_doc.append("items",{
					't_warehouse': doc.repair_warehouse,
					'item_code':i.item_code,
					'item_name':i.item_name,
					'description':i.item_name,
					'qty':i.quantity,
					'uom':frappe.db.get_value("Item",i.item_code,'stock_uom') or "Nos",
					'branch':doc.branch,
					'cost_center':frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1}) or "",
					'job_order_data':doc.name,
					'conversion_factor':1,
					'allow_zero_valuation_rate':1
				})
			se_doc.save(ignore_permissions = True)
			se_doc.submit()
	