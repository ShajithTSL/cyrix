# Copyright (c) 2025, tsl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TechnicianID(Document):
	pass


@frappe.whitelist()
def get_last_technician_id():
	last_technician_id = frappe.db.get_value("Technician ID", {}, "name", order_by="name desc")
	if last_technician_id:
		return int(last_technician_id) + 1
	else:
		return 1