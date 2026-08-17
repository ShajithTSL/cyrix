// Copyright (c) 2026, tsl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Termination Form", {
    hods_relieving_date: function(frm){
		if (frm.doc.hods_relieving_date && frm.doc.employee){
			frappe.call({
				method: "cyrix.cyrix_tsl.doctype.resignation_form.resignation_form.calculate_relieving_date",
				args: {
					posting_date : frm.doc.hods_relieving_date,
					employee: frm.doc.employee
				},
				callback(r){
					if(r.message){
						frm.set_value("actual_relieving_date",r.message)
					}
				}
			})
		}
	}
});
