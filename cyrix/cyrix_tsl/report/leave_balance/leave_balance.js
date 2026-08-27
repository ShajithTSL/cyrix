// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.query_reports["Leave Balance"] = {
	"filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "reqd": 1,
        },
        {
            "fieldname": "to_date",
            "label": __("As on Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "leave_type",
            "label": __("Leave Type"),
            "fieldtype": "Link",
            "options": "Leave Type",
            "reqd": 1
        },
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            get_query: function () {
                let company = frappe.query_report.get_filter_value("company");
                return {
                    filters: {
                        company: company
                    }
                };
            }
        },
        {
            "fieldname": "status",
            "label": __("Employee Status"),
            "fieldtype": "Select",
            "options": [
                { "label": "Active", "value": "Active" },
                { "label": "Left", "value": "Left" }
            ],
            "default": "Active",
            // "hidden": 1
        }       
    ],
    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "remaining" || column.fieldname === "projected_balance") {
            if (data && data.remaining > 0) {
                // Green for positive
                value = `<span style="color: green; font-weight: bold;">${value}</span>`;
            } else {
                // Red for zero or negative
                value = `<span style="color: red; font-weight: bold;">${value}</span>`;
            }
        }

        return value;
    }
};
