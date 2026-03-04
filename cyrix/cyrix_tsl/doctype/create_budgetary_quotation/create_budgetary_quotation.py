# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CreateBudgetaryQuotation(Document):
	@frappe.whitelist()
	def create_budget_quote(self):
		frappe.errprint("called")
		link = []
		if not self.customer:
			frappe.throw("Please mention Customer")
		if not self.branch:
			frappe.throw("Please mention branch")
		if not self.sales_person:
			frappe.throw("Please mention Sales person")
		if not self.items:
			frappe.throw("Please fill Budgetary Quotation Details Table")

		for i in self.get("items"):
			if not i.get("description"):
				frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Specify Description")
			if not i.get("uom"):
				frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Please Specify Unit of Measurement for the Item")
			
			if not i.get("qty") or i.get("qty")<=0:
				frappe.throw("<b>Row - "+str(i.get("idx"))+"</b>  Quantity should be greater than zero")

			md = frappe.get_value("Item Model",i.model,["model"])
			item = frappe.db.exists("Item",{"model":i.model,"mfg":i.mfg})
			if not item:
				s = frappe.new_doc("Item")
				s.model = i.model
				s.item_name = i.description
				s.description = i.description
				s.mfg = i.mfg
				s.uom = i.uom
				s.item_group = "Equipments"
				s.stock_uom = "Nos"
				s.save()
				
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
		if self.items:
			for i in self.items:
				it = frappe.db.exists("Item",{"model":i.model,"mfg":i.mfg})
				if it:
					s.append("items",{
						"sku":it,
						"model":i.model,
						"uom":i.uom,
						"description":i.description,
						"mfg":i.mfg,
						"qty":i.qty,
					})
		s.save()
		s.submit()
		link.append(s.name)
		if link:
			frappe.delete_doc("Create Budgetary Quotation", "Create Budgetary Quotation")
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
		
			
