// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.query_reports["Leave Allocation"] = {
	"filters": [
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.month_start()
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.month_end()
        },
        {
            "fieldname": "company",
            "label": "Company",
            "fieldtype": "Link",
			"options":"Company",
            "reqd": 1
        }
    ],
	formatter: function (value, row, column, data, default_formatter) {
        // Use the default formatting first
        value = default_formatter(value, row, column, data);

        // Highlight rows or difference values where difference != 0
        if (data && column.fieldname === "difference") {
            if (Math.abs(data.difference) > 0.005) {
                // Red text for mismatched values
                value = `<span style="color: #e74c3c; font-weight: 600;">${value}</span>`;
            } else {
                // Green text for matching values
                value = `<span style="color: #27ae60; font-weight: 600;">${value}</span>`;
            }
        }

        return value;
    }
};