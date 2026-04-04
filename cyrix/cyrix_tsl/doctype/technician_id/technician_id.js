// Copyright (c) 2025, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Technician ID", {
	onload(frm) {
        if (frm.doc.__islocal) {
            frappe.call({
                method: "cyrix.cyrix_tsl.doctype.technician_id.technician_id.get_last_technician_id",
                callback: function(r) {
                    if (r.message) {
                        frm.set_value("id", r.message);
                    }
                }
            });
        }
	},
});
