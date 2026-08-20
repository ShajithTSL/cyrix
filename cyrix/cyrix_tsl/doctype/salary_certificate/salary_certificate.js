// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Salary Certificate', {
	refresh(frm) {
        frm.add_custom_button(__('Salary Certificate'), function () {
            var f_name = frm.doc.name
            var print_format = "Salary Certificate";
            window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
                + "doctype=" + encodeURIComponent(frm.doc.doctype)
                + "&name=" + encodeURIComponent(f_name)
                + "&trigger_print=1"
                + "&format=" + print_format
                + "&no_letterhead=0"
            ));
        },__('Print'))
	}
})