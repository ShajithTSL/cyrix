import frappe

def validate_awaiting_parts(self, method):
	if not self.get("awaiting_parts"):
		return

	for item in self.get("items"):
		# Only exclude the current doc on trash
		if method == "on_trash":
			update_awaiting_qty(item, stock_entry_name=self.name)
		else:
			update_awaiting_qty(item)

def update_awaiting_qty(item, stock_entry_name=None):
	"""
	Recalculate total awaiting quantity for the item and warehouse,
	excluding the stock entry being trashed (if provided).
	"""

	conditions = """
		se.docstatus = 0
		AND sed.item_code = %s
		AND se.stock_entry_type = 'Material Issue'
		AND sed.s_warehouse = %s
		AND se.awaiting_parts = 1
	"""
	params = [item.item_code, item.s_warehouse]

	if stock_entry_name:
		# Exclude the document being trashed
		conditions += " AND se.name != %s"
		params.append(stock_entry_name)

	query = f"""
		SELECT 
			SUM(sed.qty) AS awaiting
		FROM `tabStock Entry Detail` sed
		JOIN `tabStock Entry` se ON sed.parent = se.name
		WHERE {conditions}
	"""

	result = frappe.db.sql(query, params, as_dict=True)
	awaiting = result[0].awaiting if result and result[0].awaiting else 0

	# Update Bin document
	bin_exists = frappe.db.exists("Bin", {'item_code': item.item_code, 'warehouse': item.s_warehouse})
	if bin_exists:
		doc = frappe.get_doc("Bin", bin_exists)
		if doc.awaiting_qty != awaiting:
			doc.awaiting_qty = awaiting
			doc.save(ignore_permissions=True)
			
