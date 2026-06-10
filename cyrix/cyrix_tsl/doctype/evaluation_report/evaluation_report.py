# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from frappe.utils import add_to_date
from cyrix.custom_py.boot import get_bootinfo as info
from cyrix.custom_py.utils import sendmail

NO_REPLY_EMAIL = "no-reply@cyrix-tsl.com"
base_url = frappe.utils.get_url()
warehouse_list = {
	"Kuwait": "Kuwait - CT-K",
	"Riyadh":"Riyadh - BM",
	"Jeddah":"Jeddah - BM"
}



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
		check_for_shared_docs_on_evaluation(self)	
	
	def on_update(self):		
		check_for_shared_docs_on_evaluation(self)
		
	def validate_evaluation_time(self):
		if (not self.evaluation_time or not self.estimated_repair_time) and self.status not in ["Return Not Repaired"]:
			frappe.throw("Note: Evaluation Time and Estimated Repair Time is not given.")
		self.check_stock_availability() # to update the stock availability

	def before_submit(self):
		self.validate_evaluation_time()
		
	def on_submit(self):
		self.update_job_order_status() # to update the Job Order Data status
		self.send_mail_on_status_update(action = "on_submit")

	def on_update_after_submit(self):
		self.check_stock_availability() # to update the stock availability
		self.update_job_order_status() # to update the Job Order Data status
		self.update_part_no()
		check_for_shared_docs_on_evaluation(self)
		self.send_mail_on_status_update(action = "on_update_after_submit")

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
		self.update_board_evaluation_status() # if the document status is changed as Board Evaluation, Need to change the JO status as Board Evaluation
		# 1. this case mostly works on initial submission
		if doc.status in ["NE-Need Evaluation","NER-Need Evaluation Return","UE-Under Evaluation"]:
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
			if doc.status != "W-Working" and not self.check_quotation_exists(self.job_order_data):
				doc.status = "W-Working"
			doc.save(ignore_permissions=True)

		if self.status == "Installed and Completed/Repaired":
			if doc.status != "RS-Repaired and Shipped":
				doc.status = "RS-Repaired and Shipped"
			doc.save(ignore_permissions=True)

		if self.status == "Return Not Repaired":
			if doc.status != "RNR-Return Not Repaired":
				doc.status = "RNR-Return Not Repaired"
			doc.save(ignore_permissions=True)	

		if self.status == "RNP-Return No Parts":
			if doc.status != "RNP-Return No Parts":
				doc.status = "RNP-Return No Parts"
			doc.save(ignore_permissions=True)		

	def update_board_evaluation_status(self):
		doc = frappe.get_doc("Job Order Data",self.job_order_data)
		if self.status == "Board Evaluation":
			if doc.status != "Board Evaluation":
				doc.status = "Board Evaluation"
			doc.save(ignore_permissions=True)

	def check_quotation_exists(self,jo):
		# check whether the Customer Quotation is exists for the given Job Order Data, workflow_state should beApproved by Customer and the job_order_data is set in Quotation Item table.
		quotation_exists = False
		quotations = frappe.get_all("Quotation Item", filters={"job_order_data": jo, "docstatus": 1}, pluck="parent")
		if quotations:
			for q in quotations:
				quotation_doc = frappe.get_doc("Quotation", q)
				if quotation_doc.workflow_state == "Approved by Customer":
					quotation_exists = True
					break
		return quotation_exists

	def send_mail_on_status_update(self, action):
		if self.status not in ["Internal Extra Parts", "Spare Parts", "Extra Parts"]:
			return

		# to check for the previous status
		before = self.get_doc_before_save()

		if not before:
			return

		if before.status == self.status and action != "on_submit":
			return

		message = f""" Dear Purchase Team,<br><br>
						Evaluation Report - <b>{self.name}</b> has been created<br>
						Job Order Data - <b>{self.get("job_order_data")}</b><br>
						Status - <b>{self.get("status")}</b><br><br>
						Please take action to release the parts.<br><br>
						<a href="{base_url}/app/evaluation-report/{self.name}" target="_blank">Click Here</a>
					"""

		sendmail(self, 
			message, 
			subject = f"Evaluation Report - {self.name}", 
			sender = NO_REPLY_EMAIL, 
			recipients = info().get("purchase_to").get(self.company), 
			attachments = None, 
			cc = None 
		)

def check_for_shared_docs_on_evaluation(self):
	jo_doc = frappe.get_doc("Job Order Data",self.job_order_data)
	tech_user = frappe.db.get_value("Technician ID",jo_doc.technician,"user_email")
	technicians = [tech_user]
	if jo_doc.parent_jo:
		parent_doc = frappe.get_doc("Job Order Data",jo_doc.parent_jo)
		parent_tech_user = frappe.db.get_value("Technician ID",parent_doc.technician,"user_email")
		technicians.append(parent_tech_user)
		for pa_jo in parent_doc.multiple_technicians:
			if pa_jo.get("email") not in technicians:
				technicians.append(pa_jo.get("email"))
	# self.multiple_technicians is a table_multiselect
	for row in jo_doc.multiple_technicians:
		if row.get("email") not in technicians:
			technicians.append(row.get("email"))

	for t_id in technicians:
		if t_id:
			doc = frappe.db.exists("DocShare",{
				"user":t_id,
				"share_doctype": self.doctype,
				"share_name": self.name
			})
			if not doc:
				doc = frappe.new_doc("DocShare")
				doc.user = t_id
				doc.share_doctype = self.doctype
				doc.share_name = self.name
				doc.read = 1
				doc.write = 1
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
	rfq.cost_center = frappe.db.get_value("Job Order Data",doc.job_order_data,"department") or frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1})
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
				"cost_center":frappe.db.get_value("Job Order Data",doc.job_order_data,"department") or frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1})
			})

	return rfq

@frappe.whitelist()
def warehouse_based_on_branch_and_company(company,branch):
	warehouse = frappe.db.get_value("Warehouse List",{"branch":branch,"parent":company},["actual_warehouse"])
	return warehouse
	
@frappe.whitelist()
def create_item(model,part_no,category,sub_category,package,description):
	part = frappe.db.exists("Item",{'model':model,'category':category,'sub_category':sub_category})
	if part:
		return part
	else:
		if not part_no:
			# if frappe.session.user == "purchase@tsl-me.com" or frappe.session.user == "purchase-sa1@tsl-me.com":
			item_doc = frappe.new_doc("Item")
			item_doc.naming_series = "P.######"
			item_doc.model = model
			item_doc.category = category
			item_doc.sub_category = sub_category
			item_doc.package = package
			item_doc.item_name = description
			item_doc.item_group = "Components"
			item_doc.save(ignore_permissions = True)
			if not description:
				frappe.db.set_value("Item",item_doc.name,"item_name",item_doc.name,update_modified = False)
			return item_doc.name
		else:
			frappe.msgprint("SKU already there in this row")

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


from frappe.utils import flt


@frappe.whitelist()
def get_release_items(docname):

	doc = frappe.get_doc("Evaluation Report", docname)

	output = []

	for row in doc.items:
		if row.from_scrap == 1:
			continue

		# REQUIRED QTY
		required_qty = flt(row.qty)

		# ALREADY RELEASED (from Stock Entry)
		released_qty = frappe.db.sql("""
			SELECT IFNULL(SUM(sed.qty),0)
			FROM `tabStock Entry Detail` sed
			JOIN `tabStock Entry` se ON se.name = sed.parent
			WHERE se.docstatus < 2
			AND sed.item_code=%s
			AND sed.job_order_data=%s
			AND se.awaiting_parts = 1
			AND sed.evaluation_row = %s
		""", (row.part, doc.job_order_data, row.name))[0][0] or 0

		# STOCK IN WAREHOUSE
		stock_qty = frappe.db.get_value(
			"Bin",
			{"item_code": row.part, "warehouse": warehouse_list.get(doc.branch)},
			["actual_qty", "awaiting_qty"],
			as_dict=True
		)
		reserved_qty = 0
		
		available_qty = 0
		if stock_qty:
			available_qty = (stock_qty.actual_qty or 0) - (stock_qty.awaiting_qty or 0) - reserved_qty


		output.append({
			"row_name": row.name,
			"item_code": row.part,
			"required_qty": required_qty,
			"released_qty": released_qty,
			"stock_qty": available_qty
		})

	# frappe.errprint(output)

	return output


@frappe.whitelist()
def create_stock_entry(evaluation, items):

	doc = frappe.get_doc("Evaluation Report", evaluation)
	items = frappe.parse_json(items)

	# Branch Mapping

	branch_map = {
		"Kuwait": ("Kuwait - CT-K", "Kuwait - Repair - CT-K"),
		"Riyadh": ("Riyadh - BM", "Riyadh - Repair - BM"),
		"Jeddah": ("Jeddah - BM", "Jeddah - Repair - BM")
	}

	war, cc = branch_map.get(doc.branch, ("", ""))

	if not war:
		frappe.throw("Warehouse not configured for this branch")

	new_doc = frappe.new_doc("Stock Entry")
	new_doc.company = doc.company
	new_doc.stock_entry_type = "Material Issue"
	new_doc.from_warehouse = war

	for item in items:
		if item.get("qty", 0) <= 0:
			continue

		new_doc.append("items", {
			"s_warehouse": war,
			"item_code": item["item_code"],
			"qty": item["qty"],
			"serial_no": item.get("serial_no", ""),
			"uom": item.get("uom"),
			"stock_uom": item.get("uom"),
			"cost_center": cc,
			"job_order_data": doc.job_order_data,
			"conversion_factor": 1,
			"evaluation_row":item.get("row_name")
			# "allow_zero_valuation_rate": 1
		})


	new_doc.awaiting_parts = 1
	new_doc.save(ignore_permissions=True)
	new_doc.submit()

	frappe.msgprint("Parts Released and Material Issue is Created")
	return new_doc.name


def migrate_old_releases():
	# find old entries without row reference
	old_rows = frappe.db.sql("""
		SELECT 
			sed.parent,
			sed.name, 
			sed.item_code,
			sed.qty, 
			sed.job_order_data
		FROM `tabStock Entry Detail` sed
		JOIN `tabStock Entry` se ON se.name = sed.parent
		WHERE se.docstatus = 1
			# AND se.awaiting_parts = 1
			AND se.stock_entry_type = 'Material Issue'
			AND IFNULL(sed.job_order_data,'') != ''
			AND IFNULL(sed.evaluation_row,'') = ''
			ORDER BY se.posting_date, se.creation
	""", as_dict=True)

	for sed in old_rows:
		print(sed)

		remaining_qty = flt(sed.qty)
		eval_list = frappe.db.get_all("Evaluation Report",{'job_order_data':sed.job_order_data},'name')
		for eval in eval_list:
			# get evaluation rows FIFO
			eval_rows = frappe.db.sql("""
				SELECT parent,name, part, qty
				FROM `tabPart Sheet Item`
				WHERE parent=%s
				AND parenttype = 'Evaluation Report'
				AND part=%s
				ORDER BY idx
			""", (eval.name, sed.item_code), as_dict=True)
			if eval_rows:
				print(eval_rows)

			for row in eval_rows:

				if remaining_qty <= 0:
					break

				# already allocated qty for this row
				allocated = frappe.db.sql("""
					SELECT IFNULL(SUM(qty),0)
					FROM `tabStock Entry Detail`
					WHERE evaluation_row=%s
				""", row.name)[0][0] or 0

				balance = flt(row.qty) - flt(allocated)

				if balance <= 0:
					continue

				allocate = min(balance, remaining_qty)
				print(allocate)

				# update stock entry row
				frappe.db.set_value(
					"Stock Entry Detail",
					sed.name,
					"evaluation_row",
					row.name
				)

				remaining_qty -= allocate
			frappe.db.commit()
		print("Migration completed")


@frappe.whitelist()
def create_technical_report(name):
	doc = frappe.get_doc("Job Order Data", name)
	new_doc = frappe.new_doc("Technical Report")
	new_doc.company = doc.company
	new_doc.customer = doc.customer
	new_doc.customer_address = frappe.db.get_value("Customer", doc.customer, "customer_primary_address")
	new_doc.address_display = frappe.db.get_value("Customer",doc.customer,"primary_address")
	new_doc.sales_person = doc.sales_person
	new_doc.document_type = doc.doctype
	new_doc.document_reference = doc.name
	new_doc.branch = doc.branch
	for item in doc.material_list:
		new_doc.manufacturer = item.mfg
		new_doc.model = item.model_no
		new_doc.serial_number = item.serial_no
		new_doc.description = item.item_name
	new_doc.append("technician",{
		"technician": doc.technician,
	})

	return new_doc