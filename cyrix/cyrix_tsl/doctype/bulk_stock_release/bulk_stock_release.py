# Copyright (c) 2026, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from collections import defaultdict


class BulkStockRelease(Document):
	@frappe.whitelist()
	def submit_bulk_entries(self):
		# Track processed Stock Entries to avoid duplicate submissions
		processed_entries = set()

		for entry in self.stock_details:
			if not entry.se_reference or not entry.child_name:
				continue

			# Fetch the Stock Entry document
			stock_entry = frappe.get_doc("Stock Entry", entry.se_reference)

			# 1. Update Stock Entry's posting date
			stock_entry.set_posting_time = 1
			if self.posting_date:
				stock_entry.posting_date = self.posting_date

			# 2. Find and update the child row inside Stock Entry
			target_child = None
			for item in stock_entry.items:
				if item.name == entry.child_name:
					target_child = item
					break

			if target_child:
				target_child.expense_account = self.account  # Make sure 'account' field exists on Stock Entry Detail
				target_child.branch = self.branch
			else:
				frappe.throw(f"Child row {entry.child_name} not found in Stock Entry {entry.se_reference}")

			# Save but don't submit yet
			stock_entry.save()

			# Mark for submission
			processed_entries.add(stock_entry.name)

		# 3. Submit all updated Stock Entries
		for se_name in processed_entries:
			se_doc = frappe.get_doc("Stock Entry", se_name)
			if se_doc.docstatus == 0:
				se_doc.submit()

		frappe.msgprint("All Stock Entries updated and submitted successfully.")

	

@frappe.whitelist()
def fetch_draft_entries(from_date,to_date,warehouse,cost_center,branch):
	if from_date and to_date and warehouse and cost_center:
		query = """
			SELECT
				se.posting_date, 
				sed.item_code,
				sed.name as child_name, 
				sed.parent as se_reference, 
				sed.qty,
				sed.cost_center, 
				sed.description, 
				sed.basic_rate as rate, 
				sed.basic_amount as amount,
				sed.job_order_data as job_order_data,
				i.model_num as model
			FROM `tabStock Entry Detail` sed
			JOIN `tabStock Entry` se ON sed.parent = se.name
			JOIN `tabItem` i ON sed.item_code = i.name
			WHERE se.docstatus = 0
				AND se.posting_date BETWEEN %s AND %s
				AND sed.s_warehouse = %s
				AND sed.cost_center = %s
				AND se.stock_entry_type = 'Material Issue'
				AND sed.job_order_data IS NOT NULL
			ORDER BY se.posting_date ASC
		"""

		se_list = frappe.db.sql(query, (from_date, to_date, warehouse,cost_center), as_dict=1)
		for row in se_list:
			row["branch"] = branch
		return se_list