# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document

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
	new_doc.sales_rep = doc.salesman_name
	new_doc.service_call_form = doc.name
	new_doc.branch = doc.branch
	new_doc.append("items",{
		"item_code":"000010",
		"item_name":"Service Item",
		"description":"",
		"qty":1,
		"uom":"Nos",
		"stock_uom":"Nos",
		"conversion_factor":1,
		"stock_qty":1,
	})
	return new_doc