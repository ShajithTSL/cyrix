# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

branch_map = {
	"Kuwait": ("Kuwait - CT-K", "Kuwait - Repair - CT-K"),
	"Riyadh": ("Riyadh - BM", "Riyadh - Repair - BM"),
	"Jeddah": ("Jeddah - BM", "Jeddah - Repair - BM")
}
class ReturnedParts(Document):
	# def validate(self):
	# 	self.update_qty_on_submit()
	def update_qty_on_submit(self):
		if self.returned_parts:
			for rp in self.returned_parts:
				# take the qty and return qty from the table before submission
				qty, returned_qty = frappe.db.get_value("Part Sheet Item",{"parent":self.get("evaluation_report"),"name":rp.reference},['qty','returned_qty'])
				
				# calculate the return qty
				returned_qty += rp.qty
				
				# update the calculated returned qty
				frappe.db.set_value("Part Sheet Item",rp.reference,'returned_qty',returned_qty)

				# if the qty and returned_qty from the Part Sheet Item table is equal
				if qty == returned_qty:
					frappe.db.set_value("Part Sheet Item",rp.reference,'returned',1)
				else:
					frappe.db.set_value("Part Sheet Item",rp.reference,'returned',0)

					# to limit the returned_qty beyond the actual qty
					if returned_qty > qty:
						frappe.throw("Row #"+str(rp.idx)+" - Quantity cannot be more than <b>"+str(qty)+"</b>")

	def reverse_qty_on_cancel(self):
		if self.returned_parts:
			for rp in self.returned_parts:
				qty, returned_qty = frappe.db.get_value("Part Sheet Item",{"parent":self.get("evaluation_report"),"name":rp.reference},['qty','returned_qty'])
				returned_qty -= rp.qty
				frappe.db.set_value("Part Sheet Item",rp.reference,'returned_qty',returned_qty)
				if qty == returned_qty:
					frappe.db.set_value("Part Sheet Item",rp.reference,'returned',1)
				else:
					frappe.db.set_value("Part Sheet Item",rp.reference,'returned',0)
					if returned_qty > qty:
						frappe.throw("Not Allowed")


	def on_cancel(self):
		self.reverse_qty_on_cancel()
		stock_entry = frappe.db.exists("Stock Entry",{'returned_parts':self.name},'name')
		if stock_entry:
			se = frappe.get_doc("Stock Entry",stock_entry)
			se.cancel()
		
	def on_submit(self):
		new_doc = frappe.new_doc("Stock Entry")
		new_doc.company = self.company
		new_doc.stock_entry_type = "Material Receipt"


		# fetch warehouse and cost center according the company and branch 
		war, cc = branch_map.get(self.branch, ("", ""))

		for i in self.returned_parts:
			uom = frappe.db.get_value("Item",i.part,'stock_uom')
			new_doc.append("items",{
				't_warehouse':self.warehouse or war,
				'item_code':i.part,
				'qty':i.qty,
				'uom':uom,
				'stock_uom':uom,
				'cost_center':cc,
				'job_order_data':self.job_order_data,
				'evaluation_row':i.reference,
				'conversion_factor':1,
				'basic_rate': i.price_ea,
				'allow_zero_valuation_rate': 0 if i.price_ea > 0 else 1
			})
		new_doc.returned_parts = self.name
		new_doc.save(ignore_permissions = True)
		new_doc.submit()

		frappe.msgprint("Parts Returned and Material Receipt is Created")
		self.update_qty_on_submit()
