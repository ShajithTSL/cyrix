// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.query_reports["Gratuity"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
		},
		{
			"fieldname": "date",
			"label": __("Date"),
			"fieldtype": "Date",
			"options": "Today",
		}	
	]
};
