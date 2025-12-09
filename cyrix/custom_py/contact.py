from gettext import find
import frappe
from frappe.utils import datetime,now,today

def before_save(self, method):
	# Get all customers linked to this Contact
	customers = [l.link_name for l in self.links if l.link_doctype == "Customer"]

	for customer in customers:
		create_or_update_contact_details(self, customer)


def create_or_update_contact_details(contact, customer):
	"""Create or update Contact Details child doc under Customer"""

	# Check if child already exists
	existing_child_name = frappe.db.exists(
		"Contact Details",
		{
			"parent": customer,
			"parenttype": "Customer",
			"parentfield": "contact_details",
			"name1": contact.name
		}
	)

	if existing_child_name:
		# 🔄 Update existing child doc
		child = frappe.get_doc("Contact Details", existing_child_name)

	else:
		# ➕ Create new child doc
		child = frappe.new_doc("Contact Details")
		child.parent = customer
		child.parenttype = "Customer"
		child.parentfield = "contact_details"

	# Set / update fields
	child.name1 = contact.name
	child.designation = contact.designation
	child.phone_number = contact.mobile_no or contact.phone
	child.email_id = contact.email_id
	child.location = contact.location
	
	# Save child doc
	child.save(ignore_permissions=True)
