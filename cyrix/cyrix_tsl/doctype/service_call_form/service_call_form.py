# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document
from cyrix.custom_py import utils

class ServiceCallForm(Document):
	pass

@frappe.whitelist()
def create_qtn(source):
	doc = frappe.get_doc("Service Call Form",source)
	new_doc = frappe.new_doc("Quotation")	
	new_doc.company = doc.company
	new_doc.party_name = doc.customer
	new_doc.customer_address = frappe.db.get_value("Customer",doc.customer,"customer_primary_address")
	new_doc.address_display = frappe.db.get_value("Customer",doc.customer,"primary_address")
	new_doc.quotation_type = "Internal Quotation - Site Visit"
	new_doc.sales_person = doc.sales_person
	new_doc.service_call_form = doc.name
	new_doc.currency = frappe.db.get_value("Company",doc.company,"default_currency")
	new_doc.selling_price_list = utils.fetch_price_list(doc.company, "selling")
	new_doc.branch = doc.branch
	if len(doc.items) > 0:
		for item in doc.items:
			new_doc.append("items",{
				"item_code":item.item_code,
				"item_name":item.item_name,
				"description":item.description,
				"qty":item.qty,
				"uom":frappe.db.get_value("Item", item.item_code, "stock_uom") if item.item_code else item.uom,
				"stock_uom":frappe.db.get_value("Item", item.item_code, "stock_uom") if item.item_code else item.uom,
				"conversion_factor":1,
				"stock_qty":1,
			})

	else:
		new_doc.append("items",{
			"item_code":frappe.db.get_value("Item",{"item_name":"Service Call"},'name'),
			"item_name":"Service Call",
			"description":"",
			"qty":1,
			"uom":"Nos",
			"stock_uom":"Nos",
			"conversion_factor":1,
			"stock_qty":1,
		})
	return new_doc

@frappe.whitelist()
def create_service_report(source, row_id):
	doc = frappe.get_doc("Service Call Form",source)
	new_doc = frappe.new_doc("Technical Report")	
	new_doc.company = doc.company
	new_doc.customer = doc.customer
	new_doc.customer_address = frappe.db.get_value("Customer",doc.customer,"customer_primary_address")
	new_doc.address_display = frappe.db.get_value("Customer",doc.customer,"primary_address")
	new_doc.sales_person = doc.sales_person
	new_doc.service_call_form = doc.name
	new_doc.branch = doc.branch
	for item in doc.items:
		if item.name == row_id:
			new_doc.sku = item.item_code
			new_doc.manufacturer = item.manufacturer
			new_doc.model = item.model
			new_doc.serial_number = item.serial_number
			new_doc.description = item.description
			new_doc.technician = doc.technician_name

	return new_doc