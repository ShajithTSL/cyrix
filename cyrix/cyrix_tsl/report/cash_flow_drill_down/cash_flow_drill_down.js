// Cash Flow Drill — opened in a NEW TAB from the Cash Flow (Direct) report.
// Filters arrive via the URL query string (?acct_list=...&from_date=...), so this
// report never depends on frappe.route_options and can't corrupt the main report.
// acct_list / cost_centers / sign are visible but READ-ONLY (debugging aid).

frappe.query_reports["Cash Flow Drill Down"] = {
    filters: [
        { fieldname: "company", label: "Company", fieldtype: "Link", options: "Company" },
        { fieldname: "from_date", label: "From Date", fieldtype: "Date", reqd: 1 },
        { fieldname: "to_date", label: "To Date", fieldtype: "Date", reqd: 1 },
        { fieldname: "acct_list", label: "Accounts (from Cash Flow)", fieldtype: "Data", read_only: 1 },
        { fieldname: "cost_centers", label: "Cost Centers (from Cash Flow)", fieldtype: "Data", read_only: 1 },
        { fieldname: "sign", label: "Sign", fieldtype: "Float", default: 1, read_only: 1 },
    ],

    onload(report) {
        // Read filters from the URL (primary) and route_options (same-tab fallback),
        // set them all at once, then run. Nothing is written back to any global.
        const params = new URLSearchParams(window.location.search);
        const ro = frappe.route_options || {};
        const keys = ["company", "from_date", "to_date", "sign", "acct_list", "cost_centers"];

        const vals = {};
        keys.forEach((k) => {
            let v = params.get(k);
            if (v === null || v === "") v = ro[k];
            if (v !== undefined && v !== null && v !== "") vals[k] = v;
        });

        // Don't leave anything in the global that could bleed into another report.
        frappe.route_options = {};

        if (Object.keys(vals).length) {
            report.set_filter_value(vals);   // one call -> single refresh
        }
    },
};