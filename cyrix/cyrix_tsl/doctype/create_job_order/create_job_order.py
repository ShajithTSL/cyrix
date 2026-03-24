# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from datetime import datetime

class CreateJobOrder(Document):
	pass

naming_series = {
	"Dammam": {"normal":"JO-D.YY.-", "updated": "SB-JO-D.YY.-"},
	"Riyadh": {"normal":"JO-R.YY.-", "updated": "SB-JO-R.YY.-"},
	"Jeddah": {"normal":"JO-J.YY.-", "updated": "SB-JO-J.YY.-"},
	"Kuwait": {"normal":"JO-K.YY.-", "updated": "SB-JO-K.YY.-"},
	"Dubai": {"normal":"JO-DU.YY.-", "updated": "SB-JO-DU.YY.-"},
}
@frappe.whitelist()
def update_job_order_data(dict):
	doc = frappe._dict(json.loads(dict))
	# Proceed only if job_order_data reference exists
	if doc.job_order_data:
		for i in doc.get("received_equipment"):
			if not i.get("uom"):
				frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Specify Unit of Measurement for the Item")

			# Fetch delivery date and warranty duration from Job Order Data
			warr = frappe.db.get_value("Job Order Data", doc.job_order_data, ["delivery", "warranty"], as_dict=1)
			if warr['delivery'] and warr['warranty']:
				if warr['warranty'] == "NA":
					frappe.throw("Warranty Not Applicable")
				# Calculate warranty expiry date
				date = frappe.utils.add_to_date(warr['delivery'], months=int(warr['warranty']))

				# Update expiry date and returned date in Job Order Data
				frappe.db.set_value("Job Order Data",doc.job_order_data, "expiry_date", date)
				frappe.db.set_value("Job Order Data", doc.job_order_data, "returned_date", doc.received_date)

				# Check if Evaluation Report already exists for this Job Order
				eval = frappe.db.exists("Evaluation Report",{"job_order_data":doc.job_order_data})
				
				# If returned date is within warranty period, then proceed
				if (datetime.strptime(doc.received_date, '%Y-%m-%d').date()) <= date:
					if eval:
						frappe.db.set_value("Evaluation Report", eval, "ner_field", "NER-Need Evaluation Return")
					jo = frappe.get_doc("Job Order Data",doc.job_order_data)
					jo.status = "NER-Need Evaluation Return"
					if i.get("no_power"): jo.no_power = 1
					if i.get("no_output"): jo.no_output = 1
					if i.get("not_working"): jo.not_working = 1
					if i.get("no_display"): jo.no_display = 1
					if i.get("no_communication"): jo.no_communication = 1
					if i.get("supply_voltage"): jo.supply_voltage = 1
					if i.get("touchkeypad_not_working"): jo.touch_keypad_not_working = 1
					if i.get("no_backlight"): jo.no_backlight = 1
					if i.get("error_code"): jo.error_code = 1
					if i.get("short_circuit"): jo.short_circuit = 1
					if i.get("overloadovercurrent"): jo.overload_overcurrent = 1
					if i.get("other"):
						jo.others = 1
						jo.specify = i["specify"]
					jo.save(ignore_permissions = 1)
					
					
					create_stock_entry(i, doc, jo) # Create a related stock entry based on the returned equipment
					create_serial_no(i, doc)
					# Set Job Order Data CAP status and date
					frappe.db.set_value("Job Order Data", doc.job_order_data, "status_cap", "NER-Need Evaluation Return")
					status_cap_exists = frappe.db.get_value("Job Order Data", doc.job_order_data, "status_cap_date")
					if not status_cap_exists:
						frappe.db.set_value("Job Order Data", doc.job_order_data, "status_cap_date", datetime.now().date())

					jo_list = [""" <a href='/app/job-order-data/{0}'>{0}</a> """.format(doc.job_order_data)]
					frappe.msgprint("Job Order Updated: "+', '.join(jo_list))
				else:
					frappe.throw("Warranty Expired for the Job Order Data - "+str(doc.job_order_data))
			else:
				frappe.throw("No Warranty Period or Delivery Date is Mentioned In work order")
	# frappe.delete_doc("Create Job Order", "Create Job Order")


@frappe.whitelist()
def create_job_order_data(dict):
	doc = frappe._dict(json.loads(dict))
	if not doc.branch:
		frappe.throw("Please Specify Branch Name")
	if not doc.customer:
		frappe.throw("Please Mention the Customer Name")
	if not doc.incharge:
		frappe.throw("Please Mention the Customer Representative")

	# Ensure Address is linked to the Customer
	if doc.address:
		if not frappe.db.get_value("Dynamic Link", {"parent": doc.address, "link_doctype": "Customer"}, "link_name"):
			addr = frappe.get_doc("Address", doc.address)
			addr.append("links", {
				"link_doctype": "Customer",
				"link_name": doc.customer
			})
			addr.save(ignore_permissions=True)

	# Ensure Contact (Incharge) is linked to the Customer
	if doc.incharge:
		if not frappe.db.get_value("Dynamic Link", {"parent": doc.incharge, "link_doctype": "Customer", "parenttype": "Contact"}, "link_name"):
			addr = frappe.get_doc("Contact", doc.incharge)
			addr.append("links", {
				"link_doctype": "Customer",
				"link_name": doc.customer
			})
			addr.save(ignore_permissions=True)

	# Loop through each received equipment to create a Job Order Data record
	link = []
	for i in doc.get("received_equipment"):

		# validation for mandatory fields in received equipment
		if not i.get("model") and i.get("ignore") != 1:
			frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Specify Model Number for the Received Equipment")
		if not i.get("manufacturer") and i.get("ignore") != 1:
			frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Specify Manufacturer for the Received Equipment")
		if not i.get("uom"):
			frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Specify Unit of Measurement for the Item")
		if not i.get("attach_image"):
			frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Attach Image for the Item")

		if i.get("ignore") == 1 and not i.get("item_name"):
			frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Specify Description and Specification")

		jo = frappe.new_doc("Job Order Data")
		if doc.job_order_data:
			jo.naming_series = naming_series[doc.branch]["updated"]
		else:
			jo.naming_series = naming_series[doc.branch]["normal"]

		jo.department = frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1}) or ""
		jo.customer = doc.customer
		jo.sales_person = doc.sales_person
		jo.incharge = doc.incharge
		jo.priority_status = doc.sts
		jo.branch = doc.branch
		jo.repair_warehouse = doc.repair_warehouse
		jo.received_date = doc.received_date
		jo.unit_type = doc.unit_type
		jo.plant = doc.plant
		jo.company = doc.company
		jo.sec = doc.sec
		jo.address = doc.address
		jo.customer_rep = doc.incharge
		if doc.job_order_data:
			jo.parent_jo = doc.job_order_data
		if doc.warranty_date:
			jo.expiry_date = doc.warranty_date
		jo.status = "NE-Need Evaluation"
		
		if 'attach_image' in i and i['attach_image']:
			bg_less_image = i["attach_image"]
		else:
			bg_less_image = ""
		jo.attach_image = bg_less_image.replace(" ","%20") if 'attach_image' in i and i['attach_image'] else ""
		

		# check whether item_code exists or create new Item if needed
		check_for_item(i,bg_less_image)
		create_serial_no(i, doc)

		jo.append("material_list",{
			"item_code": i.get('item_code', ""),
			"item_name":i.get('item_name', ""),
			"model_no":i.get('model', ""),
			"mfg":i.get('manufacturer', ""),
			"quantity":i.get('qty', 0),
			"serial_no":i.get('serial_no', "")
		})
		if i.get("no_power"): jo.no_power = 1
		if i.get("no_output"): jo.no_output = 1
		if i.get("not_working"): jo.not_working = 1
		if i.get("no_display"): jo.no_display = 1
		if i.get("no_communication"): jo.no_communication = 1
		if i.get("supply_voltage"): jo.supply_voltage = 1
		if i.get("touchkeypad_not_working"): jo.touch_keypad_not_working = 1
		if i.get("no_backlight"): jo.no_backlight = 1
		if i.get("error_code"): jo.error_code = 1
		if i.get("short_circuit"): jo.short_circuit = 1
		if i.get("overloadovercurrent"): jo.overload_overcurrent = 1
		if i.get("other"):
			jo.others = 1
			jo.specify = i.get("specify", "")

		jo.save(ignore_permissions = True)

		# Update the File record if image was uploaded
		if jo.name and "attach_image" in i:
			frappe.db.sql('''update `tabFile` set attached_to_name = %s where file_url = %s ''',(jo.name,bg_less_image))
		jo.submit()
		
		# Create stock entry for the received item
		if not doc.job_order_data or doc.is_returned_unit:
			create_stock_entry(i, doc, jo)

		# append the Job Order names for message popup
		link.append(jo.name)

	if link:
		# frappe.delete_doc("Create Job Order", "Create Job Order")
		links_list = []
		for l in link:
			links_list.append(""" <a href='/app/job-order-data/{0}'>{0}</a> """.format(l))
		frappe.msgprint("Job Order created: "+', '.join(links_list))
		return True
	return False

def check_for_item(i,bg_less_image):
	# If item_code is not provided, try to fetch or create Item based on model and manufacturer
	if not 'item_code' in i and (i.get('model') or i.get('manufacturer')):
		item = frappe.db.get_value("Item", {"model": i.get('model'), "mfg": i.get('manufacturer')}, "name")
		if item:
			i['item_code'] = item
			i['item_name'] = frappe.db.get_value("Item", item, "item_name")
		else:
			if not 'item_name' in i:
				i['item_name'] = ""
			new_doc = frappe.new_doc('Item')
			new_doc.naming_series = '.######'
			new_doc.item_name = i.get('item_name')
			if 'item_group' in i:
				new_doc.item_group = i.get('item_group')
			else:
				new_doc.item_group = "Equipments"
			new_doc.description = i.get('item_name')
			new_doc.model = i.get('model')
			new_doc.stock_uom = i.get('uom')
			new_doc.image = bg_less_image.replace(" ","%20") if 'attach_image' in i and i.get('attach_image') else ""
			new_doc.is_stock_item = 1
			new_doc.mfg = i.get('manufacturer')
			new_doc.save(ignore_permissions=True)
			if new_doc.name:
				i['item_code'] = new_doc.name

	elif 'item_name' in i and not 'item_code' in i:
		new_doc = frappe.new_doc('Item')
		new_doc.naming_series = '.######'
		new_doc.item_name = i.get('item_name', "")
		if 'item_group' in i:
			new_doc.item_group = i.get('item_group')
		else:
			new_doc.item_group = "Equipments"
		new_doc.description = i.get('item_name', "")
		new_doc.model = i.get('model', "")
		new_doc.stock_uom = i.get('uom', "")
		new_doc.image = bg_less_image.replace(" ","%20") if 'attach_image' in i and i.get('attach_image') else ""
		new_doc.is_stock_item = 1
		new_doc.mfg = i.get('manufacturer', "")
		new_doc.save(ignore_permissions=True)
		if new_doc.name:
			i['item_code'] = new_doc.name

def create_serial_no(i, doc):
	
	# Create Serial Number record if the item has serial number and update its status to Active
	if i.get('has_serial_no') and i.get('serial_no'):
		s_number = frappe.db.exists("Serial Number",{"name":i.get('serial_no')})
		if s_number:
			sn_doc = frappe.get_doc("Serial Number",i.get('serial_no'))
			sn_doc.item_code = i['item_code']
			sn_doc.status = "Active"
			sn_doc.save()
			
		else:
			sn_doc = frappe.new_doc("Serial Number")
			sn_doc.serial_no = i.get('serial_no')
			sn_doc.item_code = i['item_code']
			sn_doc.company = doc.company
			sn_doc.status = "Active"
			sn_doc.save(ignore_permissions=True)

def create_stock_entry(i, doc, jo):

	# If item code exists, create stock entry for the received item
	if i['item_code']:
		se_doc = frappe.new_doc("Stock Entry")
		se_doc.stock_entry_type = "Material Receipt"
		se_doc.company = doc.company
		se_doc.branch = doc.branch
		se_doc.to_warehouse = doc.repair_warehouse
		se_doc.job_order_data = jo.name
		se_doc.append("items",{
			't_warehouse': doc.repair_warehouse,
			'item_code':i['item_code'],
			'item_name':i['item_name'],
			'description':i['item_name'],
			'serial_number':i.get('serial_no', ""),
			'qty':i['qty'],
			'uom':frappe.db.get_value("Item",i['item_code'],'stock_uom') or "Nos",
			'branch':doc.branch,
			'cost_center':frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_repair":1}) or "",
			'job_order_data':jo.name,
			'conversion_factor':1,
			'allow_zero_valuation_rate':1
		})
		se_doc.save(ignore_permissions = True)
		if se_doc.name:
			se_doc.submit()
			try:
				se_doc.submit()
			except Exception as e:
				frappe.log_error(frappe.get_traceback())
			pass

# Used to fetch the data when Job Order data is selected
@frappe.whitelist()
def get_jo_details(jo):
	l = []
	doc = frappe.get_doc("Job Order Data", jo)
	for i in doc.get("material_list"):
		incharge_name = frappe.db.get_value("Contact",doc.incharge,['first_name']) 
		incharge_email = frappe.db.get_value("Contact",doc.incharge,['email_id']) 
		incharge_phone_no = frappe.db.get_value("Contact",doc.incharge,['mobile_no']) 
		l.append(frappe._dict({
			"item_name": i.item_name,
			"item_code": i.item_code,
			"uom": frappe.db.get_value("Item", i.item_code, "stock_uom") or "Nos",
			"mfg": i.mfg,
			"model_no": i.model_no,
			"serial_no": i.serial_no,
			"qty": i.quantity,
			"sales_person": doc.sales_person,
			"customer": doc.customer,
			"incharge": doc.incharge,
			"incharge_name": incharge_name,
			"incharge_email": incharge_email,
			"incharge_phone_no": incharge_phone_no,
			"address": doc.address,
			"repair_warehouse": doc.repair_warehouse,
			"branch": doc.branch,
			"company": doc.company
		}))
	return l


# to fetch the customer representative and sales person
@frappe.whitelist()
def get_contacts(customer):
	doc = frappe.get_doc("Customer", customer)
	customer_rep = []
	sales_person = []
	for i in doc.get("contact_details"):
		customer_rep.append(i.name1)
	for i in doc.get("sales_team"):
		sales_person.append(i.sales_person)
	return [customer_rep, sales_person]


def updates():
	new_doc = frappe.new_doc('Item')
	new_doc.naming_series = '.######'
	new_doc.item_name = "Voltas - ITEM"
	new_doc.item_code = "Voltas - ITEM"
	new_doc.item_group = "Equipments"
	new_doc.description = "Voltas - ITEM"
	new_doc.model = "M000005"
	new_doc.is_stock_item = 1
	new_doc.mfg = "Voltas"
	new_doc.save(ignore_permissions=True)