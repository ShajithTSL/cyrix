# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class CreateSupplyOrder(Document):
	pass

naming_series = {
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

@frappe.whitelist()
def create_supply_order_data(dict):
	doc = frappe._dict(json.loads(dict))
	if not doc.branch:
		frappe.throw("Please Specify Branch Name")
	if not doc.customer:
		frappe.throw("Please Mention the Customer Name")
	if not doc.incharge:
		frappe.throw("Please Mention the Customer Representative")

	so = frappe.new_doc("Supply Order Data")
	so.naming_series = naming_series[doc.branch][doc.document_type]
	so.department = frappe.db.get_value("Cost Center",{"company":doc.company,"branch":doc.branch,"is_supply":1}) or ""
	so.customer = doc.customer
	so.document_type = doc.document_type
	so.sales_person = doc.sales_person
	so.incharge = doc.incharge
	so.priority_status = doc.sts
	so.branch = doc.branch
	so.warehouse = doc.repair_warehouse
	so.received_date = doc.received_date
	so.unit_type = doc.unit_type
	so.plant = doc.plant
	so.company = doc.company
	so.sec = doc.sec
	so.address = doc.address
	so.customer_rep = doc.incharge
	so.customer_reference_number = doc.customer_reference_number

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

	# Loop through each received equipment to create a Supply Order Data record
	link = []
	for i in doc.get("received_equipment"):
		# validation for mandatory fields in received equipment
		if not i.get("model") and i.get("ignore") != 1:
			frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Specify Model Number for the Received Equipment")
		if not i.get("manufacturer") and i.get("ignore") != 1:
			frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Specify Manufacturer for the Received Equipment")
		if not i.get("uom"):
			frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Specify Unit of Measurement for the Item")
		
		if i.get("ignore") == 1 and not i.get("item_name"):
			frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Specify Description and Specification")
		
		# check whether item_code exists or create new Item if needed
		check_for_item(i)

		so.append("material_list",{
			"item_code": i.get('item_code'),
			"item_name":i.get('item_name'),
			"model_no":i.get('model'),
			"mfg":i.get('manufacturer'),
			"quantity":i.get('qty'),
		})

	so.save(ignore_permissions = True)

	# Update the File record if image was uploaded
	if so.name and "attach_image" in i:
		frappe.db.sql('''update `tabFile` set attached_to_name = %s where file_url = %s ''',(so.name,i["attach_image"]))
	so.submit()
	
	# append the Supply Order names for message popup
	link.append(so.name)

	if link:
		# frappe.delete_doc("Create Supply Order", "Create Supply Order")
		links_list = []
		for l in link:
			links_list.append(""" <a href='/app/supply-order-data/{0}'>{0}</a> """.format(l))
		frappe.msgprint("Supply Order created: "+', '.join(links_list))
		return True
	return False

def check_for_item(i):
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
			new_doc.item_name = i.get('item_name', "")
			new_doc.stock_uom = i.get('uom', "")
			if 'item_group' in i:
				new_doc.item_group = i.get('item_group')
			else:
				new_doc.item_group = "Equipments"
			new_doc.description = i.get('item_name', "")
			new_doc.model = i.get('model', "")
			new_doc.image = (i.get('attach_image', "")).replace(" ","%20") if 'attach_image' in i and i.get('attach_image') else ""
			new_doc.is_stock_item = 1
			new_doc.mfg = i.get('manufacturer', "")
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
		new_doc.image = (i.get('attach_image', "")).replace(" ","%20") if 'attach_image' in i and i.get('attach_image') else ""
		new_doc.is_stock_item = 1
		new_doc.mfg = i.get('manufacturer', "")
		new_doc.save(ignore_permissions=True)
		if new_doc.name:
			i['item_code'] = new_doc.name
