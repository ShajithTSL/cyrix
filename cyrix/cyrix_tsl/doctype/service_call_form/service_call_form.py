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