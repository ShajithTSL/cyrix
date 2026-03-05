# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CreateBudgetaryQuotation(Document):
	@frappe.whitelist()
	def create_budget_quote(self):
		link = []
		if not self.customer:
			frappe.throw("Please mention Customer")
		if not self.branch:
			frappe.throw("Please mention Branch")
		if not self.sales_person:
			frappe.throw("Please mention Sales person")
		if not self.department:
			frappe.throw("Please mention Department")
		if not self.items:
			frappe.throw("Please fill Budgetary Quotation Details Table")

		s = frappe.new_doc("Budgetary Quotation")
		s.customer = self.customer
		s.company = self.company
		s.status = "Inquiry"
		s.customer_representative = self.customer_representative
		s.customer_ref = self.customer_ref
		s.mobile = self.mobile
		s.branch = self.branch
		s.department = self.department
		s.sales_person = self.sales_person

		for i in self.get("items"):
			if not i.get("description"):
				frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Specify Description")
			if not i.get("uom"):
				frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Specify Unit of Measurement for the Item")
			
			if not i.get("qty") or i.get("qty")<=0:
				frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Quantity should be greater than zero")

			check_for_item(i)
			frappe.errprint(i)
			
			s.append("items",{
				"sku":i.sku,
				"model":i.model,
				"item_group":i.item_group,
				"uom":i.uom,
				"description":i.description,
				"mfg":i.mfg,
				"qty":i.qty,
			})
		s.save()
		s.submit()
		link.append(s.name)
		if link:
			frappe.msgprint("Budgetary Quotation is created: <a href='/app/budgetary-quotation/{0}'>{0}</a>".format(s.name,s.name))
			return True
		return False
			
	@frappe.whitelist()
	def get_contact(self):
		doc = frappe.get_doc("Customer", self.customer)
		l = []
		for i in doc.get("contact_details"):
			l.append(frappe.db.get_value("Contact",i.name1,'first_name')or i.name1)
		return l
		
def check_for_item(i):
	# If sku is not provided, try to fetch or create Item based on model and mfg
	if not i.get('sku') and (i.get('model') or i.get('mfg')):
		item = frappe.db.get_value("Item", {"model": i.get('model'), "mfg": i.get('mfg')}, "name")
		if item:
			i.sku = item
			i.description = frappe.db.get_value("Item", item, "item_name")
		else:
			if not i.get("description"):
				i.description = ""
			new_doc = frappe.new_doc('Item')
			new_doc.naming_series = '.######'
			new_doc.item_name = i.get('description')
			if i.get('item_group'):
				new_doc.item_group = i.get('item_group')
			else:
				new_doc.item_group = "Equipments"
			new_doc.description = i.get('description')
			new_doc.model = i.get('model')
			new_doc.stock_uom = i.get('uom')
			new_doc.is_stock_item = 1
			new_doc.mfg = i.get('mfg')
			new_doc.save(ignore_permissions=True)
			if new_doc.name:
				i.sku = new_doc.name
	
	elif i.get("description") and not i.get('sku'):
		new_doc = frappe.new_doc('Item')
		new_doc.naming_series = '.######'
		new_doc.item_name = i.get('description')
		if i.get('item_group'):
			new_doc.item_group = i.get('item_group')
		else:
			new_doc.item_group = "Equipments"
		new_doc.description = i.get('description')
		new_doc.model = i.get('model')
		new_doc.stock_uom = i.get('uom')
		new_doc.is_stock_item = 1
		new_doc.mfg = i.get('mfg')
		new_doc.save(ignore_permissions=True)
		if new_doc.name:
			i.sku = new_doc.name		
