import frappe

def create_custom_fields_hr_settings():

	hr_settings_fields = [
		
		{
			"fieldname": "last_number_in_series",
			"label": "Last Number in Series",
			"fieldtype": "Int",
			"insert_after": "retirement_age",
		},
		{
			"fieldname": "leave_settings",
			"label": "Leave Settings",
			"fieldtype": "Tab Break",
			"insert_after": "role_allowed_to_create_backdated_leave_application",
		},
		{
			"fieldname": "annual_leave_policy",
			"label": "Annual Leave Policy",
			"fieldtype": "Table",
			"options": "Annual Leave Policy",
			"insert_after": "leave_allocation",
		},
		{
			"fieldname": "leave_allocation",
			"label": "Leave Allocation",
			"fieldtype": "Table",
			"options": "Leave Allocation Table",
			"insert_after": "leave_settings",
		},
	]


	for field in hr_settings_fields:
		if not frappe.db.exists(
			"Custom Field",
			{
				"dt": "HR Settings",
				"fieldname": field["fieldname"],
			},
		):
			frappe.get_doc({
				"doctype": "Custom Field",
				"dt": "HR Settings",
				**field,
			}).insert(ignore_permissions=True)

	frappe.db.commit()



def create_custom_fields_payroll_settings():

	payroll_settings_fields = [
		{
			"fieldname": "total_working_days_company_wise",
			"label": "Company Wise Total Working Days",
			"fieldtype": "Section Break",
			"insert_after": "create_overtime_slip",
		},
		{
			"fieldname": "company_working_days",
			"fieldtype": "Table",
			"options": "Company Wise Payroll Days",
			"insert_after": "total_working_days_company_wise",
		},
	]


	for field in payroll_settings_fields:
		if not frappe.db.exists(
			"Custom Field",
			{
				"dt": "Payroll Settings",
				"fieldname": field["fieldname"],
			},
		):
			frappe.get_doc({
				"doctype": "Custom Field",
				"dt": "Payroll Settings",
				**field,
			}).insert(ignore_permissions=True)

	frappe.db.commit()