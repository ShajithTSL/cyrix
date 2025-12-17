# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from frappe.utils import add_to_date

class EvaluationReport(Document):
	@frappe.whitelist()
	def update_availability_status(self):
		for i in self.items:
			if i.part:
				if frappe.db.exists("Bin",{'item_code':i.part,'warehouse':self.warehouse}):
					bin = frappe.db.get_value("Bin",{'item_code':i.part,'warehouse':self.warehouse},'actual_qty')
					price = frappe.db.get_value("Bin", {"item_code": i.part,'warehouse':self.warehouse}, "valuation_rate") or frappe.db.get_value("Item Price", {"item_code": i.part, "buying": 1}, "price_list_rate") or 0
					if float(bin) >= float(i.qty):
						status = "Yes"
						i.parts_availability = status
						i.price_ea = price
						total = price * i.qty
						i.total = total

						frappe.db.sql('''update `tabPart Sheet Item` set parts_availability = '{0}', price_ea = {1}, total = {2} where name ='{3}' '''.format(status,price,total,i.name))
					else:
						i.parts_availability = "No"
						frappe.db.sql('''update `tabPart Sheet Item` set parts_availability = '{0}'  where name ='{1}' '''.format("No",i.name))


		self.check_stock_availability() # to update the stock availability
		self.update_job_order_status() # to update the Job Order Data status

	def validate(self):
		self.update_part_sheet_number()

	def update_part_sheet_number(self):
		for i in self.items:
			if not i.part_sheet_no:
				i.part_sheet_no = 1

	def update_part_no(self):
		if self.if_parts_required:
			self.part_no = 0
			for i in self.get("items"):
				if not i.part_sheet_no:
					i.part_sheet_no = int(self.part_no)+1
					frappe.db.sql('''update `tabPart Sheet Item` set part_sheet_no = %s where name = %s''',((int(self.part_no)+1),i.name))
				self.part_no = i.part_sheet_no
				frappe.db.sql('''update `tabEvaluation Report` set part_no = %s where name = %s''',((int(i.part_sheet_no)),self.name))
		
		if int(self.items[-1].part_sheet_no) > int(1) and self.status in ["Spare Parts","Comparison","Extra Parts","Internal Extra Parts"] and self.ner_field != "NER-Need Evaluation Return":
			self.status = "Internal Extra Parts"
			frappe.db.sql('''update `tabEvaluation Report` set status = %s where name = %s ''',("Internal Extra Parts",self.name))
			if self.document_active_status == "Yes":
				wd = frappe.get_doc("Job Order Data",self.job_order_data)
				wd.status = "IP-Internal Extra Parts"
				wd.save(ignore_permissions = 1)
			
	def after_insert(self):		
		doc = frappe.get_doc("Job Order Data",self.job_order_data)
		doc.status = "UE-Under Evaluation"
		doc.save(ignore_permissions = True)
		
	def validate_evaluation_time(self):
		if not self.evaluation_time or not self.estimated_repair_time:
			frappe.throw("Note: Evaluation Time and Estimated Repair Time is not given.")
		self.check_stock_availability() # to update the stock availability

	def before_submit(self):
		self.validate_evaluation_time()
		
	def on_submit(self):
		if self.if_parts_required:
			self.update_job_order_status() # to update the Job Order Data status

	def on_update_after_submit(self):
		self.check_stock_availability() # to update the stock availability
		self.update_job_order_status() # to update the Job Order Data status
		self.update_part_no()

	def check_stock_availability(self):
		# based on the stock availability check in child table rows, overall availability is defined
		if self.if_parts_required:
			check =0
			for i in self.get("items"):
				if i.parts_availability == "No" and not i.from_scrap:
					check=1
			if check:
				self.parts_availability = "No"
				frappe.db.set_value("Evaluation Report",self.name,'parts_availability',"No",update_modified = False)
			else:
				self.parts_availability = "Yes"
				frappe.db.set_value("Evaluation Report",self.name,'parts_availability',"Yes",update_modified = False)

	def update_jo_status_after_purchase_receipt(self):
		# based on the stock availability check in child table rows, update the Job Order status
		if self.if_parts_required:
			check =0
			for i in self.get("items"):
				if i.parts_availability == "No" and not i.from_scrap:
					check=1
			doc = frappe.get_doc("Job Order Data",self.job_order_data)
			if check == 0:
				doc.status = "TR-Technician Repair"
			else:
				doc.status = "WP-Waiting Parts"
			doc.save(ignore_permissions=True)

	def update_job_order_status(self):
		# based on the stock availability Job Order Data status will be defined
		doc = frappe.get_doc("Job Order Data",self.job_order_data)

		self.update_working_status() # if the document status is changed as Working, Need to change the JO status as Working
		
		# 1. this case mostly works on initial submission
		if self.status == "Spare Parts":
			# if parts avaliability field is yes
			if self.parts_availability == "Yes":
				doc.status = "AP-Available Parts"
			else:
				doc.status = "SP-Searching Parts"
			doc.save(ignore_permissions=True)

	def update_working_status(self):
		doc = frappe.get_doc("Job Order Data",self.job_order_data)
		if self.status == "Working":
			if doc.status != "W-Working":
				doc.status = "W-Working"
			doc.save(ignore_permissions=True)
		if self.status == "Installed and Completed/Repaired":
			if doc.status != "RS-Repaired and Shipped":
				doc.status = "RS-Repaired and Shipped"
			doc.save(ignore_permissions=True)

@frappe.whitelist()
def get_valuation_rate(item, warehouse, qty):
	price = 0
	sts = "No"
	if frappe.db.exists("Bin",{'item_code':item,'warehouse':warehouse}):
		bin = frappe.db.get_value("Bin",{'item_code':item,'warehouse':warehouse},'actual_qty')
		if float(bin) >= float(qty):
			sts = "Yes"		
	price = frappe.db.get_value("Bin", {"item_code": item,'warehouse':warehouse}, "valuation_rate") or frappe.db.get_value("Item Price", {"item_code": item, "buying": 1}, "price_list_rate") or 0

	return {"price": price, "status": sts}

# Item creation
@frappe.whitelist()
def sku_creation(doc):
	sku_list = []
	data_dict = frappe._dict(json.loads(doc))

	for pm in data_dict.get("items", []):
		model = pm.get("model")
		part_no = pm.get("part")
		category = pm.get("category")
		sub_cat = pm.get("sub_category")
		package = pm.get("part_description")
		des = pm.get("part_name")
		if not part_no:
			# Check if an item already exists with same model, category, sub_category
			existing_item = frappe.get_all("Item", filters={
				"model": model,
				"category": category,
				"sub_category": sub_cat
			}, fields=["name"])

			if not existing_item:
				item_doc = frappe.new_doc("Item")
				item_doc.naming_series = 'P.######'
				item_doc.model = model

				# Fetch model number
				mod = frappe.db.get_value("Item Model", model, "model")
				item_doc.model_num = mod if mod else ""

				item_doc.category = category

				# Fetch sub-category name
				scn = frappe.db.get_value("Sub Category", sub_cat, "sub_category")
				item_doc.sub_category = sub_cat
				item_doc.sub_category_name = scn if scn else ""

				item_doc.package = package
				item_doc.description = des
				item_doc.item_name = des
				item_doc.item_group = "Components"

				try:
					item_doc.save(ignore_permissions=True)
					if not des:
						frappe.db.set_value("Item",item_doc.name,"description",item_doc.name,update_modified = False)
						frappe.db.set_value("Item",item_doc.name,"item_name",item_doc.name,update_modified = False)

					frappe.db.set_value("Part Sheet Item",pm.get("name"),'part',item_doc.name)
					sku_list.append(item_doc.name)
				except Exception as e:
					frappe.log_error(frappe.get_traceback(), "SKU Creation Error")
			else:
				frappe.msgprint(f"Item with model: {model}, category: {category}, sub-category: {sub_cat} already exists as <a href='/app/item/{existing_item[0].name}'>{existing_item[0].name}</a>.")
				frappe.db.set_value("Part Sheet Item",pm.get("name"),'part',existing_item[0].name)
	if sku_list:
		links = [f"<a href='/app/item/{sku}'>{sku}</a>" for sku in sku_list]
		frappe.msgprint("SKU Created: " + ', '.join(links))
	else:
		frappe.msgprint("No new SKUs were created based on the provided data.")


@frappe.whitelist()
def create_rfq(name):
	doc = frappe.get_doc("Evaluation Report",name)
	rfq = frappe.new_doc("Request for Quotation")
	rfq.company = doc.company
	rfq.branch = frappe.db.get_value("Job Order Data",doc.job_order_data,"branch")
	rfq.job_order_data = doc.job_order_data
	rfq.evaluation_report = doc.name
	rfq.department = frappe.db.get_value("Job Order Data",doc.job_order_data,"department")
	rfq.schedule_date = add_to_date(rfq.transaction_date,days = 2)
	rfq.items=[]
	warehouse = warehouse_based_on_branch_and_company(rfq.company,rfq.branch)
	for i in doc.get("items"):
		if i.parts_availability == "No" and i.from_scrap == 0:
			rfq.append("items",{
				"item_code":i.part,
				"item_name":i.part_name,
				"description":i.part_name,
				'model':i.model,
				"category":i.category,
				"sub_category":i.sub_category,
				"mfg":i.manufacturer,
				'serial_no':i.serial_no,
				"uom":"Nos",
				"stock_uom":"Nos",
				"conversion_factor":1,
				"stock_qty":1,
				"qty":i.qty,
				"schedule_date":add_to_date(rfq.transaction_date,days = 2),
				"warehouse":warehouse,
				"branch":rfq.branch,
				"parent_jo":doc.parent_jo,
				"job_order_data":doc.job_order_data,
				"department":frappe.db.get_value("Job Order Data",doc.job_order_data,"department")
			})

	return rfq

@frappe.whitelist()
def warehouse_based_on_branch_and_company(company,branch):
	warehouse = frappe.db.get_value("Warehouse List",{"branch":branch,"parent":company},["actual_warehouse"])
	return warehouse
	
@frappe.whitelist()
def release_parts(name):
	try:
		doc = frappe.get_doc('Evaluation Report', name)
		if doc.parts_released:
			frappe.throw("Parts have already been released for this Evaluation Report.")
		if not doc.items:
			frappe.throw("No items found in Evaluation Report to release.")

		warehouse = warehouse_based_on_branch_and_company(doc.company, doc.branch)

		new_doc = frappe.new_doc("Stock Entry")
		new_doc.stock_entry_type = "Material Issue"
		new_doc.company = doc.company
		new_doc.from_warehouse = warehouse

		for i in doc.items:
			if i.released != 1 and i.from_scrap == 0:
				new_doc.append("items", {
					's_warehouse': warehouse,
					'item_code': i.part,
					'qty': i.qty,
					'uom': frappe.db.get_value("Item", i.part, 'stock_uom'),
					'conversion_factor': 1,
					'rate': i.price_ea,
					'job_order_data': doc.job_order_data
				})
				i.released = 1
		new_doc.job_order_data = doc.job_order_data
		new_doc.save(ignore_permissions=True)
		new_doc.submit()

		# Mark parts as released in the Evaluation Report
		# doc.parts_released = 1
		doc.save(ignore_permissions=True)

		frappe.msgprint(f"Parts Released and Material Issue is Created - <b>{new_doc.name}</b>")
		return True

	except Exception as e:
		# Catch all other exceptions
		frappe.msgprint(f"An unexpected error occurred: {str(e)}")
		return False
