frappe.ui.form.on('Salary Slip', {
	refresh(frm) {
        frm.add_custom_button(__('Pay Slip'), function () {
            var f_name = frm.doc.name
            var print_format = "Salary Slip";
            window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
                + "doctype=" + encodeURIComponent(frm.doc.doctype)
                + "&name=" + encodeURIComponent(f_name)
                + "&trigger_print=1"
                + "&format=" + print_format
                + "&no_letterhead=0"
            ));
        })
    }
})