// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.query_reports["Cyrix Profit and Loss"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "filter_based_on",
			label: __("Filter Based On"),
			fieldtype: "Select",
			options: ["Fiscal Year", "Date Range"],
			default: "Fiscal Year",
			reqd: 1,
			on_change: function () {
				const based_on = frappe.query_report.get_filter_value("filter_based_on");
				frappe.query_report.toggle_filter_display("from_fiscal_year", based_on === "Date Range");
				frappe.query_report.toggle_filter_display("to_fiscal_year", based_on === "Date Range");
				frappe.query_report.toggle_filter_display("period_start_date", based_on === "Fiscal Year");
				frappe.query_report.toggle_filter_display("period_end_date", based_on === "Fiscal Year");
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "from_fiscal_year",
			label: __("Start Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today()),
		},
		{
			fieldname: "to_fiscal_year",
			label: __("End Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today()),
		},
		{
			fieldname: "period_start_date",
			label: __("Start Date"),
			fieldtype: "Date",
			default: frappe.datetime.year_start(),
			hidden: 1,
		},
		{
			fieldname: "period_end_date",
			label: __("End Date"),
			fieldtype: "Date",
			default: frappe.datetime.year_end(),
			hidden: 1,
		},
		{
			fieldname: "periodicity",
			label: __("Periodicity"),
			fieldtype: "Select",
			options: ["Monthly", "Quarterly", "Half-Yearly", "Yearly", "Weekly"],
			default: "Monthly",
			reqd: 1,
		},
		{
			fieldname: "comparison_years",
			label: __("Compare With Years"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Fiscal Year", txt);
			},
		},
		{
			fieldname: "branches",
			label: __("Branches (2+ = compare)"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Branch", txt);
			},
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Cost Center", txt, {
					company: frappe.query_report.get_filter_value("company"),
				});
			},
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Department", txt, {
					company: frappe.query_report.get_filter_value("company"),
				});
			},
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "consolidate_companies",
			label: __("Consolidate With Companies"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Company", txt);
			},
		},
		{
			fieldname: "presentation_currency",
			label: __("Currency"),
			fieldtype: "Select",
			options: erpnext.get_presentation_currency_list(),
		},
		{
			fieldname: "show_growth",
			label: __("Show Growth %"),
			fieldtype: "Check",
			default: 0,
		},
		{
			fieldname: "remove_decimals",
			label: __("Remove Decimals"),
			fieldtype: "Check",
			default: 0,
		},
		{
			fieldname: "group_operating_expenses",
			label: __("Group Operating Expenses by Sub-Group"),
			fieldtype: "Check",
			default: 1,
		},
		{
			fieldname: "show_zero_values",
			label: __("Show Accounts with Zero Balance"),
			fieldtype: "Check",
			default: 0,
		},
		{
			fieldname: "debug",
			label: __("Debug (show matching info)"),
			fieldtype: "Check",
			default: 0,
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) return value;

		// Growth % columns: colored with direction arrows
		if (column.fieldname && column.fieldname.startsWith("growth_")) {
			const raw = data[column.fieldname];
			if (raw == null || raw === "") return "";
			const arrow = raw > 0 ? "▲" : raw < 0 ? "▼" : "";
			const color = raw > 0 ? "green" : raw < 0 ? "red" : "inherit";
			const weight = data.is_total || data.is_subtotal ? "700" : "400";
			return `<span style="color:${color};font-weight:${weight}">${arrow} ${Math.abs(Math.round(raw))}%</span>`;
		}

		// Section headers: bold
		if (data.is_header && column.fieldname === "account_label") {
			value = `<span style="font-weight:700">${value}</span>`;
		}

		// Empty cells (spacer/header rows) should render blank, not 0.00
		if (
			column.fieldname !== "account_label" &&
			(data[column.fieldname] === null || data[column.fieldname] === undefined)
		) {
			return "";
		}

		// Remove Decimals: show currency amounts as whole numbers
		if (
			column.fieldtype === "Currency" &&
			frappe.query_report.get_filter_value("remove_decimals") &&
			data[column.fieldname] != null
		) {
			value = format_currency(Math.round(data[column.fieldname]), data.currency, 0);
		}

		// Account rows: click-through to General Ledger
		if (data.account && column.fieldname === "account_label") {
			const enc = encodeURIComponent(data.account);
			value = `<a href="#" style="text-decoration:none" onclick="event.preventDefault(); cpl_open_gl(decodeURIComponent('${enc}'))">${value}</a>`;
		}

		// Sub-group headers (e.g. Staff Welfare Expenses): semi-bold italic
		if (data.is_subheader && column.fieldname === "account_label") {
			value = `<span style="font-weight:600;font-style:italic">${value}</span>`;
		}

		// Sub-group subtotals: semi-bold
		if (data.is_subtotal) {
			value = `<span style="font-weight:600">${value}</span>`;
		}

		// Total rows: bold
		if (data.is_total) {
			value = `<span style="font-weight:700">${value}</span>`;
		}

		// Gross / Net Profit: color each period column by its own sign
		if (
			data.bold_class === "profit" &&
			column.fieldname !== "account_label" &&
			data[column.fieldname] != null
		) {
			const color = data[column.fieldname] >= 0 ? "green" : "red";
			value = `<span style="font-weight:700;color:${color}">${value}</span>`;
		}

		return value;
	},

	onload: function (report) {
		// Ensure correct filter visibility on first load
		const based_on = report.get_filter_value("filter_based_on") || "Fiscal Year";
		report.toggle_filter_display("from_fiscal_year", based_on === "Date Range");
		report.toggle_filter_display("to_fiscal_year", based_on === "Date Range");
		report.toggle_filter_display("period_start_date", based_on === "Fiscal Year");
		report.toggle_filter_display("period_end_date", based_on === "Fiscal Year");
	},
};

// Auto-add filters for every active Accounting Dimension
// (Department/Branch are already defined above and are skipped server-side)
erpnext.utils.add_dimensions("Custom Profit and Loss", 10);

// Click-through: open General Ledger filtered to the clicked account,
// carrying over company, date range and dimension filters
window.cpl_open_gl = async function (account) {
	const f = frappe.query_report.get_filter_values();

	let from_date = f.period_start_date;
	let to_date = f.period_end_date;

	if ((f.filter_based_on || "Fiscal Year") === "Fiscal Year" && f.from_fiscal_year) {
		const start = await frappe.db.get_value(
			"Fiscal Year", f.from_fiscal_year, "year_start_date"
		);
		const end = await frappe.db.get_value(
			"Fiscal Year", f.to_fiscal_year || f.from_fiscal_year, "year_end_date"
		);
		from_date = start.message.year_start_date;
		to_date = end.message.year_end_date;
	}

	const route_options = {
		company: f.company,
		account: account,
		from_date: from_date,
		to_date: to_date,
		group_by: "Group by Voucher (Consolidated)",
	};
	if (f.project) route_options.project = f.project;
	if (f.cost_center && f.cost_center.length) route_options.cost_center = f.cost_center;
	if (f.branches && f.branches.length === 1) route_options.branch = f.branches[0];

	frappe.route_options = route_options;
	frappe.set_route("query-report", "General Ledger");
};
