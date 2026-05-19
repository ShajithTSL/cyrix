// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.query_reports["Service Call Report"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"width": "80",
			"reqd": 1,
		}

	]
};
