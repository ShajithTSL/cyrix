// Cash Flow (Direct) — client script matched to tsl_cash_flow_direct.py.
// Cyrix-style filter bar + the reconciling cell drill (opens in a NEW TAB).
//
// >>> Set the key below to THIS report's exact document name. <<<
// (If your report is named "Cash Flow Cyrix", leave it; if it's "TSL Cash Flow
//  Direct", change the key to that.)  After editing: bench clear-cache, hard-refresh.

frappe.query_reports["Cash Flow Cyrix"] = {
    filters: [
        { fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company",
          default: frappe.defaults.get_user_default("Company"), reqd: 1 },

        { fieldname: "filter_based_on", label: __("Filter Based On"), fieldtype: "Select",
          options: ["Fiscal Year", "Date Range"], default: "Fiscal Year", reqd: 1,
          on_change: function () {
              const b = frappe.query_report.get_filter_value("filter_based_on");
              frappe.query_report.toggle_filter_display("from_fiscal_year", b !== "Fiscal Year");
              frappe.query_report.toggle_filter_display("to_fiscal_year", b !== "Fiscal Year");
              frappe.query_report.toggle_filter_display("period_start_date", b !== "Date Range");
              frappe.query_report.toggle_filter_display("period_end_date", b !== "Date Range");
              frappe.query_report.refresh();
          } },

        { fieldname: "from_fiscal_year", label: __("Start Year"), fieldtype: "Link",
          options: "Fiscal Year" },
        { fieldname: "to_fiscal_year", label: __("End Year"), fieldtype: "Link",
          options: "Fiscal Year" },

        { fieldname: "period_start_date", label: __("Start Date"), fieldtype: "Date",
          default: frappe.datetime.year_start(), hidden: 1 },
        { fieldname: "period_end_date", label: __("End Date"), fieldtype: "Date",
          default: frappe.datetime.year_end(), hidden: 1 },

        { fieldname: "periodicity", label: __("Periodicity"), fieldtype: "Select",
          options: ["Monthly", "Quarterly", "Half-Yearly", "Yearly", "Weekly"], default: "Yearly", reqd: 1 },

        { fieldname: "comparison_years", label: __("Compare With Years"), fieldtype: "MultiSelectList",
          get_data: (txt) => frappe.db.get_link_options("Fiscal Year", txt) },

        { fieldname: "cost_center", label: __("Cost Center"), fieldtype: "MultiSelectList",
          get_data: (txt) => frappe.db.get_link_options("Cost Center", txt, {
              company: frappe.query_report.get_filter_value("company") }) },

        { fieldname: "consolidate_companies", label: __("Consolidate With Companies"),
          fieldtype: "MultiSelectList",
          get_data: (txt) => frappe.db.get_link_options("Company", txt) },

        { fieldname: "presentation_currency", label: __("Currency"), fieldtype: "Select",
          options: erpnext.get_presentation_currency_list() },

        { fieldname: "show_growth", label: __("Show Growth %"), fieldtype: "Check", default: 0 },
        { fieldname: "remove_decimals", label: __("Remove Decimals"), fieldtype: "Check", default: 0 },
    ],

    formatter(value, row, column, data, default_formatter) {
        if (column.fieldtype === "Float" && typeof value === "number") {
            const isGrowth = /_growth$/.test(column.fieldname);
            const prec = isGrowth ? 1
                : (frappe.query_report.get_filter_value("remove_decimals") ? 0 : 2);
            let text = format_number(value, null, prec) + (isGrowth ? " %" : "");

            // figure cells with accounts behind them -> reconciling drill
            if (!isGrowth && data && data.gl_accounts && data.gl_accounts.length && value !== 0) {
                const payload = {
                    accounts: data.gl_accounts,
                    company: column.gl_company || "",
                    from_date: column.gl_from_date,
                    to_date: column.gl_to_date,
                    sign: data._sign || 1,
                };
                const token = encodeURIComponent(JSON.stringify(payload));
                return `<a class="tsl-drill" data-p="${token}"
                           style="cursor:pointer; text-decoration:underline;">${text}</a>`;
            }
            return text;
        }
        return default_formatter(value, row, column, data);
    },

    after_datatable_render() {
        $(document).off("click.tsldrill").on("click.tsldrill", "a.tsl-drill", function (e) {
            e.preventDefault();
            let p;
            try { p = JSON.parse(decodeURIComponent(this.getAttribute("data-p"))); }
            catch (err) { console.error("Cash Flow drill:", err); return; }

            const params = new URLSearchParams();
            params.set("acct_list", JSON.stringify(p.accounts));
            params.set("from_date", p.from_date);
            params.set("to_date", p.to_date);
            params.set("sign", p.sign);
            if (p.company) params.set("company", p.company);
            const cc = frappe.query_report.get_filter_value("cost_center");
            if (cc && cc.length) params.set("cost_centers", JSON.stringify(cc));

            const url = "/app/query-report/" + encodeURIComponent("Cash Flow Drill Down")
                + "?" + params.toString();
            window.open(url, "_blank");
        });
    },

    onload(report) {
        const b = report.get_filter_value("filter_based_on") || "Fiscal Year";
        report.toggle_filter_display("from_fiscal_year", b !== "Fiscal Year");
        report.toggle_filter_display("to_fiscal_year", b !== "Fiscal Year");
        report.toggle_filter_display("period_start_date", b !== "Date Range");
        report.toggle_filter_display("period_end_date", b !== "Date Range");

        // Default Start/End Year to the fiscal year covering today — done with a plain
        // DB lookup (avoids erpnext.utils.get_fiscal_year, which throws on some builds).
        if (!report.get_filter_value("from_fiscal_year")) {
            const today = frappe.datetime.get_today();
            frappe.db.get_value("Fiscal Year", {
                year_start_date: ["<=", today],
                year_end_date: [">=", today],
            }, "name").then((r) => {
                const fy = r && r.message && r.message.name;
                if (fy) {
                    report.set_filter_value("from_fiscal_year", fy);
                    if (!report.get_filter_value("to_fiscal_year")) {
                        report.set_filter_value("to_fiscal_year", fy);
                    }
                }
            });
        }
    },
};