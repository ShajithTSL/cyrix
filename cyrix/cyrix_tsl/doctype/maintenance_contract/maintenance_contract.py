# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from cyrix.custom_py import utils


class MaintenanceContract(Document):
	def before_submit(self):
		for i in self.get('items'):
			self.check_for_item(i)
			self.create_serial_no(i)

	def create_serial_no(self, i):
		# Create Serial Number record if the item has serial number and update its status to Active
		if i.get('serial_number'):
			s_number = frappe.db.exists("Serial Number",{"name":i.get('serial_number')})
			if s_number:
				sn_doc = frappe.get_doc("Serial Number",i.get('serial_number'))
				sn_doc.item_code = i.get('item_code')
				sn_doc.status = "Active"
				sn_doc.save()
				
			else:
				sn_doc = frappe.new_doc("Serial Number")
				sn_doc.serial_no = i.get('serial_number')
				sn_doc.item_code = i.get('item_code')
				sn_doc.company = self.company
				sn_doc.status = "Active"
				sn_doc.save(ignore_permissions=True)

	def check_for_item(self, i):
		# If item_code is not provided, try to fetch or create Item based on model and manufacturer
		if not i.get("item_code") and (i.get("model") or i.get("manufacturer")):
			item = frappe.db.get_value("Item", {
				"model": i.get("model"),
				"mfg": i.get("manufacturer")
			}, "name")

			if item:
				i.item_code = item
				i.item_name = frappe.db.get_value("Item", item, "item_name")
			else:
				if not i.get("item_name"):
					i.item_name = ""

				new_doc = frappe.new_doc('Item')
				new_doc.naming_series = '.######'
				new_doc.item_name = i.get('item_name')
				new_doc.item_group = i.get('item_group') or "Equipments"
				new_doc.description = i.get('item_name')
				new_doc.model = i.get('model')
				new_doc.stock_uom = i.get('uom')
				new_doc.is_stock_item = 1
				new_doc.mfg = i.get('manufacturer')
				new_doc.save(ignore_permissions=True)

				if new_doc.name:
					i.item_code = new_doc.name

		elif i.get("item_name") and not i.get("item_code"):
			new_doc = frappe.new_doc('Item')
			new_doc.naming_series = '.######'
			new_doc.item_name = i.get('item_name', "")
			new_doc.item_group = i.get('item_group') or "Equipments"
			new_doc.description = i.get('item_name', "")
			new_doc.model = i.get('model', "")
			new_doc.stock_uom = i.get('uom', "")
			new_doc.is_stock_item = 1
			new_doc.mfg = i.get('manufacturer', "")
			new_doc.save(ignore_permissions=True)

			if new_doc.name:
				i.item_code = new_doc.name

# Interval is mentioned in days. Need to calculate the no of schedules based on the start and end date and interval and return the list of schedule dates
@frappe.whitelist()
def create_schedule(from_date, to_date, interval):
	schedule_dates = []
	current_date = from_date

	while current_date <= to_date:
		schedule_dates.append(current_date)
		current_date = frappe.utils.add_days(current_date, int(interval))

	return schedule_dates


# @frappe.whitelist()
# def create_service_call_form(source):
# 	doc = frappe.get_doc("Maintenance Contract", source)
# 	new_doc = frappe.new_doc("Service Call Form")
# 	new_doc.document_type = "Maintenance Contract"
# 	new_doc.related_doc = doc.name
# 	new_doc.customer = doc.customer
# 	new_doc.company = doc.company
# 	new_doc.sales_person = doc.sales_person
# 	new_doc.branch = doc.branch

# 	return new_doc

from frappe.model.mapper import get_mapped_doc
@frappe.whitelist()
def create_service_call_form(source, target_doc=None):
	doc = get_mapped_doc(
		"Maintenance Contract",
		source,
		{
			"Maintenance Contract": {
				"doctype": "Service Call Form",
				"field_map": {
					"doctype": "document_type",
					"name": "related_doc",
					"description": "reason"
				},
			},
			"Maintenance Contract Item": {
				"doctype": "Service Call Item"
			},
		},
		target_doc,
	)

	return doc

# route to Create Job Order single doctype page with reference to Maintenance Contract and pre-fill the item details in Job Order Item child table based on the items added in Maintenance Contract
@frappe.whitelist()
def create_job_order(source, row_name):
	doc = frappe.get_doc("Maintenance Contract", source)
	# if doc.items:
	job_order = frappe.new_doc("Create Job Order")
	job_order.maintenance_contract = doc.name
	job_order.customer = doc.customer
	job_order.incharge = doc.incharge
	job_order.incharge_name = doc.incharge_name
	job_order.incharge_email = doc.incharge_email
	job_order.incharge_phone_no = doc.incharge_phone_no
	job_order.company = doc.company
	job_order.sales_person = doc.sales_person
	job_order.branch = doc.branch
	for item in doc.items:
		if row_name and item.name != row_name:
			continue
		serial_no = item.serial_number if item.serial_number else ""
		has_serial_no = 1 if item.serial_number else 0
		job_order.append("received_equipment", {
			"item_code": item.item_code,
			"item_name": item.item_name,
			"item_group": item.item_group,
			"model": item.model,
			"manufacturer": item.manufacturer,
			"serial_no": serial_no,
			"has_serial_no": has_serial_no,
			"uom": frappe.db.get_value("Item", item.item_code, "stock_uom") if item.item_code else item.uom,
			"qty": item.qty
		})
	return job_order


@frappe.whitelist()
def create_qtn(source):
	doc = frappe.get_doc("Maintenance Contract",source)
	new_doc = frappe.new_doc("Quotation")	
	new_doc.company = doc.company
	new_doc.party_name = doc.customer
	new_doc.customer_address = frappe.db.get_value("Customer",doc.customer,"customer_primary_address")
	new_doc.address_display = frappe.db.get_value("Customer",doc.customer,"primary_address")
	new_doc.quotation_type = "Internal Quotation - MC"
	new_doc.sales_person = doc.sales_person
	new_doc.maintenance_contract = doc.name
	new_doc.currency = frappe.db.get_value("Company",doc.company,"default_currency")
	new_doc.selling_price_list = utils.fetch_price_list(doc.company, "selling")
	new_doc.branch = doc.branch
	for item in doc.items:
		new_doc.append("items",{
			"item_code":item.item_code,
			"item_name":item.item_name,
			"model":frappe.db.get_value("Item", item.item_code, "model"),
			"mfg":frappe.db.get_value("Item", item.item_code, "mfg"),
			"description":item.description,
			"serial_number":item.serial_number,
			"qty":item.qty,
			"uom":frappe.db.get_value("Item", item.item_code, "stock_uom") if item.item_code else item.uom,
			"stock_uom":frappe.db.get_value("Item", item.item_code, "stock_uom") if item.item_code else item.uom,
			"conversion_factor":1,
		})

	return new_doc