# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

from codecs import ignore_errors
from hashlib import new
from pydoc import doc
from types import new_class
import frappe
import json
from frappe.model.document import Document
from frappe.utils import getdate,today
from datetime import datetime,date
from frappe.utils.data import (
	add_days,
	add_months,
	add_to_date,
	date_diff,
	flt,
	get_date_str,
	nowdate,
)

class ReplacementUnit(Document):
	pass


@frappe.whitelist()
def create_rfq(docname):
	doc = frappe.get_doc("Replacement Unit",docname)
	new_doc = frappe.new_doc("Request for Quotation")
	new_doc.company = doc.company
	new_doc.branch = doc.branch
	new_doc.schedule_date = today()
	new_doc.custom_replacement_unit = docname
	# new_doc.job_order_data = docname
	new_doc.department = doc.department
	new_doc.items=[]
	warehouse = ""
	if new_doc.company == "Cyrix TSL - Kuwait":
		warehouse = "Kuwait - CT-K"
	if new_doc.company == "Cyrix TSL - UAE":
		warehouse = "Dubai - CT-UAE"
	if new_doc.company == "Company Al-Halloul Faniye Medical":
		warehouse = "Riyadh - BM"
		
	for i in doc.get("material_list"):
		new_doc.append("items",{
			"item_code":i.item_code,
			'model':i.model_no,
			"uom":"Nos",
			"stock_uom":"Nos",
			"conversion_factor":1,
			"stock_qty":1,
			"qty":1,
			# "job_order_data":docname,
			"custom_replacement_unit":docname,
			# "schedule_date":add_to_date(new_doc.transaction_date,days = 2),
			"schedule_date":today(),
			"warehouse":warehouse,
			"branch":new_doc.branch,
			"department":doc.department,
			"cost_center":doc.department      
		})
	return new_doc
