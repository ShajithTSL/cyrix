// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Checkin"] = {
	filters: [
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_start()
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_end()
        },
        {
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company"
        },
        {
            fieldname: "branch",
            label: "Branch",
            fieldtype: "Link",
            options: "Branch"
        },
        {
            fieldname: "employee",
            label: "Employee",
            fieldtype: "Link",
            options: "Employee"
        },
        // {
        //     fieldname: "cyrix_employee",
        //     label: __("Cyrix Employee"),
        //     fieldtype: "Select",
        //     options: "\nYes\nNo",
        //     default: ""
        // },
    ],
      onload(report) {
        report.page.add_inner_button(__("Download PDF"), function () {
			const filters = report.get_values();

			window.open(
				"/api/method/cyrix.cyrix_tsl.report.employee_checkin.employee_checkin.download_pdf?" +
				$.param(filters)
			);
		});
    },
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (data && (data.employee_name === "TOTAL" || data.employee_name === "GRAND TOTAL")) {
			column.css = {
				"background-color": "#ff0000",
				"color": "#ffffff",
				"font-weight": "bold"
			};
		}

		return value;
	}
};
