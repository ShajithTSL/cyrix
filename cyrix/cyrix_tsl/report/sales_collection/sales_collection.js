// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Collection"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
			width: "100px",
		},
		{
			fieldname: "to_date",
			label: __("To"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
			width: "100px",
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			width: "100px",
			reqd: 1,
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
			width: "100px",
			get_query: function (doc) {
				return {
					filters: {
						company: frappe.query_report.get_filter_value("company")
					}
				};
			}
		},
		{
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person",
			width: "100px",
			// reqd: 1,
		},
		{
		fieldname: "type",
		label: __("Type"),
		fieldtype: "Select",
		options: "\nRepair\nSupply",
		width: "100px",
	}

	]
};
