// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Probation"] = {
	filters: [
		{
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company"
        },	
	],
};
