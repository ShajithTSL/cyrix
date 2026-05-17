
import frappe
import json
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, getdate, nowdate

def update_job_order_status(self, method):
	for item in self.get("items"):
		if item.job_order_data:
			update = frappe.get_doc("Job Order Data", item.job_order_data)
			update.status = "WP-Waiting Parts"
			update.purchase_order_no = self.name
			update.save(ignore_permissions=True)

def update_supply_order_status(self, method):
	for item in self.get("items"):
		if item.supply_order_data:
			update = frappe.get_doc("Supply Order Data", item.supply_order_data)
			update.ordered_quantity += item.qty
			update.purchase_order_no = self.name
			update.save(ignore_permissions=True)

def update_supply_order_status_on_cancel(self, method):
	for item in self.get("items"):
		if item.supply_order_data:
			update = frappe.get_doc("Supply Order Data", item.supply_order_data)
			update.ordered_quantity -= item.qty
			update.purchase_order_no = ""
			update.save(ignore_permissions=True)

def update_budgetary_quotation_status(self, method):
	if self.budgetary_quotation:
		update = frappe.get_doc("Budgetary Quotation", self.budgetary_quotation)
		update.status = "Ordered"
		update.purchase_order_no = self.name
		update.save(ignore_permissions=True)

@frappe.whitelist()
def make_po_from_job_order(job_orders, target_doc=None):
	job_orders = json.loads(job_orders)

	if not job_orders:
		frappe.throw("No Job Orders selected.")

	# Get all Supplier Quotations linked to these Job Orders
	sq_list = frappe.get_all("Supplier Quotation", 
		filters={
			"job_order_data": ["in", job_orders],
			"docstatus": 1
		}, 
		fields=["name"]
	)
	
	if not sq_list:
		frappe.throw("No submitted Supplier Quotations found for selected Job Orders.")

	# Use first SQ to create base PO
	base_po = None
	for i, sq in enumerate(sq_list):
		if i == 0:
			base_po = make_purchase_order(sq.name, target_doc)
		else:
			# For other SQs, map and add items to base_po
			new_po = make_purchase_order(sq.name, None)
			for item in new_po.items:
				base_po.append("items", item)

	return base_po

@frappe.whitelist()
def get_job_order_data(job_order_data):
	job_order_data = json.loads(job_order_data)
	l = []
	for i in list(job_order_data):
		er =  frappe.db.sql('''select name from `tabEvaluation Report` where docstatus = 1 and job_order_data = %s and parts_availability = "No" ''',i,as_dict=1)
		for j in er:
			doc = frappe.get_doc("Evaluation Report",j['name'])
			for k in doc.items:
				if k.parts_availability == "No":
					d = frappe._dict((k.as_dict()))
					d["job_order_data"] = i
					# d["part_sheet"] = j["name"]
					l.append(d)
	return l

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.run_method("set_missing_values")
		target.run_method("get_schedule_dates")
		target.run_method("calculate_taxes_and_totals")

	def update_item(obj, target, source_parent):
		target.stock_qty = flt(obj.qty) * flt(obj.conversion_factor)

	doclist = get_mapped_doc(
		"Supplier Quotation",
		source_name,
		{
			"Supplier Quotation": {
				"doctype": "Purchase Order",
				"field_no_map": ["transaction_date"],
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Supplier Quotation Item": {
				"doctype": "Purchase Order Item",
				"field_map": [
					["name", "supplier_quotation_item"],
					["parent", "supplier_quotation"],
					["material_request", "material_request"],
					["material_request_item", "material_request_item"],
					["sales_order", "sales_order"],
				],
				"postprocess": update_item,
			},
			"Purchase Taxes and Charges": {
				"doctype": "Purchase Taxes and Charges",
			},
		},
		target_doc,
		set_missing_values,
	)

	return doclist